import pytest
from unittest.mock import MagicMock, patch
import datetime
from ostervalt.nucleo.casos_de_uso.realizar_trabalho import RealizarTrabalho
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.nucleo.casos_de_uso.dtos import ResultadoTrabalhoDTO

def test_realizar_trabalho_sucesso():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    
    # Configurar mocks
    personagem = Personagem(
        "Teste", # nome
        1,       # id
        5,       # nivel
        100,     # dinheiro
        datetime.datetime.now() - datetime.timedelta(hours=2), # ultimo_tempo_trabalho
    )
    repo_mock.obter_por_id.return_value = personagem
    config_mock.obter.side_effect = lambda key: {
        "limites": {"intervalo_trabalhar": 3600},  # 1 hora
        "tiers": {"tier1": {"nivel_min": 1, "nivel_max": 10, "recompensa": 50}},
        "messages": {"trabalho": ["Você trabalhou bem!"]}
    }.get(key)
    
    caso_uso = RealizarTrabalho(repo_mock, config_mock)
    
    # Act
    tempo_atual = datetime.datetime.now() # Obter timestamp real fora do patch
    resultado = caso_uso.executar(1, tempo_atual=tempo_atual) # Passar tempo_atual como argumento
    
    # Assert
    assert isinstance(resultado, ResultadoTrabalhoDTO)
    assert resultado.personagem.dinheiro == 150  # 100 + 50 de recompensa
    assert "Você trabalhou bem!" in resultado.mensagem
    assert resultado.recompensa == 50
    repo_mock.atualizar.assert_called_once_with(personagem)

def test_realizar_trabalho_personagem_nao_encontrado():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    repo_mock.obter_por_id.return_value = None
    caso_uso = RealizarTrabalho(repo_mock, config_mock)
    
    # Act & Assert
    with pytest.raises(ValueError, match="Personagem com ID 1 não encontrado"):
        caso_uso.executar(1)

def test_realizar_trabalho_cooldown_nao_terminou():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    
    personagem = Personagem(
        "Teste", # nome
        1,       # id
        5,       # nivel
        100,     # dinheiro
        datetime.datetime.now() - datetime.timedelta(minutes=30), # ultimo_tempo_trabalho
    )
    repo_mock.obter_por_id.return_value = personagem
    config_mock.obter.return_value = {"intervalo_trabalhar": 3600}  # 1 hora
    
    caso_uso = RealizarTrabalho(repo_mock, config_mock)
    
    # Act & Assert
    tempo_atual = datetime.datetime(2025, 1, 1, 12, 0, 0) # Usar um datetime real e consistente
    with pytest.raises(ValueError, match="Ação de trabalho está em cooldown"):
        caso_uso.executar(1, tempo_atual=tempo_atual) # Passar tempo_atual como argumento

def test_realizar_trabalho_configuracao_faltando():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    
    personagem = Personagem(
        "Teste", # nome
        1,       # id
        5,       # nivel
        100,     # dinheiro
        datetime.datetime.now() - datetime.timedelta(hours=2), # ultimo_tempo_trabalho
    )
    repo_mock.obter_por_id.return_value = personagem
    config_mock.obter.side_effect = KeyError("Configuração não encontrada")
    
    caso_uso = RealizarTrabalho(repo_mock, config_mock)
    
    # Act & Assert
    with pytest.raises(KeyError, match="Configuração não encontrada"):
        caso_uso.executar(1)