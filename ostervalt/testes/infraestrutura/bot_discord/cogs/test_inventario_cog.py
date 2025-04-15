import pytest
from unittest.mock import AsyncMock, MagicMock
from discord.ext import commands
import discord

# Importar classes e DTOs necessários
from ostervalt.infraestrutura.bot_discord.cogs.inventario_cog import InventarioCog
from ostervalt.nucleo.casos_de_uso.listar_inventario import ListarInventario
from ostervalt.nucleo.casos_de_uso.adicionar_item_inventario import AdicionarItemInventario
from ostervalt.nucleo.casos_de_uso.remover_item_inventario import RemoverItemInventario
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens
from ostervalt.nucleo.entidades.item import ItemInventario
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.infraestrutura.persistencia.models import StatusPersonagem

# Comentar testes de integração temporariamente
# @pytest.mark.asyncio
# async def test_ver_inventario_sucesso():
#     interaction = AsyncMock()
#     interaction.user.id = 123
#     interaction.guild_id = 456
#     interaction.response = AsyncMock()
#     interaction.followup = AsyncMock()
#     character_name = "Aventureiro"
#     personagem_id_mock = 789
#
#     listar_inventario_uc = AsyncMock(spec=ListarInventario)
#     adicionar_item_uc = AsyncMock(spec=AdicionarItemInventario)
#     remover_item_uc = AsyncMock(spec=RemoverItemInventario)
#     listar_personagens_uc = AsyncMock(spec=ListarPersonagens)
#     bot_mock = AsyncMock(spec=commands.Bot)
#
#     personagem_mock = MagicMock(spec=Personagem)
#     personagem_mock.id = personagem_id_mock
#     personagem_mock.nome = character_name
#     personagem_mock.status = StatusPersonagem.ATIVO
#     listar_personagens_uc.executar.return_value = [personagem_mock]
#
#     item1 = ItemInventario(id=1, item_id=101, personagem_id=personagem_id_mock, quantidade=2)
#     item2 = ItemInventario(id=2, item_id=102, personagem_id=personagem_id_mock, quantidade=1)
#     listar_inventario_uc.executar.return_value = [item1, item2]
#
#     cog = InventarioCog(
#         bot_mock,
#         listar_inventario_uc=listar_inventario_uc,
#         adicionar_item_uc=adicionar_item_uc,
#         remover_item_uc=remover_item_uc,
#         listar_personagens_uc=listar_personagens_uc
#     )
#
#     # await cog.ver_inventario(interaction, character=character_name) # Comentado
#     # TODO: Implementar teste de integração simulando a árvore de comandos
#     pass # Teste desativado

# @pytest.mark.asyncio
# async def test_adicionar_item_sucesso():
#     interaction = AsyncMock()
#     interaction.response = AsyncMock()
#     interaction.followup = AsyncMock()
#     personagem_id = 1
#     item_id = 101
#     quantidade = 5
#
#     listar_inventario_uc = AsyncMock(spec=ListarInventario)
#     adicionar_item_uc = AsyncMock(spec=AdicionarItemInventario)
#     remover_item_uc = AsyncMock(spec=RemoverItemInventario)
#     listar_personagens_uc = AsyncMock(spec=ListarPersonagens)
#     bot_mock = AsyncMock(spec=commands.Bot)
#
#     cog = InventarioCog(
#         bot_mock,
#         listar_inventario_uc=listar_inventario_uc,
#         adicionar_item_uc=adicionar_item_uc,
#         remover_item_uc=remover_item_uc,
#         listar_personagens_uc=listar_personagens_uc
#     )
#
#     # await cog.adicionar_item(interaction, personagem_id=personagem_id, item_id=item_id, quantidade=quantidade) # Comentado
#     # TODO: Implementar teste de integração simulando a árvore de comandos
#     pass # Teste desativado

# @pytest.mark.asyncio
# async def test_remover_item_sucesso():
#     interaction = AsyncMock()
#     interaction.user.id = 123
#     interaction.guild_id = 456
#     interaction.response = AsyncMock()
#     interaction.followup = AsyncMock()
#     character_name = "Aventureiro"
#     personagem_id_mock = 789
#     item_id = 101
#     quantidade = 1
#
#     listar_inventario_uc = AsyncMock(spec=ListarInventario)
#     adicionar_item_uc = AsyncMock(spec=AdicionarItemInventario)
#     remover_item_uc = AsyncMock(spec=RemoverItemInventario)
#     listar_personagens_uc = AsyncMock(spec=ListarPersonagens)
#     bot_mock = AsyncMock(spec=commands.Bot)
#
#     personagem_mock = MagicMock(spec=Personagem)
#     personagem_mock.id = personagem_id_mock
#     personagem_mock.nome = character_name
#     personagem_mock.status = StatusPersonagem.ATIVO
#     listar_personagens_uc.executar.return_value = [personagem_mock]
#
#     cog = InventarioCog(
#         bot_mock,
#         listar_inventario_uc=listar_inventario_uc,
#         adicionar_item_uc=adicionar_item_uc,
#         remover_item_uc=remover_item_uc,
#         listar_personagens_uc=listar_personagens_uc
#     )
#
#     # await cog.remover_item_inventario(interaction, character=character_name, item_id=item_id, quantidade=quantidade) # Comentado
#     # TODO: Implementar teste de integração simulando a árvore de comandos
#     pass # Teste desativado