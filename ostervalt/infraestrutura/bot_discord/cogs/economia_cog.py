# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
import random # Para adicionar alguma variação nas mensagens

from ostervalt.nucleo.casos_de_uso.realizar_trabalho import RealizarTrabalho
from ostervalt.nucleo.casos_de_uso.cometer_crime import CometerCrime
from ostervalt.nucleo.casos_de_uso.dtos import ResultadoTrabalhoDTO, ResultadoCrimeDTO, ComandoDTO

class EconomiaCog(commands.Cog):
    """Cog para comandos relacionados à economia (trabalho, crime, etc.)."""

    def __init__(
        self,
        bot: commands.Bot,
        realizar_trabalho_uc: RealizarTrabalho,
        cometer_crime_uc: CometerCrime,
    ):
        self.bot = bot
        self.realizar_trabalho_uc = realizar_trabalho_uc
        self.cometer_crime_uc = cometer_crime_uc
        print("Cog Economia carregado.") # Log para depuração

    # --- Comandos Slash ---

    @app_commands.command(name="trabalhar", description="Realiza um trabalho para ganhar dinheiro e experiência.")
    async def trabalhar(self, interaction: discord.Interaction):
        """Executa a ação de trabalhar."""
        await interaction.response.defer(ephemeral=True)
        try:
            # TODO: Precisará do ID do personagem ativo no futuro
            comando_dto = ComandoDTO(discord_id=interaction.user.id)
            resultado_dto: ResultadoTrabalhoDTO = self.realizar_trabalho_uc.executar(comando_dto)

            embed = discord.Embed(
                title="💼 Trabalho Concluído!",
                description=resultado_dto.mensagem,
                color=discord.Color.gold()
            )
            embed.add_field(name="Dinheiro Ganho", value=f"🪙 {resultado_dto.dinheiro_ganho}", inline=True)
            embed.add_field(name="Experiência Ganha", value=f"✨ {resultado_dto.xp_ganho}", inline=True)
            embed.add_field(name="Energia Restante", value=f"⚡ {resultado_dto.energia_atual}/{resultado_dto.energia_maxima}", inline=True)
            if resultado_dto.subiu_de_nivel:
                embed.add_field(name="🎉 Nível Acima!", value=f"Você alcançou o nível {resultado_dto.novo_nivel}!", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            # TODO: Tratar exceções específicas (e.g., sem energia, personagem não encontrado)
            print(f"Erro ao trabalhar: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro ao tentar trabalhar: {e}", ephemeral=True)

    @app_commands.command(name="crime", description="Tenta cometer um crime. Cuidado, pode dar errado!")
    async def crime(self, interaction: discord.Interaction):
        """Executa a ação de cometer um crime."""
        await interaction.response.defer(ephemeral=True)
        try:
            # TODO: Precisará do ID do personagem ativo no futuro
            comando_dto = ComandoDTO(discord_id=interaction.user.id)
            resultado_dto: ResultadoCrimeDTO = self.cometer_crime_uc.executar(comando_dto)

            if resultado_dto.sucesso:
                embed = discord.Embed(
                    title="💰 Crime Bem-Sucedido!",
                    description=resultado_dto.mensagem,
                    color=discord.Color.dark_green()
                )
                embed.add_field(name="Dinheiro Ganho", value=f"🪙 {resultado_dto.dinheiro_ganho}", inline=True)
                embed.add_field(name="Experiência Ganha", value=f"✨ {resultado_dto.xp_ganho}", inline=True)
            else:
                embed = discord.Embed(
                    title="🚓 Crime Fracassado!",
                    description=resultado_dto.mensagem,
                    color=discord.Color.red()
                )
                embed.add_field(name="Dinheiro Perdido", value=f"🪙 {resultado_dto.dinheiro_perdido}", inline=True)
                embed.add_field(name="Vida Perdida", value=f"💔 {resultado_dto.vida_perdida}", inline=True)

            embed.add_field(name="Energia Restante", value=f"⚡ {resultado_dto.energia_atual}/{resultado_dto.energia_maxima}", inline=True)
            if resultado_dto.subiu_de_nivel:
                 embed.add_field(name="🎉 Nível Acima!", value=f"Você alcançou o nível {resultado_dto.novo_nivel}!", inline=False)


            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            # TODO: Tratar exceções específicas (e.g., sem energia, personagem não encontrado, em cooldown)
            print(f"Erro ao cometer crime: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro ao tentar cometer um crime: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # TODO: Instanciar e injetar os casos de uso aqui
    # Exemplo (precisa ser substituído pela injeção real):
    # from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
    # from ostervalt.infraestrutura.configuracao.db import SessionLocal
    # repo_personagem = RepositorioPersonagensSQLAlchemy(SessionLocal) # Exemplo, pode precisar de outros repos
    # trabalho_uc = RealizarTrabalho(repo_personagem) # Simplificado
    # crime_uc = CometerCrime(repo_personagem) # Simplificado
    # await bot.add_cog(EconomiaCog(bot, trabalho_uc, crime_uc))
    print("Função setup do EconomiaCog chamada, mas a injeção de dependência real precisa ser configurada.")
    # Por enquanto, não adicionaremos o Cog até a injeção estar pronta no ostervalt.py
    pass