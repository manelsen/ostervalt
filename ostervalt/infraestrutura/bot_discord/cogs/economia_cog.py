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
from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy # Import adicionado
# Importar utilitários do Cog
from ostervalt.infraestrutura.bot_discord.discord_helpers import (
    obter_contexto_comando,
    buscar_personagem_por_nome,
    autocomplete_active_character as util_autocomplete_active_character, # Importa e renomeia
    ComandoForaDeServidorError,
    PersonagemNaoEncontradoError,
    CogUtilsError
)

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
        repo_personagens: RepositorioPersonagensSQLAlchemy, # Dependência adicionada
    ):
        self.bot = bot
        self.realizar_trabalho_uc = realizar_trabalho_uc
        self.cometer_crime_uc = cometer_crime_uc
        self.obter_personagem_uc = obter_personagem_uc
        self.listar_personagens_uc = listar_personagens_uc
        self.repo_config_servidor = repo_config_servidor
        self.repo_personagens = repo_personagens # Dependência armazenada
        print("Cog Economia carregado.")

    # --- Autocomplete ---

    # Usa a função centralizada de discord_helpers, passando o repositório injetado
    async def character_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return await util_autocomplete_active_character(interaction, current, self.repo_personagens)

    # --- Comandos Slash ---

    @app_commands.command(name="trabalhar", description="Realiza um trabalho para ganhar dinheiro.")
    @app_commands.describe(character="Nome do personagem ativo para trabalhar")
    @app_commands.autocomplete(character=character_autocomplete) # Autocomplete ativado
    async def trabalhar(self, interaction: discord.Interaction, character: str):
        """Executa a ação de trabalhar."""
        await interaction.response.defer(ephemeral=True)
        try:
            user_id, server_id = await obter_contexto_comando(interaction)

            # 1. Obter configurações do servidor
            config_servidor = self.repo_config_servidor.listar_por_servidor_como_dict(server_id)
            intervalo_trabalhar = config_servidor.get('limites', {}).get('intervalo_trabalhar', 3600) # Padrão 1h
            tiers_config = config_servidor.get('tiers', {}) # Padrão dict vazio
            mensagens_trabalho = config_servidor.get('messages', {}).get('trabalho', ["Você trabalhou duro."]) # Padrão lista

            # 2. Buscar personagem ativo selecionado
            personagem_selecionado = await buscar_personagem_por_nome(
                interaction, character, self.listar_personagens_uc, apenas_ativos=True
            )

            # 3. Executar caso de uso com parâmetros corretos
            resultado_dto: ResultadoTrabalhoDTO = self.realizar_trabalho_uc.executar(
                personagem_id=personagem_selecionado.id,
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

        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             await interaction.followup.send(f"❌ {e.mensagem}", ephemeral=True)
        except ValueError as e: # Erros específicos do caso de uso (ex: cooldown)
             print(f"Erro de valor ao trabalhar: {e}")
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao trabalhar: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao tentar trabalhar.", ephemeral=True)


    @app_commands.command(name="crime", description="Arrisque ganhar ou perder dinheiro")
    @app_commands.describe(character="Nome do personagem ativo para cometer o crime")
    @app_commands.autocomplete(character=character_autocomplete) # Autocomplete ativado
    async def crime(self, interaction: discord.Interaction, character: str):
        """Executa a ação de cometer um crime."""
        await interaction.response.defer() # Defer público para crime
        try:
            # 1. Buscar personagem ativo selecionado
            personagem_encontrado = await buscar_personagem_por_nome(
                interaction, character, self.listar_personagens_uc, apenas_ativos=True
            )

            # 2. Executar o caso de uso CometerCrime com o ID encontrado
            # A lógica de mensagens customizadas está dentro do UC CometerCrime
            resultado_dto: ResultadoCrimeDTO = self.cometer_crime_uc.executar(
                personagem_id=personagem_encontrado.id
            )

            # 3. Enviar a mensagem de resultado em um Embed
            embed = discord.Embed(
                title="🚨 Tentativa de Crime!",
                description=resultado_dto.mensagem,
                color=discord.Color.red() if not resultado_dto.sucesso else discord.Color.dark_green()
            )
            embed.set_footer(text=f"Personagem: {personagem_encontrado.nome}") # Usar nome do objeto encontrado

            await interaction.followup.send(embed=embed) # Envio público

        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             # Enviar erro como ephemeral, mesmo que o defer seja público
             await interaction.followup.send(f"❌ {e.mensagem}", ephemeral=True)
        except ValueError as e: # Erros específicos do caso de uso (ex: cooldown)
             print(f"Erro de valor ao cometer crime: {e}")
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao cometer crime: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao tentar cometer o crime.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # A injeção é feita pelo carregador_cogs.py
    pass