import pytest
from unittest.mock import AsyncMock, MagicMock
from discord.ext import commands # Import necessário
from ostervalt.infraestrutura.bot_discord.cogs.economia_cog import EconomiaCog
from ostervalt.nucleo.casos_de_uso.realizar_trabalho import RealizarTrabalho # Import necessário
from ostervalt.nucleo.casos_de_uso.cometer_crime import CometerCrime
from ostervalt.nucleo.casos_de_uso.obter_personagem import ObterPersonagem # Adicionado
from ostervalt.nucleo.casos_de_uso.dtos import ResultadoTrabalhoDTO, ResultadoCrimeDTO, PersonagemDTO # Adicionado PersonagemDTO
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
    obter_personagem_uc = AsyncMock(spec=ObterPersonagem) # Mock adicionado
    bot_mock = AsyncMock(spec=commands.Bot)
    cog = EconomiaCog(
        bot_mock,
        realizar_trabalho_uc=caso_uso_trabalho,
        cometer_crime_uc=caso_uso_crime,
        obter_personagem_uc=obter_personagem_uc # Passando o novo mock
    )
    await cog.trabalhar.callback(cog, interaction)
    interaction.response.defer.assert_called_once_with(ephemeral=True)
    interaction.followup.send.assert_called_once() # Verifica se foi chamado
    # Poderia verificar o embed aqui se necessário
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
    obter_personagem_uc = AsyncMock(spec=ObterPersonagem) # Mock adicionado
    bot_mock = AsyncMock(spec=commands.Bot)
    cog = EconomiaCog(
        bot_mock,
        realizar_trabalho_uc=caso_uso_trabalho,
        cometer_crime_uc=caso_uso_crime,
        obter_personagem_uc=obter_personagem_uc # Passando o novo mock
    )
    await cog.trabalhar.callback(cog, interaction)
    interaction.response.defer.assert_called_once_with(ephemeral=True)
    interaction.followup.send.assert_called_once()
    args, kwargs = interaction.followup.send.call_args
    assert "Ocorreu um erro ao tentar trabalhar" in args[0]
    assert kwargs["ephemeral"] == True
@pytest.mark.asyncio
async def test_crime_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    character_name = "Criminoso Joe"
    personagem_id_mock = 456

    # Mocks dos casos de uso
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho)
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    obter_personagem_uc = AsyncMock(spec=ObterPersonagem)
    bot_mock = AsyncMock(spec=commands.Bot)

    # Configurar retornos dos mocks
    personagem_dto_mock = PersonagemDTO(id=personagem_id_mock, nome=character_name, nivel=1, dinheiro=50) # ID é importante
    obter_personagem_uc.executar.return_value = personagem_dto_mock

    mensagem_esperada = f"Você tentou cometer um crime...\nSucesso! Você ganhou 150 moedas.\nSaldo atual: 200 moedas."
    resultado_crime_mock = ResultadoCrimeDTO(
        personagem=MagicMock(), # O personagem dentro do DTO não é usado diretamente na resposta do cog
        mensagem=mensagem_esperada,
        sucesso=True,
        resultado_financeiro=150
    )
    caso_uso_crime.executar.return_value = resultado_crime_mock

    # Instanciar Cog
    cog = EconomiaCog(
        bot_mock,
        realizar_trabalho_uc=caso_uso_trabalho,
        cometer_crime_uc=caso_uso_crime,
        obter_personagem_uc=obter_personagem_uc
    )

    # Executar o comando
    await cog.crime.callback(cog, interaction, character=character_name)

    # Verificar chamadas e resposta
    interaction.response.defer.assert_called_once_with() # Sem ephemeral
    obter_personagem_uc.executar.assert_called_once_with(discord_id=123, nome_personagem=character_name)
    caso_uso_crime.executar.assert_called_once_with(personagem_id=personagem_id_mock)
    interaction.followup.send.assert_called_once_with(mensagem_esperada)
@pytest.mark.asyncio
async def test_crime_falha_pego():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    character_name = "Azarado Bob"
    personagem_id_mock = 789

    # Mocks
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho)
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    obter_personagem_uc = AsyncMock(spec=ObterPersonagem)
    bot_mock = AsyncMock(spec=commands.Bot)

    # Configurar retornos
    personagem_dto_mock = PersonagemDTO(id=personagem_id_mock, nome=character_name, nivel=1, dinheiro=50)
    obter_personagem_uc.executar.return_value = personagem_dto_mock

    mensagem_esperada = f"Você tentou cometer um crime...\nVocê foi pego! Perdeu 100 moedas.\nSaldo atual: -50 moedas." # Exemplo
    resultado_crime_mock = ResultadoCrimeDTO(
        personagem=MagicMock(),
        mensagem=mensagem_esperada,
        sucesso=False,
        resultado_financeiro=-100
    )
    caso_uso_crime.executar.return_value = resultado_crime_mock

    # Instanciar Cog
    cog = EconomiaCog(
        bot_mock,
        realizar_trabalho_uc=caso_uso_trabalho,
        cometer_crime_uc=caso_uso_crime,
        obter_personagem_uc=obter_personagem_uc
    )

    # Executar
    await cog.crime.callback(cog, interaction, character=character_name)

    # Verificar
    interaction.response.defer.assert_called_once_with()
    obter_personagem_uc.executar.assert_called_once_with(discord_id=123, nome_personagem=character_name)
    caso_uso_crime.executar.assert_called_once_with(personagem_id=personagem_id_mock)
    interaction.followup.send.assert_called_once_with(mensagem_esperada)

@pytest.mark.asyncio
async def test_crime_personagem_nao_encontrado():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    character_name = "Fantasma"

    # Mocks
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho)
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    obter_personagem_uc = AsyncMock(spec=ObterPersonagem)
    bot_mock = AsyncMock(spec=commands.Bot)

    # Configurar retorno (personagem não encontrado)
    obter_personagem_uc.executar.return_value = None

    # Instanciar Cog
    cog = EconomiaCog(
        bot_mock,
        realizar_trabalho_uc=caso_uso_trabalho,
        cometer_crime_uc=caso_uso_crime,
        obter_personagem_uc=obter_personagem_uc
    )

    # Executar
    await cog.crime.callback(cog, interaction, character=character_name)

    # Verificar
    interaction.response.defer.assert_called_once_with()
    obter_personagem_uc.executar.assert_called_once_with(discord_id=123, nome_personagem=character_name)
    caso_uso_crime.executar.assert_not_called() # Não deve chamar o UC de crime
    interaction.followup.send.assert_called_once_with(f"❌ Personagem '{character_name}' não encontrado para seu usuário.", ephemeral=True)

@pytest.mark.asyncio
async def test_crime_cooldown():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    character_name = "Impaciente Carl"
    personagem_id_mock = 101

    # Mocks
    caso_uso_trabalho = AsyncMock(spec=RealizarTrabalho)
    caso_uso_crime = AsyncMock(spec=CometerCrime)
    obter_personagem_uc = AsyncMock(spec=ObterPersonagem)
    bot_mock = AsyncMock(spec=commands.Bot)

    # Configurar retornos
    personagem_dto_mock = PersonagemDTO(id=personagem_id_mock, nome=character_name, nivel=1, dinheiro=50)
    obter_personagem_uc.executar.return_value = personagem_dto_mock

    # Simular erro de cooldown (ValueError)
    mensagem_erro_cooldown = "Ação de crime está em cooldown. Tempo restante: 0:10:00."
    caso_uso_crime.executar.side_effect = ValueError(mensagem_erro_cooldown)

    # Instanciar Cog
    cog = EconomiaCog(
        bot_mock,
        realizar_trabalho_uc=caso_uso_trabalho,
        cometer_crime_uc=caso_uso_crime,
        obter_personagem_uc=obter_personagem_uc
    )

    # Executar
    await cog.crime.callback(cog, interaction, character=character_name)

    # Verificar
    interaction.response.defer.assert_called_once_with()
    obter_personagem_uc.executar.assert_called_once_with(discord_id=123, nome_personagem=character_name)
    caso_uso_crime.executar.assert_called_once_with(personagem_id=personagem_id_mock)
    interaction.followup.send.assert_called_once_with(f"❌ {mensagem_erro_cooldown}", ephemeral=True)