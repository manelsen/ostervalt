# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
from typing import List

from ostervalt.nucleo.casos_de_uso.obter_item import ObterItem
from ostervalt.nucleo.casos_de_uso.listar_itens import ListarItens
# Removido ListaItensDTO, UC retorna List[Item]
# Removido ComandoDTO, não usado aqui
from ostervalt.nucleo.casos_de_uso.dtos import ItemDTO
from ostervalt.nucleo.entidades.item import Item # Importar entidade

class ItemCog(commands.Cog):
    """Cog para comandos relacionados a itens (informações, loja)."""

    def __init__(
        self,
        bot: commands.Bot,
        obter_item_uc: ObterItem,
        listar_itens_uc: ListarItens,
    ):
        self.bot = bot
        self.obter_item_uc = obter_item_uc
        self.listar_itens_uc = listar_itens_uc
        print("Cog Item carregado.")

    # --- Comandos Slash ---

    @app_commands.command(name="iteminfo", description="Mostra informações detalhadas sobre um item.")
    @app_commands.describe(item_id="O ID do item que você quer ver")
    async def ver_item_info(self, interaction: discord.Interaction, item_id: int):
        """Exibe detalhes sobre um item específico."""
        await interaction.response.defer(ephemeral=True)
        try:
            # O caso de uso ObterItem espera apenas item_id
            resultado_item: Item | None = self.obter_item_uc.executar(item_id=item_id) # UC retorna Entidade ou None

            if resultado_item is None:
                 await interaction.followup.send(f"❌ Não foi possível encontrar o item com ID {item_id}.", ephemeral=True)
                 return

            # Criar embed a partir da entidade Item
            embed = discord.Embed(
                title=f"ℹ️ Informações do Item: {resultado_item.nome}",
                description=f"*{resultado_item.descricao}*",
                color=discord.Color.light_grey()
            )
            embed.add_field(name="ID", value=resultado_item.id, inline=True)
            embed.add_field(name="Raridade", value=resultado_item.raridade.capitalize(), inline=True)
            embed.add_field(name="Valor Padrão", value=f"🪙 {resultado_item.valor}", inline=True)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e: # Captura erro se item não for encontrado pelo UC
            print(f"Erro ao obter informações do item {item_id}: {e}")
            await interaction.followup.send(f"❌ Não foi possível encontrar o item com ID {item_id}.", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao obter informações do item: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao buscar informações do item.", ephemeral=True)


    @app_commands.command(name="loja", description="Mostra os itens disponíveis para compra.")
    async def ver_loja(self, interaction: discord.Interaction):
        """Exibe os itens disponíveis na loja."""
        # TODO: Idealmente, a loja deveria mostrar itens do EstoqueLoja, não todos os itens mestres.
        # Isso requer um novo caso de uso ou modificação do ListarItens/AdminCog.
        # Por ora, listamos todos os itens mestres como fallback.
        await interaction.response.defer(ephemeral=True)
        try:
            # ListarItens.executar retorna List[Item]
            itens_disponiveis: List[Item] = self.listar_itens_uc.executar() # Chamada corrigida

            if not itens_disponiveis:
                # Mensagem ajustada - pode não haver itens cadastrados
                await interaction.followup.send("🛒 Nenhum item encontrado no catálogo mestre.", ephemeral=True)
                return

            embed = discord.Embed(
                title="<0xF0><0x9F><0xAA><0x9A> Catálogo Mestre de Itens", # Título ajustado
                description="Itens existentes no mundo (preços podem variar na loja):",
                color=discord.Color.dark_blue()
            )
            for item in itens_disponiveis:
                 embed.add_field(
                    name=f"{item.nome} (ID: {item.id})",
                    value=f"Valor Padrão: 🪙 {item.valor}\n*'{item.descricao}'*", # Usa dados da entidade Item
                    inline=False
                )
            # TODO: Adicionar paginação se a lista for muito grande

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Erro ao listar itens da loja: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro ao buscar os itens.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # A injeção é feita pelo carregador_cogs.py
    pass