import pytest
from unittest.mock import MagicMock, patch
import datetime
from ostervalt.nucleo.casos_de_uso.cometer_crime import CometerCrime
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.nucleo.casos_de_uso.dtos import ResultadoCrimeDTO

def test_cometer_crime_sucesso():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    
    # Configurar mocks
    personagem = Personagem(
        "Teste", # nome
        1,       # id
        5,       # nivel
        100,     # dinheiro
        datetime.datetime.now() - datetime.timedelta(hours=2), # ultimo_tempo_crime
    )
    repo_mock.obter_por_id.return_value = personagem
    config_mock.obter.side_effect = lambda key: {
        "limites": {"intervalo_crime": 3600},  # 1 hora
        "probabilidades": {"crime": 100},  # 100% de sucesso
        "messages": {"crime": ["Você cometeu um crime!"]}
    }.get(key)
    
    caso_uso = CometerCrime(repo_mock, config_mock)
    
    # Act
    tempo_atual = datetime.datetime.now() # Obter timestamp real fora do patch
    resultado = caso_uso.executar(1, tempo_atual=tempo_atual) # Passar tempo_atual como argumento
    
    # Assert
    assert isinstance(resultado, ResultadoCrimeDTO)
    assert resultado.sucesso is True
    assert resultado.personagem.dinheiro > 100  # Deve ter ganhado dinheiro
    assert "Você cometeu um crime!" in resultado.mensagem
    repo_mock.atualizar.assert_called_once_with(personagem)

def test_cometer_crime_falha():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    
    personagem = Personagem(
        "Teste", # nome
        1,       # id
        5,       # nivel
        100,     # dinheiro
        datetime.datetime.now() - datetime.timedelta(hours=2), # ultimo_tempo_crime
    )
    repo_mock.obter_por_id.return_value = personagem
    config_mock.obter.side_effect = lambda key: {
        "limites": {"intervalo_crime": 3600},
        "probabilidades": {"crime": 0},  # 0% de sucesso
        "messages": {"crime": ["Você foi pego!"]}
    }.get(key)
    
    caso_uso = CometerCrime(repo_mock, config_mock)
    
    # Act
    # Mockar executar_logica_crime para garantir falha
    with patch('ostervalt.nucleo.casos_de_uso.cometer_crime.executar_logica_crime') as mock_logica_crime:
        mock_logica_crime.return_value = (False, -100) # Forçar falha com perda de 100
        tempo_atual = datetime.datetime.now()
        resultado = caso_uso.executar(1, tempo_atual=tempo_atual) # Passar tempo_atual
    
    # Assert
    assert isinstance(resultado, ResultadoCrimeDTO)
    assert resultado.sucesso is False
    assert resultado.personagem.dinheiro < 100  # Deve ter perdido dinheiro
    assert "Você foi pego!" in resultado.mensagem
    repo_mock.atualizar.assert_called_once_with(personagem)

def test_cometer_crime_personagem_nao_encontrado():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    repo_mock.obter_por_id.return_value = None
    caso_uso = CometerCrime(repo_mock, config_mock)
    
    # Act & Assert
    with pytest.raises(ValueError, match="Personagem com ID 1 não encontrado"):
        caso_uso.executar(1)

def test_cometer_crime_cooldown_nao_terminou():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    
    personagem = Personagem(
        "Teste", # nome
        1,       # id
        5,       # nivel
        100,     # dinheiro
        datetime.datetime.now() - datetime.timedelta(minutes=30), # ultimo_tempo_crime
    )
    repo_mock.obter_por_id.return_value = personagem
    # Configurar o mock para retornar o dicionário correto para cada chave esperada
    def config_side_effect(key):
        if key == "limites":
            return {"intervalo_crime": 3600}
        elif key == "probabilidades":
             return {"crime": 0} # Necessário para evitar AttributeError posterior
        else:
            return {} # Retorna dicionário vazio para outras chaves
    config_mock.obter.side_effect = config_side_effect
    
    caso_uso = CometerCrime(repo_mock, config_mock)
    
    # Act & Assert
    # Definir um tempo atual fixo para o teste
    tempo_atual_teste = datetime.datetime(2025, 1, 1, 12, 0, 0)
    # Garantir que ultimo_tempo_crime seja relativo a tempo_atual_teste
    personagem.ultimo_tempo_crime = tempo_atual_teste - datetime.timedelta(minutes=30)
    with pytest.raises(ValueError, match="Ação de crime está em cooldown"):
        caso_uso.executar(1, tempo_atual=tempo_atual_teste) # Passar tempo_atual fixo

def test_cometer_crime_configuracao_faltando():
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    
    personagem = Personagem(
        "Teste", # nome
        1,       # id
        5,       # nivel
        100,     # dinheiro
        datetime.datetime.now() - datetime.timedelta(hours=2), # ultimo_tempo_crime
    )
    repo_mock.obter_por_id.return_value = personagem
    config_mock.obter.side_effect = KeyError("Configuração não encontrada")
    
    caso_uso = CometerCrime(repo_mock, config_mock)
    
    # Act & Assert
    with pytest.raises(KeyError, match="Configuração não encontrada"):
        caso_uso.executar(1)