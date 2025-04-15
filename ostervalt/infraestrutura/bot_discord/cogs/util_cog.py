# -*- coding: utf-8 -*-
import discord
import asyncio
import datetime
import math
import traceback
from discord.ext import commands
from discord import app_commands, Member
from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
from ostervalt.infraestrutura.persistencia.repositorio_configuracao_servidor import RepositorioConfiguracaoServidor
from ostervalt.infraestrutura.persistencia.models import StatusPersonagem, PersonagemModel
from ostervalt.nucleo.entidades.personagem import Personagem
from typing import List

# Funções utilitárias
def calculate_level(marcos_val: int | float) -> int:
    if not isinstance(marcos_val, (int, float)) or marcos_val < 0: return 1
    level = math.floor(marcos_val / 16) + 1
    return max(1, min(level, 20))

def format_marcos(marcos_val: int) -> str:
    if not isinstance(marcos_val, int) or marcos_val < 0: return "0 Marcos"
    full_marcos = marcos_val // 16
    remaining_parts = marcos_val % 16
    level = calculate_level(marcos_val)
    if remaining_parts == 0: return f"{full_marcos} Marcos"
    else:
        if level > 4: return f"{full_marcos} e {remaining_parts}/16 Marcos"
        else: return f"{full_marcos} Marcos"

def marcos_to_gain(level: int) -> int:
    if level <= 4: return 16
    elif level <= 12: return 4
    elif level <= 16: return 2
    else: return 1

class UtilCog(commands.Cog):
    """Cog para comandos utilitários gerais do bot."""
    def __init__(
        self,
        bot: commands.Bot,
        repo_personagens: RepositorioPersonagensSQLAlchemy,
        repo_config_servidor: RepositorioConfiguracaoServidor
    ):
        self.bot = bot
        self.repo_personagens = repo_personagens
        self.repo_config_servidor = repo_config_servidor
        print("Cog Util carregado.")

    # --- Métodos Auxiliares ---

    # Removido _get_personagem_ativo - seleção será explícita

    async def _check_permissions(self, member: Member, target_personagem: Personagem | None, permission_type: str, allow_owner=True) -> bool:
        """Verifica permissões (Admin, Cargo Especial, Dono)."""
        if not member.guild: return False
        server_id = member.guild.id
        if member.guild_permissions.administrator: return True
        key = f"cargos_{permission_type}_ids"
        cargos_permitidos_ids = self.repo_config_servidor.obter_valor(server_id, key, default=[])
        if any(role.id in cargos_permitidos_ids for role in member.roles): return True
        # Dono só pode ser verificado se target_personagem foi fornecido e encontrado
        if allow_owner and target_personagem and target_personagem.usuario_id == member.id: return True
        return False

    # --- Autocomplete Methods ---

    async def autocomplete_character(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocompleta com personagens do usuário (incluindo aposentados para alguns comandos)."""
        # Nota: Este autocomplete básico não filtra por status.
        # Comandos específicos podem precisar filtrar a lista retornada ou ter autocompletes dedicados.
        if not interaction.guild_id: return []
        user_id = interaction.user.id
        server_id = interaction.guild_id
        try:
            personagens: List[Personagem] = self.repo_personagens.listar_por_usuario(user_id, server_id)
            choices = [
                app_commands.Choice(name=f"{p.nome}{' (Aposentado)' if p.status == StatusPersonagem.APOSENTADO else ''}", value=p.nome)
                for p in personagens
                if current.lower() in p.nome.lower()
            ]
            # Ordena para mostrar ativos primeiro (opcional)
            choices.sort(key=lambda c: '(Aposentado)' in c.name)
            return choices[:25]
        except Exception as e:
            print(f"Erro no autocomplete_character (UtilCog): {e}")
            return []

    async def autocomplete_character_for_user(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocompleta com personagens de um usuário específico (para comandos admin)."""
        if not interaction.guild_id: return []
        target_user = interaction.namespace.usuario # Assume que a opção se chama 'usuario'
        if not isinstance(target_user, Member):
             print("Autocomplete Admin: Não foi possível determinar o usuário alvo.")
             return []
        target_user_id = target_user.id
        server_id = interaction.guild_id
        try:
            personagens: List[Personagem] = self.repo_personagens.listar_por_usuario(target_user_id, server_id)
            choices = [
                 app_commands.Choice(name=f"{p.nome}{' (Aposentado)' if p.status == StatusPersonagem.APOSENTADO else ''}", value=p.nome)
                for p in personagens
                if current.lower() in p.nome.lower()
            ]
            choices.sort(key=lambda c: '(Aposentado)' in c.name)
            return choices[:25]
        except Exception as e:
            print(f"Erro no autocomplete_character_for_user (UtilCog): {e}")
            return []

    async def autocomplete_item(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        print(f"[Autocomplete Item] Buscando: {current} (Implementação Pendente em UtilCog)")
        return []


    # --- Commands ---
    @app_commands.command(name="carteira", description="Mostra quanto dinheiro um personagem tem")
    @app_commands.describe(character="Nome do personagem") # Tornou obrigatório
    @app_commands.autocomplete(character=autocomplete_character)
    async def carteira(self, interaction: discord.Interaction, character: str): # Removido | None = None
        """Mostra quanto dinheiro um personagem tem."""
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        server_id = interaction.guild_id
        if not server_id:
             await interaction.followup.send("❌ Este comando só pode ser usado em um servidor.", ephemeral=True)
             return

        try:
            target_personagem: Personagem | None = None
            # Buscar personagem específico pelo nome
            personagens_usuario = self.repo_personagens.listar_por_usuario(user_id, server_id)
            for p in personagens_usuario:
                if p.nome.lower() == character.lower():
                    target_personagem = p
                    break

            if not target_personagem:
                await interaction.followup.send(f"❌ Personagem '{character}' não encontrado para seu usuário.", ephemeral=True)
                return

            # Verificar permissão (dono ou cargo 'saldo')
            if not await self._check_permissions(interaction.user, target_personagem, "saldo", allow_owner=True):
                 await interaction.followup.send("🚫 Você não tem permissão para ver esta carteira.", ephemeral=True)
                 return

            await interaction.followup.send(f"💰 {target_personagem.nome} tem {target_personagem.dinheiro} moedas.", ephemeral=True)

        except Exception as e:
            print(f"Erro no comando /carteira: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ Ocorreu um erro ao buscar a carteira.", ephemeral=True)


    @app_commands.command(name="listar_comandos", description="Lista todos os comandos de slash disponíveis")
    async def listar_comandos_slash(self, interaction: discord.Interaction):
        """Lista todos os comandos de slash disponíveis."""
        all_commands = self.bot.tree.get_commands(guild=interaction.guild)
        command_names = sorted([cmd.name for cmd in all_commands])

        if command_names:
            formatted_list = [f"`/{name}`" for name in command_names]
            message_content = f"Comandos disponíveis:\n" + "\n".join(formatted_list)
            if len(message_content) > 1900:
                 parts = []
                 current_part = "Comandos disponíveis:\n"
                 for name in formatted_list:
                      if len(current_part) + len(name) + 1 > 1900:
                           parts.append(current_part)
                           current_part = ""
                      current_part += name + "\n"
                 parts.append(current_part)
                 await interaction.response.send_message(parts[0], ephemeral=True)
                 for part in parts[1:]:
                      await interaction.followup.send(part, ephemeral=True)
            else:
                 await interaction.response.send_message(message_content, ephemeral=True)
        else:
            await interaction.response.send_message("Nenhum comando de slash encontrado.", ephemeral=True)


    @app_commands.command(name="marcos", description="Mostra os Marcos e nível de um personagem")
    @app_commands.describe(character="Nome do personagem") # Tornou obrigatório
    @app_commands.autocomplete(character=autocomplete_character)
    async def marcos(self, interaction: discord.Interaction, character: str): # Removido | None = None
        """Mostra os marcos e nível de um personagem."""
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        server_id = interaction.guild_id
        if not server_id:
             await interaction.followup.send("❌ Este comando só pode ser usado em um servidor.", ephemeral=True)
             return

        try:
            target_personagem: Personagem | None = None
            personagens_usuario = self.repo_personagens.listar_por_usuario(user_id, server_id)
            for p in personagens_usuario:
                if p.nome.lower() == character.lower():
                    target_personagem = p
                    break

            if not target_personagem:
                await interaction.followup.send(f"❌ Personagem '{character}' não encontrado para seu usuário.", ephemeral=True)
                return

            # Verificar permissão (dono ou cargo 'marcos')
            if not await self._check_permissions(interaction.user, target_personagem, "marcos", allow_owner=True):
                 await interaction.followup.send("🚫 Você não tem permissão para ver estes marcos.", ephemeral=True)
                 return

            marcos_val = target_personagem.marcos
            level = calculate_level(marcos_val)
            await interaction.followup.send(f'🔰 {target_personagem.nome} tem {format_marcos(marcos_val)} (Nível {level})', ephemeral=True)

        except Exception as e:
            print(f"Erro no comando /marcos: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ Ocorreu um erro ao buscar os marcos.", ephemeral=True)


    @app_commands.command(name="up", description="Adiciona Marcos a um personagem ou sobe de nível")
    @app_commands.describe(character="Nome do personagem") # Tornou obrigatório
    @app_commands.autocomplete(character=autocomplete_character) # Autocomplete agora filtra ativos
    async def up(self, interaction: discord.Interaction, character: str): # Removido | None = None
        """Adiciona marcos a um personagem ou sobe de nível."""
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        server_id = interaction.guild_id
        if not server_id:
             await interaction.followup.send("❌ Este comando só pode ser usado em um servidor.", ephemeral=True)
             return

        try:
            target_personagem: Personagem | None = None
            personagens_usuario = self.repo_personagens.listar_por_usuario(user_id, server_id)
            for p in personagens_usuario:
                if p.nome.lower() == character.lower():
                    target_personagem = p
                    break

            if not target_personagem:
                await interaction.followup.send(f"❌ Personagem '{character}' não encontrado para seu usuário.", ephemeral=True)
                return

            # Verificar se personagem está aposentado ANTES de checar permissão
            if target_personagem.status == StatusPersonagem.APOSENTADO:
                 await interaction.followup.send(f"❌ Personagem '{character}' está aposentado e não pode receber /up.", ephemeral=True)
                 return

            # Verificar permissão (dono ou cargo 'marcos')
            if not await self._check_permissions(interaction.user, target_personagem, "marcos", allow_owner=True):
                 await interaction.followup.send("🚫 Você não tem permissão para usar /up neste personagem.", ephemeral=True)
                 return

            current_level = target_personagem.nivel
            marcos_to_add = marcos_to_gain(current_level)

            current_marcos = target_personagem.marcos
            target_personagem.marcos = current_marcos + marcos_to_add
            new_marcos = target_personagem.marcos
            new_level = calculate_level(new_marcos)
            target_personagem.nivel = new_level

            response_message = ""
            if new_level > current_level:
                response_message = f'🎉 {target_personagem.nome} subiu para o nível {new_level}!'
            else:
                fraction_added = f"{marcos_to_add}/16"
                response_message = f'✨ Adicionado {fraction_added} de Marco para {target_personagem.nome}. Total: {format_marcos(new_marcos)} (Nível {new_level})'

            self.repo_personagens.atualizar(target_personagem)
            await interaction.followup.send(response_message, ephemeral=True)

        except Exception as e:
            print(f"Erro inesperado no comando /up: {type(e).__name__} - {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ Ocorreu um erro inesperado ao tentar dar up.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # A injeção é feita pelo carregador_cogs.py
    pass