import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from ostervalt.infraestrutura.bot_discord.cogs.personagem_cog import PersonagemCog
from discord.ext import commands # Import necessário
from ostervalt.nucleo.casos_de_uso.criar_personagem import CriarPersonagem         # Import necessário
from ostervalt.nucleo.casos_de_uso.obter_personagem import ObterPersonagem         # Import necessário
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens       # Import necessário

@pytest.mark.asyncio
async def test_criar_personagem_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_criar = AsyncMock()
    caso_uso_criar = AsyncMock(spec=CriarPersonagem)
    caso_uso_criar.executar.return_value = MagicMock(nome="Teste", usuario_id=123, servidor_id=1)
    caso_uso_criar = AsyncMock(spec=CriarPersonagem)
    caso_uso_criar.executar.return_value = MagicMock(nome="Teste", usuario_id=123, servidor_id=1)
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = PersonagemCog(bot_mock, criar_personagem_uc=caso_uso_criar, obter_personagem_uc=MagicMock(), listar_personagens_uc=MagicMock()) # bot como primeiro argumento posicional
    await cog.criar_personagem.callback(cog, interaction, nome="Teste") # Usar callback
    assert interaction.response.send_message.called

@pytest.mark.asyncio
async def test_criar_personagem_falha():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_criar = AsyncMock()
    caso_uso_criar = AsyncMock(spec=CriarPersonagem)
    caso_uso_criar.executar.side_effect = Exception("Erro")
    caso_uso_criar = AsyncMock(spec=CriarPersonagem)
    caso_uso_criar.executar.side_effect = Exception("Erro")
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = PersonagemCog(bot_mock, criar_personagem_uc=caso_uso_criar, obter_personagem_uc=MagicMock(), listar_personagens_uc=MagicMock()) # bot como primeiro argumento posicional
    await cog.criar_personagem.callback(cog, interaction, nome="Teste") # Usar callback
    assert interaction.response.send_message.called