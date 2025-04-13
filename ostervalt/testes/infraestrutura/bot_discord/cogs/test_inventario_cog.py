import pytest
from unittest.mock import AsyncMock, MagicMock
from ostervalt.infraestrutura.bot_discord.cogs.inventario_cog import InventarioCog
from discord.ext import commands # Import necessário
from ostervalt.nucleo.casos_de_uso.listar_inventario import ListarInventario     # Import necessário
from ostervalt.nucleo.casos_de_uso.adicionar_item_inventario import AdicionarItemInventario # Import necessário
from ostervalt.nucleo.casos_de_uso.remover_item_inventario import RemoverItemInventario # Import necessário
from ostervalt.nucleo.casos_de_uso.dtos import InventarioDTO, ItemInventarioDTO # Importar DTOs

@pytest.mark.asyncio
async def test_ver_inventario_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_listar = AsyncMock(spec=ListarInventario)
    # Corrigir valor de retorno para ser um InventarioDTO
    item1_inv_dto = ItemInventarioDTO(item_id=1, nome_item="Poção Pequena", quantidade=3, descricao_item="Cura um pouco.")
    item2_inv_dto = ItemInventarioDTO(item_id=5, nome_item="Adaga Enferrujada", quantidade=1, descricao_item="Melhor que nada.")
    resultado_listar_mock = InventarioDTO(nome_personagem="Teste", itens=[item1_inv_dto, item2_inv_dto])
    caso_uso_listar.executar.return_value = resultado_listar_mock
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = InventarioCog(bot_mock, listar_inventario_uc=caso_uso_listar, adicionar_item_uc=MagicMock(), remover_item_uc=MagicMock()) # bot como primeiro argumento posicional
    await cog.ver_inventario.callback(cog, interaction) # Usar o nome do método 'ver_inventario'
    assert interaction.followup.send.called # Verificar followup.send pois defer foi usado

@pytest.mark.asyncio
async def test_adicionar_item_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_adicionar = AsyncMock(spec=AdicionarItemInventario)
    caso_uso_adicionar.executar.return_value = MagicMock()
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = InventarioCog(bot_mock, listar_inventario_uc=MagicMock(), adicionar_item_uc=caso_uso_adicionar, remover_item_uc=MagicMock()) # bot como primeiro argumento posicional
    await cog.adicionar_item.callback(cog, interaction, personagem_id=1, item_id=2, quantidade=1) # Usar callback
    assert interaction.followup.send.called # Verificar followup.send pois defer foi usado

@pytest.mark.asyncio
async def test_remover_item_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_remover = AsyncMock(spec=RemoverItemInventario)
    caso_uso_remover.executar.return_value = True
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = InventarioCog(bot_mock, listar_inventario_uc=MagicMock(), adicionar_item_uc=MagicMock(), remover_item_uc=caso_uso_remover) # bot como primeiro argumento posicional
    await cog.remover_item.callback(cog, interaction, item_id=2, quantidade=1) # Usar callback
    assert interaction.followup.send.called # Verificar followup.send pois defer foi usado