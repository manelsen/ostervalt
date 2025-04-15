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
# Importar funções utilitárias do núcleo
from ostervalt.nucleo.utilitarios import calculate_level, formatar_marcos, marcos_to_gain # Corrigido: formatar_marcos

# Funções locais removidas

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

    async def _check_permissions(self, member: Member, target_personagem: Personagem | None, permission_type: str, allow_owner=True) -> bool:
        """Verifica permissões (Admin, Cargo Especial, Dono)."""
        if not member.guild: return False
        server_id = member.guild.id
        if member.guild_permissions.administrator: return True
        key = f"cargos_{permission_type}_ids"
        cargos_permitidos_ids = self.repo_config_servidor.obter_valor(server_id, key, default=[])
        if any(role.id in cargos_permitidos_ids for role in member.roles): return True
        if allow_owner and target_personagem and target_personagem.usuario_id == member.id: return True
        return False

    # --- Autocomplete Methods ---

    async def autocomplete_character(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocompleta com personagens do usuário (incluindo aposentados)."""
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
            choices.sort(key=lambda c: '(Aposentado)' in c.name)
            return choices[:25]
        except Exception as e:
            print(f"Erro no autocomplete_character (UtilCog): {e}")
            return []

    async def autocomplete_active_character(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocompleta apenas com personagens ATIVOS do usuário."""
        if not interaction.guild_id: return []
        user_id = interaction.user.id
        server_id = interaction.guild_id
        try:
            personagens: List[Personagem] = self.repo_personagens.listar_por_usuario(user_id, server_id)
            choices = [
                app_commands.Choice(name=p.nome, value=p.nome)
                for p in personagens
                if p.status == StatusPersonagem.ATIVO and current.lower() in p.nome.lower()
            ]
            return choices[:25]
        except Exception as e:
            print(f"Erro no autocomplete_active_character (UtilCog): {e}")
            return []

    async def autocomplete_character_for_user(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocompleta com personagens de um usuário específico (para comandos admin)."""
        if not interaction.guild_id: return []
        target_user: Member | None = None
        # Acessa as opções do comando atual
        if interaction.data and 'options' in interaction.data:
             options = interaction.data['options']
             # Verifica se é um subcomando
             if options and options[0].get('type') == discord.AppCommandOptionType.subcommand.value:
                 options = options[0].get('options', []) # Pega as opções do subcomando

             for option in options:
                 if option.get('name') == 'usuario' and option.get('type') == discord.AppCommandOptionType.user.value:
                      user_id = int(option['value'])
                      target_user = interaction.guild.get_member(user_id)
                      break

        if not target_user:
             print("Autocomplete Admin: Não foi possível determinar o usuário alvo da opção 'usuario'.")
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
    @app_commands.describe(character="Nome do personagem")
    @app_commands.autocomplete(character=autocomplete_character)
    async def carteira(self, interaction: discord.Interaction, character: str):
        """Mostra quanto dinheiro um personagem tem."""
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

            if not await self._check_permissions(interaction.user, target_personagem, "saldo", allow_owner=True):
                 await interaction.followup.send("🚫 Você não tem permissão para ver esta carteira.", ephemeral=True)
                 return

            status_str = f" (Status: {target_personagem.status.value.capitalize()})" if target_personagem.status else ""
            await interaction.followup.send(f"💰 {target_personagem.nome}{status_str} tem {target_personagem.dinheiro} moedas.", ephemeral=True)

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
    @app_commands.describe(character="Nome do personagem")
    @app_commands.autocomplete(character=autocomplete_character)
    async def marcos(self, interaction: discord.Interaction, character: str):
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

            if not await self._check_permissions(interaction.user, target_personagem, "marcos", allow_owner=True):
                 await interaction.followup.send("🚫 Você não tem permissão para ver estes marcos.", ephemeral=True)
                 return

            marcos_val = target_personagem.marcos
            level = calculate_level(marcos_val) # Usa função importada
            status_str = f" (Status: {target_personagem.status.value.capitalize()})" if target_personagem.status else ""
            await interaction.followup.send(f'🔰 {target_personagem.nome}{status_str} tem {formatar_marcos(marcos_val)} (Nível {level})', ephemeral=True) # Usa função importada

        except Exception as e:
            print(f"Erro no comando /marcos: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ Ocorreu um erro ao buscar os marcos.", ephemeral=True)


    @app_commands.command(name="up", description="Adiciona Marcos a um personagem ativo ou sobe de nível")
    @app_commands.describe(character="Nome do personagem ativo")
    @app_commands.autocomplete(character=autocomplete_active_character) # Usa autocomplete de ativos
    async def up(self, interaction: discord.Interaction, character: str):
        """Adiciona marcos a um personagem ativo ou sobe de nível."""
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

            if target_personagem.status == StatusPersonagem.APOSENTADO:
                 await interaction.followup.send(f"❌ Personagem '{character}' está aposentado e não pode receber /up.", ephemeral=True)
                 return

            if not await self._check_permissions(interaction.user, target_personagem, "marcos", allow_owner=True):
                 await interaction.followup.send("🚫 Você não tem permissão para usar /up neste personagem.", ephemeral=True)
                 return

            current_level = target_personagem.nivel
            marcos_to_add = marcos_to_gain(current_level) # Usa função importada

            current_marcos = target_personagem.marcos
            target_personagem.marcos = current_marcos + marcos_to_add
            new_marcos = target_personagem.marcos
            new_level = calculate_level(new_marcos) # Usa função importada
            target_personagem.nivel = new_level

            response_message = ""
            if new_level > current_level:
                response_message = f'🎉 {target_personagem.nome} subiu para o nível {new_level}!'
            else:
                fraction_added = f"{marcos_to_add}/16"
                response_message = f'✨ Adicionado {fraction_added} de Marco para {target_personagem.nome}. Total: {formatar_marcos(new_marcos)} (Nível {new_level})' # Usa função importada

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