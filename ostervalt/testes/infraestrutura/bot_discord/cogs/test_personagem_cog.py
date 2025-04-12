import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from ostervalt.infraestrutura.bot_discord.cogs.personagem_cog import PersonagemCog

@pytest.mark.asyncio
async def test_criar_personagem_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_criar = AsyncMock()
    caso_uso_criar.executar.return_value = MagicMock(nome="Teste", usuario_id=123, servidor_id=1)
    cog = PersonagemCog(caso_uso_criar, MagicMock(), MagicMock())
    await cog.criar_personagem(interaction, nome="Teste")
    assert interaction.response.send_message.called

@pytest.mark.asyncio
async def test_criar_personagem_falha():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_criar = AsyncMock()
    caso_uso_criar.executar.side_effect = Exception("Erro")
    cog = PersonagemCog(caso_uso_criar, MagicMock(), MagicMock())
    await cog.criar_personagem(interaction, nome="Teste")
    assert interaction.response.send_message.called