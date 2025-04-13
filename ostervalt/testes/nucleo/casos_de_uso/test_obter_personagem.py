import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.obter_personagem import ObterPersonagem
from ostervalt.nucleo.entidades.personagem import Personagem # Embora não usemos diretamente, é bom ter como referência

def test_obter_personagem_sucesso():
    # Arrange
    repo_mock = MagicMock()
    personagem_mock = MagicMock(spec=Personagem) # Mock com a especificação da entidade
    personagem_mock.id = 1
    personagem_mock.nome = "Teste"
    repo_mock.obter_por_id.return_value = personagem_mock
    caso_uso = ObterPersonagem(repo_mock)
    personagem_id_teste = 1

    # Act
    personagem_obtido = caso_uso.executar(personagem_id_teste)

    # Assert
    assert personagem_obtido is personagem_mock
    repo_mock.obter_por_id.assert_called_once_with(personagem_id_teste)

def test_obter_personagem_nao_encontrado():
    # Arrange
    repo_mock = MagicMock()
    repo_mock.obter_por_id.return_value = None # Simula personagem não encontrado
    caso_uso = ObterPersonagem(repo_mock)
    personagem_id_teste = 999

    # Act
    personagem_obtido = caso_uso.executar(personagem_id_teste)

    # Assert
    assert personagem_obtido is None
    repo_mock.obter_por_id.assert_called_once_with(personagem_id_teste)

def test_obter_personagem_erro_repositorio():
    # Arrange
    repo_mock = MagicMock()
    erro_esperado = Exception("Erro simulado no banco de dados")
    repo_mock.obter_por_id.side_effect = erro_esperado # Simula exceção no repositório
    caso_uso = ObterPersonagem(repo_mock)
    personagem_id_teste = 1

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        caso_uso.executar(personagem_id_teste)
    assert excinfo.value is erro_esperado # Verifica se a exceção original foi propagada
    repo_mock.obter_por_id.assert_called_once_with(personagem_id_teste)