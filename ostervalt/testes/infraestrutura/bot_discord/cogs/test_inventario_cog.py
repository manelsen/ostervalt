import pytest
from unittest.mock import AsyncMock, MagicMock
from ostervalt.infraestrutura.bot_discord.cogs.inventario_cog import InventarioCog

@pytest.mark.asyncio
async def test_ver_inventario_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_listar = AsyncMock()
    caso_uso_listar.executar.return_value = ["item1", "item2"]
    cog = InventarioCog(caso_uso_listar, MagicMock(), MagicMock())
    await cog.ver_inventario(interaction)
    assert interaction.response.send_message.called

@pytest.mark.asyncio
async def test_adicionar_item_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_adicionar = AsyncMock()
    caso_uso_adicionar.executar.return_value = MagicMock()
    cog = InventarioCog(MagicMock(), caso_uso_adicionar, MagicMock())
    await cog.adicionar_item(interaction, personagem_id=1, item_id=2, quantidade=1)
    assert interaction.response.send_message.called

@pytest.mark.asyncio
async def test_remover_item_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_remover = AsyncMock()
    caso_uso_remover.executar.return_value = True
    cog = InventarioCog(MagicMock(), MagicMock(), caso_uso_remover)
    await cog.remover_item(interaction, item_id=2, quantidade=1)
    assert interaction.response.send_message.called