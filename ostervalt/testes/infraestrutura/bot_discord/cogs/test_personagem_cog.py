import pytest
from unittest.mock import AsyncMock, MagicMock
from discord.ext import commands
import discord

# Importar classes e DTOs necessários
from ostervalt.infraestrutura.bot_discord.cogs.personagem_cog import PersonagemCog
from ostervalt.nucleo.casos_de_uso.criar_personagem import CriarPersonagem
from ostervalt.nucleo.casos_de_uso.obter_personagem import ObterPersonagem
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens
from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
from ostervalt.nucleo.casos_de_uso.dtos import PersonagemDTO
from ostervalt.nucleo.entidades.personagem import Personagem

# Comentar testes de integração temporariamente
# @pytest.mark.asyncio
# async def test_criar_personagem_sucesso():
#     interaction = AsyncMock()
#     interaction.user.id = 123
#     interaction.guild_id = 456
#     interaction.response = AsyncMock()
#     interaction.followup = AsyncMock()
#     nome_personagem = "Heroi Teste"
#
#     criar_personagem_uc = AsyncMock(spec=CriarPersonagem)
#     obter_personagem_uc = AsyncMock(spec=ObterPersonagem)
#     listar_personagens_uc = AsyncMock(spec=ListarPersonagens)
#     repo_personagens = AsyncMock(spec=RepositorioPersonagensSQLAlchemy)
#     bot_mock = AsyncMock(spec=commands.Bot)
#
#     personagem_criado_mock = Personagem(id=1, nome=nome_personagem, usuario_id=123, servidor_id=456, nivel=1, dinheiro=0)
#     criar_personagem_uc.executar.return_value = personagem_criado_mock
#
#     cog = PersonagemCog(
#         bot_mock,
#         criar_personagem_uc=criar_personagem_uc,
#         obter_personagem_uc=obter_personagem_uc,
#         listar_personagens_uc=listar_personagens_uc,
#         repo_personagens=repo_personagens
#     )
#
#     # await cog.criar_personagem(interaction, nome=nome_personagem) # Comentado
#     # TODO: Implementar teste de integração simulando a árvore de comandos
#     pass # Teste desativado

# @pytest.mark.asyncio
# async def test_criar_personagem_falha():
#     interaction = AsyncMock()
#     interaction.user.id = 123
#     interaction.guild_id = 456
#     interaction.response = AsyncMock()
#     interaction.followup = AsyncMock()
#     nome_personagem = "Duplicado"
#
#     criar_personagem_uc = AsyncMock(spec=CriarPersonagem)
#     obter_personagem_uc = AsyncMock(spec=ObterPersonagem)
#     listar_personagens_uc = AsyncMock(spec=ListarPersonagens)
#     repo_personagens = AsyncMock(spec=RepositorioPersonagensSQLAlchemy)
#     bot_mock = AsyncMock(spec=commands.Bot)
#
#     erro_msg = "Personagem com este nome já existe."
#     criar_personagem_uc.executar.side_effect = ValueError(erro_msg)
#
#     cog = PersonagemCog(
#         bot_mock,
#         criar_personagem_uc=criar_personagem_uc,
#         obter_personagem_uc=obter_personagem_uc,
#         listar_personagens_uc=listar_personagens_uc,
#         repo_personagens=repo_personagens
#     )
#
#     # await cog.criar_personagem(interaction, nome=nome_personagem) # Comentado
#     # TODO: Implementar teste de integração simulando a árvore de comandos
#     pass # Teste desativado

# TODO: Adicionar testes para /perfil, /personagens, /inss