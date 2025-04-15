# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands, Member
import random
from typing import List
import traceback

from ostervalt.nucleo.casos_de_uso.realizar_trabalho import RealizarTrabalho
from ostervalt.nucleo.casos_de_uso.cometer_crime import CometerCrime
from ostervalt.nucleo.casos_de_uso.obter_personagem import ObterPersonagem
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens
from ostervalt.nucleo.casos_de_uso.dtos import ResultadoTrabalhoDTO, ResultadoCrimeDTO, PersonagemDTO
from ostervalt.infraestrutura.persistencia.repositorio_configuracao_servidor import RepositorioConfiguracaoServidor
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.infraestrutura.persistencia.models import StatusPersonagem

class EconomiaCog(commands.Cog):
    """Cog para comandos relacionados à economia (trabalho, crime, etc.)."""

    def __init__(
        self,
        bot: commands.Bot,
        realizar_trabalho_uc: RealizarTrabalho,
        cometer_crime_uc: CometerCrime,
        obter_personagem_uc: ObterPersonagem,
        listar_personagens_uc: ListarPersonagens,
        repo_config_servidor: RepositorioConfiguracaoServidor,
    ):
        self.bot = bot
        self.realizar_trabalho_uc = realizar_trabalho_uc
        self.cometer_crime_uc = cometer_crime_uc
        self.obter_personagem_uc = obter_personagem_uc
        self.listar_personagens_uc = listar_personagens_uc
        self.repo_config_servidor = repo_config_servidor
        print("Cog Economia carregado.")

    # --- Autocomplete ---
    async def autocomplete_active_character(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocompleta apenas com personagens ATIVOS do usuário."""
        if not interaction.guild_id: return []
        user_id = interaction.user.id
        server_id = interaction.guild_id
        try:
            personagens: List[Personagem] = self.listar_personagens_uc.executar(usuario_id=user_id, servidor_id=server_id)
            choices = [
                app_commands.Choice(name=p.nome, value=p.nome)
                for p in personagens
                if p.status == StatusPersonagem.ATIVO and current.lower() in p.nome.lower()
            ]
            return choices[:25]
        except Exception as e:
            print(f"Erro no autocomplete_active_character (EconomiaCog): {e}")
            return []

    # --- Comandos Slash ---

    @app_commands.command(name="trabalhar", description="Realiza um trabalho para ganhar dinheiro.")
    @app_commands.describe(character="Nome do personagem ativo para trabalhar")
    @app_commands.autocomplete(character=autocomplete_active_character)
    async def trabalhar(self, interaction: discord.Interaction, character: str):
        """Executa a ação de trabalhar."""
        await interaction.response.defer(ephemeral=True)
        try:
            server_id = interaction.guild_id
            user_id = interaction.user.id
            if not server_id:
                 await interaction.followup.send("❌ Este comando só pode ser usado em um servidor.", ephemeral=True)
                 return

            # 1. Obter configurações do servidor (usando as chaves corretas do config.yaml)
            #    O repo_config_servidor já desserializa o JSON/valor.
            config_servidor = self.repo_config_servidor.listar_por_servidor_como_dict(server_id)
            intervalo_trabalhar = config_servidor.get('limites', {}).get('intervalo_trabalhar', 3600) # Padrão 1h
            tiers_config = config_servidor.get('tiers', {}) # Padrão dict vazio
            mensagens_trabalho = config_servidor.get('messages', {}).get('trabalho', ["Você trabalhou duro."]) # Padrão lista

            # 2. Obter ID do personagem ativo selecionado
            personagens_usuario: list[Personagem] = self.listar_personagens_uc.executar(
                usuario_id=user_id, servidor_id=server_id
            )
            personagem_selecionado_id: int | None = None
            for p in personagens_usuario:
                if p.nome.lower() == character.lower() and p.status == StatusPersonagem.ATIVO:
                    personagem_selecionado_id = p.id
                    break

            if personagem_selecionado_id is None:
                 await interaction.followup.send(f"❌ Personagem ativo '{character}' não encontrado.", ephemeral=True)
                 return

            # 3. Executar caso de uso com parâmetros corretos
            resultado_dto: ResultadoTrabalhoDTO = self.realizar_trabalho_uc.executar(
                personagem_id=personagem_selecionado_id,
                intervalo_trabalhar=intervalo_trabalhar,
                tiers_config=tiers_config,
                mensagens_trabalho=mensagens_trabalho
            )

            embed = discord.Embed(
                title="💼 Trabalho Concluído!",
                description=resultado_dto.mensagem,
                color=discord.Color.gold()
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
             print(f"Erro de valor ao trabalhar: {e}")
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao trabalhar: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao tentar trabalhar.", ephemeral=True)


    @app_commands.command(name="crime", description="Arrisque ganhar ou perder dinheiro")
    @app_commands.describe(character="Nome do personagem ativo para cometer o crime")
    @app_commands.autocomplete(character=autocomplete_active_character)
    async def crime(self, interaction: discord.Interaction, character: str):
        """Executa a ação de cometer um crime."""
        await interaction.response.defer()
        try:
            server_id = interaction.guild_id
            user_id = interaction.user.id
            if not server_id:
                 await interaction.followup.send("❌ Este comando só pode ser usado em um servidor.")
                 return

            # 1. Listar personagens do usuário para encontrar o ID do ATIVO selecionado
            personagens_usuario: list[Personagem] = self.listar_personagens_uc.executar(
                usuario_id=user_id, servidor_id=server_id
            )

            personagem_encontrado_id: int | None = None
            personagem_encontrado_nome: str | None = None
            for p in personagens_usuario:
                if p.nome.lower() == character.lower():
                    if p.status != StatusPersonagem.ATIVO:
                         await interaction.followup.send(f"❌ Personagem '{character}' não está ativo e não pode cometer crimes.", ephemeral=True)
                         return
                    personagem_encontrado_id = p.id
                    personagem_encontrado_nome = p.nome
                    break

            if personagem_encontrado_id is None:
                 await interaction.followup.send(f"❌ Personagem ativo '{character}' não encontrado para seu usuário.", ephemeral=True)
                 return

            # 2. Executar o caso de uso CometerCrime com o ID encontrado
            # A lógica de mensagens customizadas está dentro do UC CometerCrime
            resultado_dto: ResultadoCrimeDTO = self.cometer_crime_uc.executar(
                personagem_id=personagem_encontrado_id
            )

            # 3. Enviar a mensagem de resultado em um Embed
            embed = discord.Embed(
                title="🚨 Tentativa de Crime!",
                description=resultado_dto.mensagem,
                color=discord.Color.red() if not resultado_dto.sucesso else discord.Color.dark_green()
            )
            embed.set_footer(text=f"Personagem: {personagem_encontrado_nome}")

            await interaction.followup.send(embed=embed)

        except ValueError as e:
             print(f"Erro de valor ao cometer crime: {e}")
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao cometer crime: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao tentar cometer o crime.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # A injeção é feita pelo carregador_cogs.py
    pass