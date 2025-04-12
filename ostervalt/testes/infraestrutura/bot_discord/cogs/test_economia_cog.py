import pytest
from unittest.mock import AsyncMock, MagicMock
from ostervalt.infraestrutura.bot_discord.cogs.economia_cog import EconomiaCog

@pytest.mark.asyncio
async def test_trabalhar_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_trabalho = AsyncMock()
    caso_uso_trabalho.executar.return_value = MagicMock()
    cog = EconomiaCog(caso_uso_trabalho, MagicMock())
    await cog.trabalhar(interaction)
    assert interaction.response.send_message.called

@pytest.mark.asyncio
async def test_trabalhar_falha():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_trabalho = AsyncMock()
    caso_uso_trabalho.executar.side_effect = Exception("Erro")
    cog = EconomiaCog(caso_uso_trabalho, MagicMock())
    await cog.trabalhar(interaction)
    assert interaction.response.send_message.called

@pytest.mark.asyncio
async def test_crime_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_crime = AsyncMock()
    caso_uso_crime.executar.return_value = MagicMock()
    cog = EconomiaCog(MagicMock(), caso_uso_crime)
    await cog.crime(interaction)
    assert interaction.response.send_message.called

@pytest.mark.asyncio
async def test_crime_falha():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_crime = AsyncMock()
    caso_uso_crime.executar.side_effect = Exception("Erro")
    cog = EconomiaCog(MagicMock(), caso_uso_crime)
    await cog.crime(interaction)
    assert interaction.response.send_message.called