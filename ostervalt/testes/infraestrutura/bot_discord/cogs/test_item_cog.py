import pytest
from unittest.mock import AsyncMock, MagicMock
from ostervalt.infraestrutura.bot_discord.cogs.item_cog import ItemCog

@pytest.mark.asyncio
async def test_ver_item_info_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_obter_item = AsyncMock()
    caso_uso_obter_item.executar.return_value = MagicMock()
    cog = ItemCog(caso_uso_obter_item, MagicMock())
    await cog.ver_item_info(interaction, item_id=1)
    assert interaction.response.send_message.called

@pytest.mark.asyncio
async def test_ver_loja_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_listar_itens = AsyncMock()
    caso_uso_listar_itens.executar.return_value = ["item1", "item2"]
    cog = ItemCog(MagicMock(), caso_uso_listar_itens)
    await cog.ver_loja(interaction)
    assert interaction.response.send_message.called