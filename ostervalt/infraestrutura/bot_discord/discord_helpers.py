# -*- coding: utf-8 -*-
import discord
import traceback
from typing import Tuple, Optional, List
from discord import Member, app_commands, Interaction # Ajustado imports
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.nucleo.entidades.item import Item
from ostervalt.infraestrutura.persistencia.models import StatusPersonagem
from ostervalt.infraestrutura.persistencia.repositorio_configuracao_servidor import RepositorioConfiguracaoServidor
from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
from ostervalt.infraestrutura.persistencia.repositorio_itens import RepositorioItensSQLAlchemy

# --- Exceções Customizadas ---

class CogUtilsError(Exception):
    """Exceção base para erros nos utilitários dos Cogs."""
    pass

class ComandoForaDeServidorError(CogUtilsError):
    """Exceção para comandos executados fora de um servidor quando não permitido."""
    def __init__(self, mensagem="Este comando só pode ser usado em um servidor."):
        self.mensagem = mensagem
        super().__init__(self.mensagem)

class PersonagemNaoEncontradoError(CogUtilsError):
    """Exceção para quando um personagem específico não é encontrado."""
    def __init__(self, nome_personagem: str, mensagem: Optional[str] = None):
        self.nome_personagem = nome_personagem
        self.mensagem = mensagem or f"Personagem '{nome_personagem}' não encontrado."
        super().__init__(self.mensagem)

class PermissaoNegadaError(CogUtilsError):
    """Exceção para quando uma ação é bloqueada por falta de permissão."""
    def __init__(self, mensagem: str = "Você não tem permissão para realizar esta ação."):
        self.mensagem = mensagem
        super().__init__(self.mensagem)

# --- Funções de Contexto e Validação ---

async def obter_contexto_comando(interaction: Interaction) -> Tuple[int, int]:
    """
    Obtém o user_id e server_id da interação. Lança ComandoForaDeServidorError se não estiver em um servidor.
    Retorna: Tuple[int, int]: (user_id, server_id).
    """
    user_id = interaction.user.id
    server_id = interaction.guild_id
    if not server_id:
        raise ComandoForaDeServidorError()
    return user_id, server_id

# --- Funções de Busca de Personagem ---

async def buscar_personagem_por_nome(
    interaction: Interaction,
    nome_personagem: str,
    listar_personagens_uc: ListarPersonagens, # Dependência do Caso de Uso
    apenas_ativos: bool = False
) -> Personagem:
    """
    Busca um personagem específico do usuário da interação pelo nome.
    Raises: ComandoForaDeServidorError, PersonagemNaoEncontradoError, CogUtilsError.
    """
    user_id, server_id = await obter_contexto_comando(interaction)
    try:
        personagens_usuario: List[Personagem] = listar_personagens_uc.executar(
            usuario_id=user_id, servidor_id=server_id
        )
        for p in personagens_usuario:
            if p.nome.lower() == nome_personagem.lower():
                if apenas_ativos and p.status != StatusPersonagem.ATIVO:
                    continue
                return p
        raise PersonagemNaoEncontradoError(nome_personagem)
    except PersonagemNaoEncontradoError:
        raise
    except Exception as e:
        print(f"Erro inesperado ao buscar personagem '{nome_personagem}' para user {user_id}: {e}")
        traceback.print_exc()
        raise CogUtilsError(f"Ocorreu um erro ao buscar o personagem '{nome_personagem}'.") from e

async def buscar_personagem_por_nome_para_usuario(
    interaction: Interaction, # Necessário para obter server_id
    nome_personagem: str,
    usuario_alvo_id: int,
    repo_personagens: RepositorioPersonagensSQLAlchemy, # Dependência do Repositório
    apenas_ativos: bool = False
) -> Personagem:
    """
    Busca um personagem específico de um USUÁRIO ALVO pelo nome.
    Raises: ComandoForaDeServidorError, PersonagemNaoEncontradoError, CogUtilsError.
    """
    # Reutiliza obter_contexto_comando apenas para pegar o server_id e validar
    _, server_id = await obter_contexto_comando(interaction)
    try:
        # Usa o usuario_alvo_id fornecido na busca
        personagens_usuario: List[Personagem] = repo_personagens.listar_por_usuario(
            usuario_alvo_id, server_id
        )
        for p in personagens_usuario:
            if p.nome.lower() == nome_personagem.lower():
                if apenas_ativos and p.status != StatusPersonagem.ATIVO:
                    continue
                return p
        raise PersonagemNaoEncontradoError(nome_personagem, f"Personagem '{nome_personagem}' não encontrado para o usuário ID {usuario_alvo_id}.")
    except PersonagemNaoEncontradoError:
        raise
    except Exception as e:
        print(f"Erro inesperado ao buscar personagem '{nome_personagem}' para user {usuario_alvo_id}: {e}")
        traceback.print_exc()
        raise CogUtilsError(f"Ocorreu um erro ao buscar o personagem '{nome_personagem}' para o usuário especificado.") from e

# --- Funções de Verificação de Permissão ---

async def verificar_permissoes(
    member: Member,
    repo_config_servidor: RepositorioConfiguracaoServidor,
    tipo_permissao: str,
    personagem_alvo: Optional[Personagem] = None,
    permitir_proprietario: bool = True
) -> bool:
    """
    Verifica se um membro tem permissão para uma ação específica (Admin, Cargo, Dono).
    Returns: True se permitido, False caso contrário.
    Raises: ComandoForaDeServidorError.
    """
    if not member.guild:
        raise ComandoForaDeServidorError("Verificação de permissões só pode ocorrer em um servidor.")
    server_id = member.guild.id
    if member.guild_permissions.administrator:
        return True
    chave_config = f"cargos_{tipo_permissao}_ids"
    try:
        cargos_permitidos_ids = repo_config_servidor.obter_valor(server_id, chave_config, default=[])
        if any(role.id in cargos_permitidos_ids for role in member.roles):
            return True
    except Exception as e:
        print(f"Erro ao buscar cargos configurados para '{tipo_permissao}' no servidor {server_id}: {e}")
    if permitir_proprietario and personagem_alvo and personagem_alvo.usuario_id == member.id:
        return True
    return False

# --- Funções de Autocomplete ---

async def autocomplete_character(interaction: Interaction, current: str, repo_personagens: RepositorioPersonagensSQLAlchemy) -> List[app_commands.Choice[str]]:
    """Autocompleta com personagens do usuário da interação (incluindo aposentados)."""
    if not interaction.guild_id: return []
    user_id = interaction.user.id
    server_id = interaction.guild_id
    try:
        personagens: List[Personagem] = repo_personagens.listar_por_usuario(user_id, server_id)
        choices = [
            app_commands.Choice(name=f"{p.nome}{' (Aposentado)' if p.status == StatusPersonagem.APOSENTADO else ''}", value=p.nome)
            for p in personagens
            if current.lower() in p.nome.lower()
        ]
        choices.sort(key=lambda c: '(Aposentado)' in c.name)
        return choices[:25]
    except Exception as e:
        print(f"Erro no autocomplete_character (cog_utils): {e}")
        return []

async def autocomplete_active_character(interaction: Interaction, current: str, repo_personagens: RepositorioPersonagensSQLAlchemy) -> List[app_commands.Choice[str]]:
    """Autocompleta apenas com personagens ATIVOS do usuário da interação."""
    if not interaction.guild_id: return []
    user_id = interaction.user.id
    server_id = interaction.guild_id
    try:
        personagens: List[Personagem] = repo_personagens.listar_por_usuario(user_id, server_id)
        choices = [
            app_commands.Choice(name=p.nome, value=p.nome)
            for p in personagens
            if p.status == StatusPersonagem.ATIVO and current.lower() in p.nome.lower()
        ]
        return choices[:25]
    except Exception as e:
        print(f"Erro no autocomplete_active_character (cog_utils): {e}")
        return []

async def autocomplete_character_for_user(interaction: Interaction, current: str, repo_personagens: RepositorioPersonagensSQLAlchemy) -> list[app_commands.Choice[str]]:
    """Autocompleta com personagens de um usuário específico (obtido das opções do comando)."""
    if not interaction.guild_id: return []
    target_user_id: Optional[int] = None
    if interaction.data and 'options' in interaction.data:
        options = interaction.data.get('options', [])
        if options and options[0].get('type') == discord.AppCommandOptionType.subcommand.value:
            options = options[0].get('options', [])
        for option in options:
            if option.get('name') == 'usuario' and option.get('type') == discord.AppCommandOptionType.user.value:
                try:
                    target_user_id = int(option['value'])
                except (ValueError, TypeError):
                    print(f"Autocomplete Admin: Falha ao processar user_id da opção: {option.get('value')}")
                break
    if target_user_id is None and interaction.namespace and hasattr(interaction.namespace, 'usuario') and hasattr(interaction.namespace.usuario, 'id'):
         try:
             target_user_id = int(interaction.namespace.usuario.id)
         except (ValueError, TypeError):
             print("Autocomplete Admin: Falha ao converter interaction.namespace.usuario.id para int.")
             target_user_id = None
    if target_user_id is None:
         print("Autocomplete Admin: Falha final ao determinar o ID do usuário alvo.")
         return []
    server_id = interaction.guild_id
    try:
        personagens: List[Personagem] = repo_personagens.listar_por_usuario(target_user_id, server_id)
        choices = [
            app_commands.Choice(name=f"{p.nome}{' (Aposentado)' if p.status == StatusPersonagem.APOSENTADO else ''}", value=p.nome)
            for p in personagens
            if current.lower() in p.nome.lower()
        ]
        choices.sort(key=lambda c: '(Aposentado)' in c.name)
        return choices[:25]
    except Exception as e:
        print(f"Erro no autocomplete_character_for_user (cog_utils): {e}")
        return []

async def autocomplete_item(interaction: Interaction, current: str, repo_itens: RepositorioItensSQLAlchemy) -> list[app_commands.Choice[str]]:
    """Autocompleta com nomes de itens mestres."""
    try:
        itens: List[Item] = repo_itens.listar_todos()
        choices = [
            app_commands.Choice(name=i.nome, value=i.nome)
            for i in itens if current.lower() in i.nome.lower()
        ]
        return choices[:25]
    except Exception as e:
        print(f"Erro no autocomplete_item (cog_utils): {e}")
        return []

# --- Decoradores (a serem adicionados) ---

# --- Funções de Embed (a serem adicionadas) ---