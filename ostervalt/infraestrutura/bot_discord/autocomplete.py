# -*- coding: utf-8 -*-
import discord
import os
import polars as pl
from discord import app_commands
from typing import List

# TODO: Importar corretamente a função de persistência
# from ostervalt.infraestrutura.persistencia.armazenamento_servidor import load_server_data

# Placeholder para load_server_data
def load_server_data(server_id):
    print(f"[Placeholder Autocomplete] Carregando dados para server_id: {server_id}")
    # Simula a estrutura básica esperada
    return {
            "characters": {},
            "stock_items": {},
            "prices": {}
        }

# --- Funções de Lógica de Autocomplete ---

async def autocomplete_item_by_rarity(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete para itens com base na raridade especificada no comando."""
    server_id = str(interaction.guild_id)
    # A raridade é acessada via namespace do comando que está usando este autocomplete
    rarity = getattr(interaction.namespace, 'raridade', None)
    if not rarity:
        return [] # Retorna vazio se a raridade não foi especificada ainda

    items = []
    # TODO: Usar repositório de itens em vez de CSV direto
    csv_file = f"items_{server_id}.csv" if os.path.exists(f"items_{server_id}.csv") else "items.csv"
    try:
        # Tentar ler o CSV com tratamento de erro para coluna ausente
        try:
            all_items = pl.read_csv(csv_file, infer_schema_length=10000, null_values=["undefined"])
        except pl.ColumnNotFoundError:
             print(f"Erro: Coluna 'Rarity' ou 'Name' não encontrada no arquivo CSV '{csv_file}'.")
             return [] # Retorna vazio se colunas essenciais faltam

        # Filtrar pela raridade e pelo texto atual (case-insensitive)
        # Usar str.contains com case=False para case-insensitive
        available_items = all_items.filter(
            (pl.col("Rarity").str.to_lowercase() == rarity.lower()) &
            (pl.col("Name").str.contains(f"(?i){current}")) # Regex para case-insensitive
        )
        item_names = available_items['Name'].to_list()
        items = sorted(list(set(item_names))) # Remover duplicatas e ordenar

    except FileNotFoundError:
        print(f"Arquivo CSV '{csv_file}' não encontrado para autocomplete.")
        items = []
    except Exception as e:
         print(f"Erro ao ler/filtrar CSV para autocomplete por raridade: {e}")
         items = []

    return [
        app_commands.Choice(name=item, value=item)
        for item in items
    ][:25]

async def autocomplete_item_in_stock(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete para itens presentes no estoque."""
    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)
    items = []
    # Iterar sobre os itens no estoque (stock_items)
    for rarity_data in server_data.get("stock_items", {}).values():
        names = rarity_data.get("Name", [])
        quantities = rarity_data.get("Quantity", [])
        min_len = min(len(names), len(quantities))
        for i in range(min_len):
            name = names[i]
            quantity = quantities[i]
            # Adicionar apenas se houver estoque e corresponder ao texto atual
            if quantity > 0 and current.lower() in name.lower():
                items.append(name)

    # Remover duplicatas e ordenar
    items = sorted(list(set(items)))
    return [
        app_commands.Choice(name=item, value=item)
        for item in items
    ][:25]

async def autocomplete_character(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete para nomes de personagens do usuário que está interagindo."""
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)
    user_characters = server_data.get("characters", {}).get(user_id, {})
    # Ordenar os nomes dos personagens
    character_names = sorted([name for name in user_characters if current.lower() in name.lower()])
    return [
        app_commands.Choice(name=char_name, value=char_name)
        for char_name in character_names
    ][:25]

async def autocomplete_item(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete para itens disponíveis na loja (em estoque), mostrando o preço."""
    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)
    items_with_price = []
    # Iterar sobre os itens no estoque (stock_items)
    for rarity_data in server_data.get("stock_items", {}).values():
        names = rarity_data.get("Name", [])
        values = rarity_data.get("Value", [])
        quantities = rarity_data.get("Quantity", [])
        min_len = min(len(names), len(values), len(quantities))
        for i in range(min_len):
            name = names[i]
            value = values[i]
            quantity = quantities[i]
            # Adicionar apenas se houver estoque e corresponder ao texto atual
            if quantity > 0 and current.lower() in name.lower():
                # Adiciona tupla (nome, preço) para ordenação posterior
                items_with_price.append((name, value))

    # Remover duplicatas (baseado no nome do item) e ordenar por nome
    unique_items = sorted(list(set(items_with_price)), key=lambda x: x[0])

    return [
        app_commands.Choice(name=f"{item} - {price} moedas", value=item)
        for item, price in unique_items
    ][:25]

async def autocomplete_character_for_user(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete para personagens de um usuário específico (usado em comandos como /rip)."""
    server_id = str(interaction.guild_id)
    # Obtém o usuário do parâmetro 'user' do comando
    user_option = getattr(interaction.namespace, 'user', None)
    # Verifica se o usuário foi fornecido e é um Member válido
    if not isinstance(user_option, discord.Member):
        return []

    target_user_id = str(user_option.id)
    server_data = load_server_data(server_id)
    user_characters = server_data.get("characters", {}).get(target_user_id, {})
    # Ordenar os nomes dos personagens
    character_names = sorted([name for name in user_characters if current.lower() in name.lower()])
    return [
        app_commands.Choice(name=char_name, value=char_name)
        for char_name in character_names
    ][:25]