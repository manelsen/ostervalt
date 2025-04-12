import os
import discord
import json
import math
import polars as pl
import asyncio
import datetime
import random
import yaml
from discord import app_commands, Member, Role
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

def load_config():
    """
    Carrega as configurações do arquivo config.yaml.

    Returns:
        dict: Dicionário com as configurações carregadas.
    """
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

config = load_config()

class RPGBot(commands.Bot):
    """
    Classe principal do bot RPG, herda de commands.Bot.

    Responsável por inicializar o bot, sincronizar comandos e tratar eventos.
    """
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        """
        Método chamado quando o bot está pronto para sincronizar os comandos.
        """
        await self.tree.sync()
        print("Comandos sincronizados automaticamente.")

    async def on_ready(self):
        """
        Evento chamado quando o bot está pronto e conectado ao Discord.
        """
        print(f'{self.user} está online e pronto para a aventura!')

bot = RPGBot()

# Funções auxiliares

def load_server_data(server_id):
    """
    Carrega os dados do servidor a partir de um arquivo JSON.

    Args:
        server_id (str): ID do servidor Discord.

    Returns:
        dict: Dicionário com os dados do servidor.
    """
    try:
        with open(f'server_data_{server_id}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "characters": {},
            "stock_items": {},
            "shop_items": None,
            "special_roles": config.get("cargos_especiais", {"saldo": [], "marcos": []}),
            "messages": config.get("messages", {}),
            "tiers": config.get("tiers", {}),
            "aposentados": {},
            "prices": {},
            "probabilidade_crime": config.get("probabilidades", {}).get("crime", 50)
        }

def save_server_data(server_id, data):
    """
    Salva os dados do servidor em um arquivo JSON.

    Args:
        server_id (str): ID do servidor Discord.
        data (dict): Dados a serem salvos.
    """
    with open(f'server_data_{server_id}.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Dados do servidor {server_id} salvos com sucesso.")

def update_item_price(server_id, item_name, value):
    """
    Atualiza o preço de um item nos dados do servidor.

    Args:
        server_id (str): ID do servidor Discord.
        item_name (str): Nome do item.
        value (str): Valor do item.
    """
    server_data = load_server_data(server_id)
    if "prices" not in server_data:
        server_data["prices"] = {}
    server_data["prices"][item_name] = value
    save_server_data(server_id, server_data)
    print(f"Preço atualizado para {item_name}: {value} moedas")

def calculate_level(marcos):
    """
    Calcula o nível do personagem com base nos marcos.

    Args:
        marcos (float): Quantidade de marcos.

    Returns:
        int: Nível calculado.
    """
    level = min(20, math.floor(marcos) + 1)
    return level

def marcos_to_gain(level):
    """
    Determina quantos marcos um personagem ganha ao usar o comando /up.

    Args:
        level (int): Nível atual do personagem.

    Returns:
        int: Quantidade de marcos a ganhar.
    """
    marcos_por_nivel = config.get("progressao", {}).get("marcos_por_nivel", {})
    if level <= 4:
        return marcos_por_nivel.get("1-4", 16)
    elif level <= 12:
        return marcos_por_nivel.get("5-12", 4)
    elif level <= 16:
        return marcos_por_nivel.get("13-16", 2)
    else:
        return marcos_por_nivel.get("17-20", 1)

def format_marcos(marcos_parts):
    """
    Formata a representação dos marcos para exibição.

    Args:
        marcos_parts (int): Partes de marcos.

    Returns:
        str: String formatada com a representação dos marcos.
    """
    full_marcos = marcos_parts // 16
    remaining_parts = marcos_parts % 16

    if remaining_parts == 0:
        return f"{full_marcos} Marcos"

    level = calculate_level(marcos_parts / 16)

    if level <= 4:
        return f"{full_marcos} Marcos"
    elif level <= 12:
        return f"{full_marcos} e {remaining_parts // 4}/4 Marcos"
    elif level <= 16:
        return f"{full_marcos} e {remaining_parts // 2}/8 Marcos"
    else:
        return f"{full_marcos} e {remaining_parts}/16 Marcos"

def check_permissions(member: Member, character: str, permission_type: str, server_data, allow_owner=True):
    """
    Verifica se o usuário tem permissão para executar determinada ação.

    Args:
        member (Member): Membro do Discord.
        character (str): Nome do personagem.
        permission_type (str): Tipo de permissão ('saldo', 'marcos', 'view').
        server_data (dict): Dados do servidor.
        allow_owner (bool): Se True, permite que o dono do personagem execute a ação.

    Returns:
        bool: True se o usuário tem permissão, False caso contrário.
    """
    user_id = str(member.id)
    is_owner = character in server_data["characters"].get(user_id, {})
    is_admin = member.guild_permissions.administrator
    has_special_role = any(role.id in server_data["special_roles"].get(permission_type, []) for role in member.roles)
    if allow_owner:
        return is_owner or is_admin or has_special_role
    else:
        return is_admin or has_special_role


def get_tier(nivel, server_data):
    """
    Obtém o nome do tier com base no nível do personagem.

    Args:
        nivel (int): Nível do personagem.
        server_data (dict): Dados do servidor.

    Returns:
        str: Nome do tier ou None se não encontrado.
    """
    for tier_name, tier_data in server_data.get("tiers", {}).items():
        if tier_data["nivel_min"] <= nivel <= tier_data["nivel_max"]:
            return tier_name
    return None

# Comandos de prefixo

@bot.command()
@commands.is_owner()
async def sync_commands(ctx):
    """
    Sincroniza os comandos de slash com o Discord.

    Args:
        ctx (Context): Contexto do comando.
    """
    guild = ctx.guild
    bot.tree.clear_commands(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    await ctx.send(f"Sincronizados {len(synced)} comandos para este servidor.")

@bot.command()
@commands.is_owner()
async def list_commands(ctx):
    """
    Lista todos os comandos disponíveis no servidor.

    Args:
        ctx (Context): Contexto do comando.
    """
    guild_commands = await bot.tree.fetch_commands(guild=ctx.guild)
    await ctx.send(f"Comandos do servidor: {', '.join(cmd.name for cmd in guild_commands)}")

# Comandos de aplicação (slash commands)

@bot.tree.command(name="cargos", description="Define cargos com permissões especiais")
@app_commands.describe(
    tipo="Tipo de permissão (saldo ou marcos)",
    acao="Adicionar ou remover cargo",
    cargo="Cargo a ser adicionado ou removido"
)
@app_commands.choices(
    tipo=[
        app_commands.Choice(name="Saldo", value="saldo"),
        app_commands.Choice(name="Marcos", value="marcos")
    ],
    acao=[
        app_commands.Choice(name="Adicionar", value="add"),
        app_commands.Choice(name="Remover", value="remove")
    ]
)
async def cargos(interaction: discord.Interaction, tipo: str, acao: str, cargo: Role):
    """
    Gerencia os cargos com permissões especiais.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        tipo (str): Tipo de permissão ('saldo' ou 'marcos').
        acao (str): Ação a ser executada ('add' ou 'remove').
        cargo (Role): Cargo a ser adicionado ou removido.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    if acao == "add":
        if cargo.id not in server_data["special_roles"][tipo]:
            server_data["special_roles"][tipo].append(cargo.id)
            await interaction.response.send_message(f"Cargo {cargo.name} adicionado às permissões de {tipo}.")
        else:
            await interaction.response.send_message(f"Cargo {cargo.name} já está nas permissões de {tipo}.")
    elif acao == "remove":
        if cargo.id in server_data["special_roles"][tipo]:
            server_data["special_roles"][tipo].remove(cargo.id)
            await interaction.response.send_message(f"Cargo {cargo.name} removido das permissões de {tipo}.")
        else:
            await interaction.response.send_message(f"Cargo {cargo.name} não estava nas permissões de {tipo}.")

    save_server_data(server_id, server_data)

@bot.tree.command(name="criar", description="Cria um novo personagem nível 0 vinculado à sua conta Discord")
@app_commands.describe(nome="Nome do novo personagem")
async def criar(interaction: discord.Interaction, nome: str):
    """
    Cria um novo personagem para o usuário.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        nome (str): Nome do novo personagem.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    limite_personagens = config.get("limites", {}).get("personagens_por_usuario", 2)
    user_characters = server_data["characters"].get(user_id, {})

    if len(user_characters) >= limite_personagens:
        await interaction.response.send_message(f"Você já possui {limite_personagens} personagens. Não é possível criar mais.", ephemeral=True)
        return

    if nome in user_characters:
        await interaction.response.send_message(f"Você já tem um personagem com o nome {nome}. Por favor, escolha outro nome.", ephemeral=True)
        return

    new_character = {
        "marcos": 0,
        "inventory": [],
        "dinheiro": 0,
        "nivel": 1,
        "last_work_time": None,
        "last_crime_time": None
    }

    user_characters[nome] = new_character
    server_data["characters"][user_id] = user_characters

    save_server_data(server_id, server_data)

    await interaction.response.send_message(f"Personagem {nome} criado com sucesso e vinculado à sua conta Discord!")

@bot.tree.command(name="estoque", description="Gera um novo estoque para a loja")
@app_commands.describe(
    common="Número de itens comuns",
    uncommon="Número de itens incomuns",
    rare="Número de itens raros",
    very_rare="Número de itens muito raros"
)
async def estoque(interaction: discord.Interaction, common: int, uncommon: int, rare: int, very_rare: int):
    """
    Gera um novo estoque de itens para a loja.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        common (int): Quantidade de itens comuns.
        uncommon (int): Quantidade de itens incomuns.
        rare (int): Quantidade de itens raros.
        very_rare (int): Quantidade de itens muito raros.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)
    server_data["stock_items"] = {}

    rarities = {
        'common': common,
        'uncommon': uncommon,
        'rare': rare,
        'very rare': very_rare
    }

    csv_file = f"items_{server_id}.csv" if os.path.exists(f"items_{server_id}.csv") else "items.csv"

    try:
        all_items = pl.read_csv(csv_file, infer_schema_length=10000, null_values=["undefined"])
    except FileNotFoundError:
        await interaction.response.send_message(f"Erro: O arquivo de itens '{csv_file}' não foi encontrado.", ephemeral=True)
        return

    await interaction.response.send_message("Criando novo estoque. Por favor, defina os preços para cada item.")

    for rarity, count in rarities.items():
        available_items = all_items.filter(pl.col("Rarity") == rarity)
        available_count = len(available_items)

        if available_count < count:
            count = available_count

        if count > 0:
            items = available_items.sample(count, with_replacement=False)
            server_data["stock_items"][rarity] = {
                'Name': items['Name'].to_list(),
                'Value': [],
                'Quantity': [1] * count,
                'Text': items['Text'].to_list()
            }

            await interaction.followup.send(f"Definindo preços para itens {rarity}:")
            for name in server_data["stock_items"][rarity]['Name']:
                price_set = False
                attempts = 0
                while not price_set and attempts < 3:
                    await interaction.followup.send(f"Digite o preço para {name} (em moedas):")
                    try:
                        price_message = await bot.wait_for('message', check=lambda m: m.author == interaction.user and m.channel == interaction.channel, timeout=60.0)
                        try:
                            price = int(price_message.content)
                            server_data["stock_items"][rarity]['Value'].append(str(price))
                            update_item_price(server_id, name, str(price))
                            await interaction.followup.send(f"Preço de {name} definido como {price} moedas e salvo.")
                            price_set = True
                        except ValueError:
                            await interaction.followup.send("Por favor, digite um número inteiro válido.")
                            attempts += 1
                    except asyncio.TimeoutError:
                        await interaction.followup.send(f"Tempo esgotado para {name}. Tentativa {attempts + 1} de 3.")
                        attempts += 1

                if not price_set:
                    preco_padrao = config.get("precos_padroes", {}).get("item_padrao", 100)
                    await interaction.followup.send(f"Falha ao definir preço para {name}. Definindo preço padrão de {preco_padrao} moedas.")
                    server_data["stock_items"][rarity]['Value'].append(str(preco_padrao))
                    update_item_price(server_id, name, str(preco_padrao))

    save_server_data(server_id, server_data)

    summary = "Novo estoque criado com:\n"
    for rarity, items in server_data["stock_items"].items():
        summary += f"- {len(items['Name'])} itens {rarity}\n"

    await interaction.followup.send(summary)
    await interaction.followup.send("Estoque atualizado com sucesso e valores salvos!")

@bot.tree.command(name="inserir", description="Insere um item no estoque da loja")
@app_commands.describe(
    raridade="Raridade do item",
    item="Nome do item a ser inserido",
    quantidade="Quantidade do item",
    valor="Valor do item (opcional)"
)
@app_commands.choices(
    raridade=[
        app_commands.Choice(name="Comum", value="common"),
        app_commands.Choice(name="Incomum", value="uncommon"),
        app_commands.Choice(name="Raro", value="rare"),
        app_commands.Choice(name="Muito Raro", value="very rare")
    ]
)
async def inserir(interaction: discord.Interaction, raridade: str, item: str, quantidade: int, valor: int = None):
    """
    Insere um item no estoque da loja.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        raridade (str): Raridade do item.
        item (str): Nome do item.
        quantidade (int): Quantidade a ser inserida.
        valor (int, optional): Valor do item. Defaults to None.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    if "stock_items" not in server_data or not server_data["stock_items"]:
        server_data["stock_items"] = {}

    if raridade not in server_data["stock_items"]:
        server_data["stock_items"][raridade] = {
            'Name': [],
            'Value': [],
            'Quantity': [],
            'Text': []
        }

    stock = server_data["stock_items"][raridade]

    if item in stock['Name']:
        index = stock['Name'].index(item)
        stock['Quantity'][index] += quantidade
        if valor is not None:
            stock['Value'][index] = str(valor)
            update_item_price(server_id, item, str(valor))
    else:
        stock['Name'].append(item)
        stock['Quantity'].append(quantidade)
        if valor is not None:
            stock['Value'].append(str(valor))
            update_item_price(server_id, item, str(valor))
        else:
            price = server_data.get("prices", {}).get(item, str(config.get("precos_padroes", {}).get("item_padrao", 100)))
            stock['Value'].append(price)
        stock['Text'].append("Descrição não disponível")

    save_server_data(server_id, server_data)
    await interaction.response.send_message(f"Item '{item}' inserido no estoque com sucesso.")

# Autocomplete para itens de determinada raridade
async def autocomplete_item_by_rarity(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """
    Autocomplete para itens com base na raridade especificada.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        current (str): Entrada atual do usuário.

    Returns:
        list[app_commands.Choice[str]]: Lista de escolhas para autocomplete.
    """
    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)
    rarity = interaction.namespace.raridade  # Obtém a raridade escolhida
    items = []

    # Carrega os itens do arquivo CSV
    csv_file = f"items_{server_id}.csv" if os.path.exists(f"items_{server_id}.csv") else "items.csv"
    try:
        all_items = pl.read_csv(csv_file, infer_schema_length=10000, null_values=["undefined"])
        available_items = all_items.filter(pl.col("Rarity") == rarity)
        item_names = available_items['Name'].to_list()
        items = [item for item in item_names if current.lower() in item.lower()]
    except FileNotFoundError:
        items = []

    return [
        app_commands.Choice(name=item, value=item)
        for item in items
    ][:25]

@inserir.autocomplete('item')
async def inserir_item_autocomplete(interaction: discord.Interaction, current: str):
    """
    Função de autocomplete para o parâmetro 'item' do comando '/inserir'.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        current (str): Entrada atual do usuário.
    """
    return await autocomplete_item_by_rarity(interaction, current)

@bot.tree.command(name="remover", description="Remove um item do estoque da loja")
@app_commands.describe(
    item="Nome do item a ser removido",
    quantidade="Quantidade a ser removida (padrão: todos)"
)
async def remover(interaction: discord.Interaction, item: str, quantidade: int = None):
    """
    Remove um item do estoque da loja.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        item (str): Nome do item.
        quantidade (int, optional): Quantidade a ser removida. Defaults to None.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    item_found = False
    for rarity, stock in server_data.get("stock_items", {}).items():
        if item in stock['Name']:
            index = stock['Name'].index(item)
            if quantidade is None or quantidade >= stock['Quantity'][index]:
                stock['Name'].pop(index)
                stock['Value'].pop(index)
                stock['Quantity'].pop(index)
                stock['Text'].pop(index)
                await interaction.response.send_message(f"Item '{item}' removido completamente do estoque.")
            else:
                stock['Quantity'][index] -= quantidade
                await interaction.response.send_message(f"Removido {quantidade} de '{item}'. Quantidade restante: {stock['Quantity'][index]}")
            item_found = True
            break

    if not item_found:
        await interaction.response.send_message(f"Item '{item}' não encontrado no estoque.")

    save_server_data(server_id, server_data)

# Autocomplete para itens presentes no estoque
async def autocomplete_item_in_stock(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """
    Autocomplete para itens presentes no estoque.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        current (str): Entrada atual do usuário.

    Returns:
        list[app_commands.Choice[str]]: Lista de escolhas para autocomplete.
    """
    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)
    items = []
    for rarity_items in server_data.get("stock_items", {}).values():
        for name in rarity_items.get("Name", []):
            if current.lower() in name.lower():
                items.append(name)
    return [
        app_commands.Choice(name=item, value=item)
        for item in items
    ][:25]

@remover.autocomplete('item')
async def remover_item_autocomplete(interaction: discord.Interaction, current: str):
    """
    Função de autocomplete para o parâmetro 'item' do comando '/remover'.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        current (str): Entrada atual do usuário.
    """
    return await autocomplete_item_in_stock(interaction, current)

@bot.tree.command(name="loja", description="Mostra os itens disponíveis na loja")
async def loja(interaction: discord.Interaction):
    """
    Mostra os itens disponíveis na loja.

    Args:
        interaction (discord.Interaction): Interação do usuário.
    """
    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    if not server_data.get("stock_items"):
        await interaction.response.send_message("A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
        return

    shop_list = "Itens disponíveis na loja:\n\n"
    for rarity, items in server_data["stock_items"].items():
        shop_list += f"**{rarity.capitalize()}:**\n"
        for name, value, quantity in zip(items['Name'], items['Value'], items['Quantity']):
            if quantity > 0:
                text = items.get('Text', [''])[items['Name'].index(name)]
                shop_list += f"- {name} (Valor: {value}, Quantidade: {quantity})\n  Descrição: {text}\n\n"

    if len(shop_list) > 2000:
        parts = [shop_list[i:i+1900] for i in range(0, len(shop_list), 1900)]
        await interaction.response.send_message(parts[0])
        for part in parts[1:]:
            await interaction.followup.send(part)
    else:
        await interaction.response.send_message(shop_list)

# Funções de autocomplete

async def autocomplete_character(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """
    Autocomplete para nomes de personagens do usuário.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        current (str): Entrada atual do usuário.

    Returns:
        list[app_commands.Choice[str]]: Lista de escolhas para autocomplete.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)
    user_characters = server_data["characters"].get(user_id, {})
    return [
        app_commands.Choice(name=char_name, value=char_name)
        for char_name in user_characters if current.lower() in char_name.lower()
    ][:25]

async def autocomplete_item(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """
    Autocomplete para itens disponíveis na loja.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        current (str): Entrada atual do usuário.

    Returns:
        list[app_commands.Choice[str]]: Lista de escolhas para autocomplete.
    """
    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)
    items = []
    for rarity_items in server_data.get("stock_items", {}).values():
        for name, value, quantity in zip(rarity_items.get("Name", []), rarity_items.get("Value", []), rarity_items.get("Quantity", [])):
            if quantity > 0 and current.lower() in name.lower():
                items.append((name, value))
    return [
        app_commands.Choice(name=f"{item} - {price} moedas", value=item)
        for item, price in items
    ][:25]

@bot.tree.command(name="up", description="Adiciona Marcos a um personagem ou sobe de nível")
@app_commands.describe(character="Nome do personagem")
@app_commands.autocomplete(character=autocomplete_character)
async def up(interaction: discord.Interaction, character: str):
    """
    Adiciona marcos a um personagem ou sobe de nível.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    if not check_permissions(interaction.user, character, "marcos", server_data):
        await interaction.response.send_message(config["messages"]["erros"]["dinheiro_permissao"], ephemeral=True)
        return

    user_characters = server_data["characters"].get(user_id, {})
    if character not in user_characters:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)
        return

    character_data = user_characters[character]
    current_level = character_data["nivel"]
    marcos_to_add = marcos_to_gain(current_level)

    character_data["marcos"] += marcos_to_add
    new_marcos = character_data["marcos"]
    new_level = calculate_level(new_marcos / 16)

    if new_level > current_level:
        character_data["nivel"] = new_level
        await interaction.response.send_message(f'{character} subiu para o nível {new_level}!')
    else:
        fraction_added = ""
        if marcos_to_add == 4:
            fraction_added = "1/4 de Marco"
        elif marcos_to_add == 2:
            fraction_added = "1/8 de Marco"
        elif marcos_to_add == 1:
            fraction_added = "1/16 de Marco"

        await interaction.response.send_message(f'Adicionado {fraction_added} para {character}. '
                       f'Total: {format_marcos(new_marcos)} (Nível {new_level})')

    save_server_data(server_id, server_data)

@bot.tree.command(name="marcos", description="Mostra os Marcos e nível de um personagem")
@app_commands.describe(character="Nome do personagem")
@app_commands.autocomplete(character=autocomplete_character)
async def marcos(interaction: discord.Interaction, character: str):
    """
    Mostra os marcos e nível de um personagem.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    if not check_permissions(interaction.user, character, "marcos", server_data):
        await interaction.response.send_message(config["messages"]["erros"]["dinheiro_permissao"], ephemeral=True)
        return

    user_characters = server_data["characters"].get(user_id, {})
    if character in user_characters:
        character_data = user_characters[character]
        marcos = character_data["marcos"]
        level = calculate_level(marcos / 16)
        await interaction.response.send_message(f'{character} tem {format_marcos(marcos)} (Nível {level})')
    else:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)

@bot.tree.command(name="mochila", description="Mostra o inventário de um personagem")
@app_commands.describe(character="Nome do personagem")
@app_commands.autocomplete(character=autocomplete_character)
async def mochila(interaction: discord.Interaction, character: str):
    """
    Mostra o inventário de um personagem.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    # Permissão de visualização mantida
    if not check_permissions(interaction.user, character, "view", server_data):
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    user_characters = server_data["characters"].get(user_id, {})
    if character in user_characters and "inventory" in user_characters[character]:
        inventory = user_characters[character]["inventory"]
        if inventory:
            await interaction.response.send_message(f'Inventário de {character}: {", ".join(inventory)}')
        else:
            await interaction.response.send_message(f'O inventário de {character} está vazio.')
    else:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)

@bot.tree.command(name="comprar", description="Compra um item da loja")
@app_commands.describe(
    character="Nome do personagem",
    item="Nome do item a ser comprado"
)
@app_commands.autocomplete(character=autocomplete_character, item=autocomplete_item)
async def comprar(interaction: discord.Interaction, character: str, item: str):
    """
    Permite que um personagem compre um item da loja.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
        item (str): Nome do item.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    # Permissão de saldo mantida para compras
    if not check_permissions(interaction.user, character, "saldo", server_data):
        await interaction.response.send_message(config["messages"]["erros"]["dinheiro_permissao"], ephemeral=True)
        return

    user_characters = server_data["characters"].get(user_id, {})
    if character not in user_characters:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)
        return

    if not server_data.get("stock_items"):
        await interaction.response.send_message("A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
        return

    character_data = user_characters[character]
    item_found = False
    for rarity, items in server_data["stock_items"].items():
        if item in items['Name']:
            item_index = items['Name'].index(item)
            if items['Quantity'][item_index] > 0:
                item_value = int(items['Value'][item_index])

                if character_data["dinheiro"] < item_value:
                    await interaction.response.send_message(f"{character} não tem dinheiro suficiente para comprar {item}. "
                                   f"Preço: {item_value}, Dinheiro disponível: {character_data['dinheiro']}")
                    return

                character_data["dinheiro"] -= item_value
                character_data["inventory"].append(item)

                items['Quantity'][item_index] -= 1

                await interaction.response.send_message(f"{character} comprou {item} por {item_value} moedas. "
                               f"Dinheiro restante: {character_data['dinheiro']}")
                save_server_data(server_id, server_data)
                item_found = True
            else:
                await interaction.response.send_message(f"Desculpe, {item} está fora de estoque.")
                item_found = True
            break

    if not item_found:
        await interaction.response.send_message(f"Item '{item}' não encontrado na loja.")

@bot.tree.command(name="dinheiro", description="Define a quantidade de dinheiro de um personagem")
@app_commands.describe(
    character="Nome do personagem",
    amount="Quantidade de dinheiro"
)
@app_commands.autocomplete(character=autocomplete_character)
async def dinheiro(interaction: discord.Interaction, character: str, amount: int):
    """
    Define a quantidade de dinheiro de um personagem.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
        amount (int): Quantidade de dinheiro.
    """
    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    if not check_permissions(interaction.user, character, "saldo", server_data, allow_owner=False):
        await interaction.response.send_message(config["messages"]["erros"]["dinheiro_permissao"], ephemeral=True)
        return

    # Procurar o personagem em todos os usuários
    character_found = False
    for user_id, characters in server_data["characters"].items():
        if character in characters:
            character_data = characters[character]
            character_data["dinheiro"] = amount
            await interaction.response.send_message(f"Dinheiro de {character} definido como {amount} moedas.")
            save_server_data(server_id, server_data)
            character_found = True
            break

    if not character_found:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)

@bot.tree.command(name="saldo", description="Adiciona ou remove dinheiro do saldo de um personagem")
@app_commands.describe(
    character="Nome do personagem",
    amount="Quantidade de dinheiro (use números negativos para remover)"
)
@app_commands.autocomplete(character=autocomplete_character)
async def saldo(interaction: discord.Interaction, character: str, amount: int):
    """
    Adiciona ou remove dinheiro do saldo de um personagem.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
        amount (int): Quantidade de dinheiro.
    """
    server_id = str(interaction.guild_id)
    # user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    # Permissão de saldo restrita a cargos especiais
    if not check_permissions(interaction.user, character, "saldo", server_data):
        await interaction.response.send_message(config["messages"]["erros"]["dinheiro_permissao"], ephemeral=True)
        return

    # Procurar o personagem em todos os usuários
    character_found = False
    for user_id, characters in server_data["characters"].items():
        if character in characters:
            character_data = characters[character]
            character_data["dinheiro"] += amount

            if amount > 0:
                await interaction.response.send_message(f"Adicionado {amount} moedas ao saldo de {character}. Novo saldo: {character_data['dinheiro']} moedas.")
            else:
                await interaction.response.send_message(f"Removido {abs(amount)} moedas do saldo de {character}. Novo saldo: {character_data['dinheiro']} moedas.")

            save_server_data(server_id, server_data)
            character_found = True
            break

    if not character_found:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)

@bot.tree.command(name="carteira", description="Mostra quanto dinheiro um personagem tem")
@app_commands.describe(character="Nome do personagem")
@app_commands.autocomplete(character=autocomplete_character)
async def carteira(interaction: discord.Interaction, character: str):
    """
    Mostra quanto dinheiro um personagem tem.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
    """
    server_id = str(interaction.guild_id)
    # user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    # Permissão de saldo restrita a cargos especiais
    if not check_permissions(interaction.user, character, "saldo", server_data):
        await interaction.response.send_message(config["messages"]["erros"]["dinheiro_permissao"], ephemeral=True)
        return

    # Procurar o personagem em todos os usuários
    character_found = False
    for user_id, characters in server_data["characters"].items():
        if character in characters:
            character_data = characters[character]
            money = character_data.get("dinheiro", 0)
            await interaction.response.send_message(f"{character} tem {money} moedas.")
            character_found = True
            break

    if not character_found:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)

@bot.tree.command(name="limpar_estoque", description="Limpa o estoque atual da loja")
async def limpar_estoque(interaction: discord.Interaction):
    """
    Limpa o estoque atual da loja.

    Args:
        interaction (discord.Interaction): Interação do usuário.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)
    server_data["stock_items"] = {}
    save_server_data(server_id, server_data)

    await interaction.response.send_message("O estoque foi limpo com sucesso.")

@bot.tree.command(name="backup", description="Mostra um backup de todos os dados dos personagens")
async def backup(interaction: discord.Interaction):
    """
    Mostra um backup de todos os dados dos personagens.

    Args:
        interaction (discord.Interaction): Interação do usuário.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    backup_data = json.dumps(server_data, indent=2)
    if len(backup_data) <= 2000:
        await interaction.response.send_message(f"```json\n{backup_data}\n```")
    else:
        with open(f"backup_{server_id}.json", "w") as f:
            json.dump(server_data, f, indent=2)
        await interaction.response.send_message("O backup é muito grande para ser enviado como mensagem. Um arquivo foi criado no servidor.")

@bot.tree.command(name="listar_comandos", description="Lista todos os comandos disponíveis")
async def listar_comandos(interaction: discord.Interaction):
    """
    Lista todos os comandos disponíveis.

    Args:
        interaction (discord.Interaction): Interação do usuário.
    """
    comandos = [command.name for command in bot.tree.get_commands()]
    await interaction.response.send_message(f"Comandos disponíveis: {', '.join(comandos)}")

# Comando /mensagens para adicionar mensagens de trabalho ou crime
@bot.tree.command(name="mensagens", description="Adiciona uma mensagem para trabalho ou crime")
@app_commands.describe(
    tipo="Tipo de mensagem (trabalho ou crime)",
    mensagem="A mensagem a ser adicionada"
)
@app_commands.choices(
    tipo=[
        app_commands.Choice(name="Trabalho", value="trabalho"),
        app_commands.Choice(name="Crime", value="crime")
    ]
)
async def mensagens(interaction: discord.Interaction, tipo: str, mensagem: str):
    """
    Adiciona uma mensagem personalizada para trabalho ou crime.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        tipo (str): Tipo de mensagem ('trabalho' ou 'crime').
        mensagem (str): Mensagem a ser adicionada.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    if "messages" not in server_data:
        server_data["messages"] = {"trabalho": [], "crime": []}

    server_data["messages"][tipo].append(mensagem)
    save_server_data(server_id, server_data)
    await interaction.response.send_message(f"Mensagem adicionada ao tipo {tipo} com sucesso.")

# Comando /tiers para definir faixas de níveis e recompensas
@bot.tree.command(name="tiers", description="Define faixas de níveis para diferentes tiers")
@app_commands.describe(
    tier="Nome do tier",
    nivel_min="Nível mínimo",
    nivel_max="Nível máximo",
    recompensa="Recompensa em dinheiro"
)
async def tiers(interaction: discord.Interaction, tier: str, nivel_min: int, nivel_max: int, recompensa: int):
    """
    Define faixas de níveis e recompensas para tiers.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        tier (str): Nome do tier.
        nivel_min (int): Nível mínimo.
        nivel_max (int): Nível máximo.
        recompensa (int): Recompensa em dinheiro.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    if "tiers" not in server_data:
        server_data["tiers"] = {}

    server_data["tiers"][tier] = {
        "nivel_min": nivel_min,
        "nivel_max": nivel_max,
        "recompensa": recompensa
    }

    save_server_data(server_id, server_data)
    await interaction.response.send_message(f"Tier '{tier}' definido para níveis {nivel_min}-{nivel_max} com recompensa de {recompensa} moedas.")

@bot.tree.command(name="trabalhar", description="Trabalhe para ganhar dinheiro diariamente com base no seu tier")
@app_commands.describe(character="Nome do personagem")
@app_commands.autocomplete(character=autocomplete_character)
async def trabalhar(interaction: discord.Interaction, character: str):
    """
    Permite que um personagem trabalhe para ganhar dinheiro.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    if not check_permissions(interaction.user, character, "view", server_data, allow_owner=True):
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    user_characters = server_data["characters"].get(user_id, {})
    if character not in user_characters:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)
        return

    character_data = user_characters[character]

    last_work_time = character_data.get("last_work_time")
    now = datetime.datetime.now()
    intervalo_trabalhar = config.get("limites", {}).get("intervalo_trabalhar", 86400)
    if last_work_time:
        delta = now - datetime.datetime.fromisoformat(last_work_time)
        if delta.total_seconds() < intervalo_trabalhar:
            await interaction.response.send_message(config["messages"]["erros"]["acao_frequente"], ephemeral=True)
            return

    nivel = character_data.get("nivel", 0)
    tier_name = get_tier(nivel, server_data)
    if not tier_name:
        await interaction.response.send_message("Nenhum tier definido para o seu nível. Contate um administrador.", ephemeral=True)
        return

    tier = server_data["tiers"][tier_name]
    recompensa = tier["recompensa"]
    character_data["dinheiro"] += recompensa
    character_data["last_work_time"] = now.isoformat()

    mensagens = server_data.get("messages", {}).get("trabalho", config["messages"]["trabalho"])
    mensagem = random.choice(mensagens) if mensagens else "Você trabalhou duro e ganhou sua recompensa!"

    save_server_data(server_id, server_data)
    await interaction.response.send_message(f"{mensagem}\nVocê ganhou {recompensa} moedas. Saldo atual: {character_data['dinheiro']} moedas.")

@bot.tree.command(name="probabilidade_crime", description="Define a probabilidade de sucesso para o comando /crime")
@app_commands.describe(probabilidade="Probabilidade de sucesso (0 a 100)")
async def probabilidade_crime(interaction: discord.Interaction, probabilidade: int):
    """
    Define a probabilidade de sucesso para o comando /crime.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        probabilidade (int): Probabilidade de sucesso (0 a 100).
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    if not (0 <= probabilidade <= 100):
        await interaction.response.send_message("Por favor, insira um valor entre 0 e 100.", ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    server_data = load_server_data(server_id)

    server_data["probabilidade_crime"] = probabilidade
    save_server_data(server_id, server_data)
    await interaction.response.send_message(f"Probabilidade de sucesso no crime definida para {probabilidade}%.")

@bot.tree.command(name="crime", description="Arrisque ganhar ou perder dinheiro")
@app_commands.describe(character="Nome do personagem")
@app_commands.autocomplete(character=autocomplete_character)
async def crime(interaction: discord.Interaction, character: str):
    """
    Permite que um personagem arrisque ganhar ou perder dinheiro.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    # Permissão de visualização mantida
    if not check_permissions(interaction.user, character, "view", server_data):
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    user_characters = server_data["characters"].get(user_id, {})
    if character not in user_characters:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)
        return

    character_data = user_characters[character]

    last_crime_time = character_data.get("last_crime_time")
    now = datetime.datetime.now()
    intervalo_crime = config.get("limites", {}).get("intervalo_crime", 86400)
    if last_crime_time:
        delta = now - datetime.datetime.fromisoformat(last_crime_time)
        if delta.total_seconds() < intervalo_crime:
            await interaction.response.send_message(config["messages"]["erros"]["acao_frequente"], ephemeral=True)
            return

    probabilidade = server_data.get("probabilidade_crime", config.get("probabilidades", {}).get("crime", 50))
    chance = random.randint(1, 100)

    mensagens = server_data.get("messages", {}).get("crime", config["messages"]["crime"])
    mensagem = random.choice(mensagens) if mensagens else "Você tentou cometer um crime..."

    if chance <= probabilidade:
        recompensa = random.randint(100, 500)
        character_data["dinheiro"] += recompensa
        resultado = f"Sucesso! Você ganhou {recompensa} moedas."
    else:
        perda = random.randint(50, 250)
        character_data["dinheiro"] = max(0, character_data["dinheiro"] - perda)
        resultado = f"Você foi pego! Perdeu {perda} moedas."

    character_data["last_crime_time"] = now.isoformat()

    save_server_data(server_id, server_data)
    await interaction.response.send_message(f"{mensagem}\n{resultado}\nSaldo atual: {character_data['dinheiro']} moedas.")

# Autocomplete para personagens de um usuário específico
async def autocomplete_character_for_user(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """
    Autocomplete para personagens de um usuário específico.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        current (str): Entrada atual do usuário.

    Returns:
        list[app_commands.Choice[str]]: Lista de escolhas para autocomplete.
    """
    server_id = str(interaction.guild_id)
    user = interaction.namespace.user  # Obtém o usuário especificado no comando
    user_id = str(user.id)
    server_data = load_server_data(server_id)
    user_characters = server_data["characters"].get(user_id, {})
    return [
        app_commands.Choice(name=char_name, value=char_name)
        for char_name in user_characters if current.lower() in char_name.lower()
    ][:25]

@bot.tree.command(name="rip", description="Elimina definitivamente um personagem")
@app_commands.describe(
    user="Usuário dono do personagem",
    character="Nome do personagem a ser eliminado"
)
async def rip(interaction: discord.Interaction, user: Member, character: str):
    """
    Elimina definitivamente um personagem de um usuário.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        user (Member): Usuário dono do personagem.
        character (str): Nome do personagem.
    """
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
        return

    server_id = str(interaction.guild_id)
    user_id = str(user.id)
    server_data = load_server_data(server_id)

    user_characters = server_data["characters"].get(user_id, {})
    if character not in user_characters:
        await interaction.response.send_message(f"Personagem {character} não encontrado para o usuário {user.display_name}.", ephemeral=True)
        return

    await interaction.response.send_message(f"Tem certeza que deseja eliminar o personagem {character} de {user.display_name}? Responda 'sim' para confirmar.", ephemeral=True)

    def check(m):
        return m.author == interaction.user and m.content.lower() == 'sim'

    try:
        await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await interaction.followup.send("Tempo de confirmação esgotado. O personagem não foi eliminado.", ephemeral=True)
        return

    del user_characters[character]
    if not user_characters:
        del server_data["characters"][user_id]
    else:
        server_data["characters"][user_id] = user_characters

    save_server_data(server_id, server_data)
    await interaction.followup.send(f"Personagem {character} de {user.display_name} foi eliminado com sucesso.", ephemeral=True)

@rip.autocomplete('character')
async def rip_character_autocomplete(interaction: discord.Interaction, current: str):
    """
    Função de autocomplete para o parâmetro 'character' do comando '/rip'.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        current (str): Entrada atual do usuário.
    """
    return await autocomplete_character_for_user(interaction, current)

@bot.tree.command(name="inss", description="Aposenta um personagem, preservando seus dados")
@app_commands.describe(character="Nome do personagem")
@app_commands.autocomplete(character=autocomplete_character)
async def inss(interaction: discord.Interaction, character: str):
    """
    Aposenta um personagem, preservando seus dados.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        character (str): Nome do personagem.
    """
    server_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    server_data = load_server_data(server_id)

    user_characters = server_data["characters"].get(user_id, {})
    if character not in user_characters:
        await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)
        return

    if "aposentados" not in server_data:
        server_data["aposentados"] = {}

    server_data["aposentados"][character] = user_characters[character]
    del user_characters[character]

    if not user_characters:
        del server_data["characters"][user_id]
    else:
        server_data["characters"][user_id] = user_characters

    save_server_data(server_id, server_data)
    await interaction.response.send_message(f"Personagem {character} foi aposentado com sucesso e seus dados foram preservados.")

# Tratamento de erros global
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """
    Trata erros globais nos comandos de slash.

    Args:
        interaction (discord.Interaction): Interação do usuário.
        error (AppCommandError): Erro ocorrido.
    """
    await interaction.response.send_message(f"Ocorreu um erro ao executar o comando: {str(error)}", ephemeral=True)
    print(f"Erro no comando de aplicação: {error}")

@bot.event
async def on_error(event, *args, **kwargs):
    """
    Trata erros globais nos eventos.

    Args:
        event (str): Nome do evento.
    """
    print(f"Erro no evento {event}: {sys.exc_info()}")

@bot.event
async def on_command_error(ctx, error):
    """
    Trata erros globais nos comandos de prefixo.

    Args:
        ctx (Context): Contexto do comando.
        error (Exception): Erro ocorrido.
    """
    print(f"Erro no comando: {error}")

# Inicialização do bot
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("Nenhum token encontrado. Certifique-se de que você tem um arquivo .env com DISCORD_TOKEN definido.")

bot.run(TOKEN)
