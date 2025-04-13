import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem # Importar para spec do mock

def test_listar_personagens_sucesso():
    # Arrange
    repo_mock = MagicMock()
    personagem_mock_1 = MagicMock(spec=Personagem)
    personagem_mock_2 = MagicMock(spec=Personagem)
    lista_esperada = [personagem_mock_1, personagem_mock_2]
    repo_mock.listar_por_usuario.return_value = lista_esperada
    caso_uso = ListarPersonagens(repo_mock)
    usuario_id_teste = 123
    servidor_id_teste = 456

    # Act
    personagens_obtidos = caso_uso.executar(usuario_id_teste, servidor_id_teste)

    # Assert
    assert personagens_obtidos == lista_esperada
    repo_mock.listar_por_usuario.assert_called_once_with(usuario_id_teste, servidor_id_teste)

def test_listar_personagens_lista_vazia():
    # Arrange
    repo_mock = MagicMock()
    repo_mock.listar_por_usuario.return_value = [] # Simula nenhum personagem encontrado
    caso_uso = ListarPersonagens(repo_mock)
    usuario_id_teste = 123
    servidor_id_teste = 456

    # Act
    personagens_obtidos = caso_uso.executar(usuario_id_teste, servidor_id_teste)

    # Assert
    assert personagens_obtidos == []
    repo_mock.listar_por_usuario.assert_called_once_with(usuario_id_teste, servidor_id_teste)

def test_listar_personagens_erro_repositorio():
    # Arrange
    repo_mock = MagicMock()
    erro_esperado = Exception("Erro simulado no banco de dados")
    repo_mock.listar_por_usuario.side_effect = erro_esperado # Simula exceção no repositório
    caso_uso = ListarPersonagens(repo_mock)
    usuario_id_teste = 123
    servidor_id_teste = 456

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        caso_uso.executar(usuario_id_teste, servidor_id_teste)
    assert excinfo.value is erro_esperado # Verifica se a exceção original foi propagada
    repo_mock.listar_por_usuario.assert_called_once_with(usuario_id_teste, servidor_id_teste)