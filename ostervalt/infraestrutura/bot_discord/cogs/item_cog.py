# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands

from ostervalt.nucleo.casos_de_uso.obter_item import ObterItem
from ostervalt.nucleo.casos_de_uso.listar_itens import ListarItens
from ostervalt.nucleo.casos_de_uso.dtos import ItemDTO, ListaItensDTO, ComandoDTO

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
        print("Cog Item carregado.") # Log para depuração

    # --- Comandos Slash ---

    @app_commands.command(name="iteminfo", description="Mostra informações detalhadas sobre um item.")
    @app_commands.describe(item_id="O ID do item que você quer ver")
    async def ver_item_info(self, interaction: discord.Interaction, item_id: int):
        """Exibe detalhes sobre um item específico."""
        await interaction.response.defer(ephemeral=True)
        try:
            comando_dto = ComandoDTO(
                discord_id=interaction.user.id, # ID do usuário que pediu
                parametros={'item_id': item_id}
            )
            resultado_dto: ItemDTO = self.obter_item_uc.executar(comando_dto)

            embed = discord.Embed(
                title=f"ℹ️ Informações do Item: {resultado_dto.nome}",
                description=f"*{resultado_dto.descricao}*",
                color=discord.Color.light_grey()
            )
            embed.add_field(name="ID", value=resultado_dto.id, inline=True)
            embed.add_field(name="Tipo", value=resultado_dto.tipo.capitalize(), inline=True)
            embed.add_field(name="Preço", value=f"🪙 {resultado_dto.preco}", inline=True)
            # Adicionar mais detalhes se disponíveis no DTO (e.g., atributos, raridade)
            # embed.add_field(name="Atributos", value=str(resultado_dto.atributos), inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            # TODO: Tratar exceção ItemNaoEncontrado
            print(f"Erro ao obter informações do item: {e}")
            await interaction.followup.send(f"❌ Não foi possível encontrar o item com ID {item_id}. Erro: {e}", ephemeral=True)

    @app_commands.command(name="loja", description="Mostra os itens disponíveis para compra.")
    async def ver_loja(self, interaction: discord.Interaction):
        """Exibe os itens disponíveis na loja."""
        await interaction.response.defer(ephemeral=True)
        try:
            # Este caso de uso pode precisar de filtros no futuro (e.g., itens compráveis)
            comando_dto = ComandoDTO(discord_id=interaction.user.id)
            resultado_dto: ListaItensDTO = self.listar_itens_uc.executar(comando_dto)

            if not resultado_dto.itens:
                await interaction.followup.send("🛒 A loja está vazia no momento.", ephemeral=True)
                return

            embed = discord.Embed(
                title="🛒 Loja de Ostervalt",
                description="Itens disponíveis para compra:",
                color=discord.Color.dark_blue()
            )
            for item in resultado_dto.itens:
                 embed.add_field(
                    name=f"{item.nome} (ID: {item.id})",
                    value=f"Preço: 🪙 {item.preco}\n*'{item.descricao}'*",
                    inline=False
                )
            # TODO: Adicionar paginação se a lista for muito grande

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Erro ao listar itens da loja: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro ao buscar os itens da loja: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # TODO: Instanciar e injetar os casos de uso aqui
    # Exemplo (precisa ser substituído pela injeção real):
    # from ostervalt.infraestrutura.persistencia.repositorio_itens import RepositorioItensSQLAlchemy
    # from ostervalt.infraestrutura.configuracao.db import SessionLocal
    # repo = RepositorioItensSQLAlchemy(SessionLocal)
    # obter_uc = ObterItem(repo)
    # listar_uc = ListarItens(repo)
    # await bot.add_cog(ItemCog(bot, obter_uc, listar_uc))
    print("Função setup do ItemCog chamada, mas a injeção de dependência real precisa ser configurada.")
    # Por enquanto, não adicionaremos o Cog até a injeção estar pronta no ostervalt.py
    pass