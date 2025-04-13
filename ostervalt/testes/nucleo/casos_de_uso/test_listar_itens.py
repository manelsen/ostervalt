import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.listar_itens import ListarItens
from ostervalt.nucleo.entidades.item import Item

def test_listar_itens_sucesso():
    # Arrange
    repo_mock = MagicMock()
    item1 = MagicMock(spec=Item)
    item2 = MagicMock(spec=Item)
    lista_esperada = [item1, item2]
    repo_mock.listar_por_raridade.return_value = lista_esperada
    caso_uso = ListarItens(repo_mock)

    # Act
    itens = caso_uso.executar()

    # Assert
    assert itens == lista_esperada
    repo_mock.listar_por_raridade.assert_called_once_with(raridade=None)

def test_listar_itens_vazio():
    # Arrange
    repo_mock = MagicMock()
    repo_mock.listar_por_raridade.return_value = []  # Lista vazia
    caso_uso = ListarItens(repo_mock)

    # Act
    itens = caso_uso.executar()

    # Assert
    assert itens == []
    repo_mock.listar_por_raridade.assert_called_once_with(raridade=None)

def test_listar_itens_erro_repositorio():
    # Arrange
    repo_mock = MagicMock()
    erro_esperado = Exception("Erro no repositório")
    repo_mock.listar_por_raridade.side_effect = erro_esperado
    caso_uso = ListarItens(repo_mock)

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        caso_uso.executar()
    assert excinfo.value is erro_esperado