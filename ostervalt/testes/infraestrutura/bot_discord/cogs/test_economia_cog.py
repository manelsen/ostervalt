import pytest
from unittest.mock import AsyncMock, MagicMock
from discord.ext import commands # Import necessário
from ostervalt.infraestrutura.bot_discord.cogs.economia_cog import EconomiaCog
from ostervalt.nucleo.casos_de_uso.realizar_trabalho import RealizarTrabalho # Import necessário
from ostervalt.nucleo.casos_de_uso.cometer_crime import CometerCrime       # Import necessário
from ostervalt.nucleo.casos_de_uso.dtos import ResultadoTrabalhoDTO, ResultadoCrimeDTO # Importar DTOs

@pytest.mark.asyncio
async def test_trabalhar_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho)
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho)
    # Retornar um DTO válido (apenas campos existentes)
    resultado_trabalho_mock = ResultadoTrabalhoDTO(
        personagem=MagicMock(), mensagem="Trabalhou!", recompensa=50
    )
    caso_uso_trabalho.executar.return_value = resultado_trabalho_mock
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = EconomiaCog(bot_mock, realizar_trabalho_uc=caso_uso_trabalho, cometer_crime_uc=caso_uso_crime) # bot como primeiro argumento posicional
    await cog.trabalhar.callback(cog, interaction) # Chamar o callback do comando
    # Verificar followup.send para a mensagem de erro
    assert interaction.followup.send.called

@pytest.mark.asyncio
async def test_trabalhar_falha():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho)
    caso_uso_trabalho.executar.side_effect = Exception("Erro")
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho)
    caso_uso_trabalho.executar.side_effect = Exception("Erro")
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = EconomiaCog(bot_mock, realizar_trabalho_uc=caso_uso_trabalho, cometer_crime_uc=caso_uso_crime) # bot como primeiro argumento posicional
    await cog.trabalhar.callback(cog, interaction) # Chamar o callback do comando
    # Verificar followup.send pois defer foi usado
    assert interaction.followup.send.called

@pytest.mark.asyncio
async def test_crime_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    # Retornar um DTO válido (apenas campos existentes)
    resultado_crime_mock = ResultadoCrimeDTO(
        personagem=MagicMock(), mensagem="Crime bem sucedido!", sucesso=True, resultado_financeiro=100
    )
    caso_uso_crime.executar.return_value = resultado_crime_mock
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    caso_uso_crime.executar.return_value = MagicMock()
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho) # Adicionado mock para o primeiro argumento
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = EconomiaCog(bot_mock, realizar_trabalho_uc=caso_uso_trabalho, cometer_crime_uc=caso_uso_crime) # bot como primeiro argumento posicional
    await cog.crime.callback(cog, interaction) # Chamar o callback do comando
    # Verificar followup.send pois defer foi usado
    assert interaction.followup.send.called

@pytest.mark.asyncio
async def test_crime_falha():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    caso_uso_crime.executar.side_effect = Exception("Erro")
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    caso_uso_crime.executar.side_effect = Exception("Erro")
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho) # Adicionado mock para o primeiro argumento
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = EconomiaCog(bot_mock, realizar_trabalho_uc=caso_uso_trabalho, cometer_crime_uc=caso_uso_crime) # bot como primeiro argumento posicional
    await cog.crime.callback(cog, interaction) # Chamar o callback do comando
    # Verificar followup.send para a mensagem de erro
    assert interaction.followup.send.called