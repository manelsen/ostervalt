import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.obter_item import ObterItem
from ostervalt.nucleo.entidades.item import Item

def test_obter_item_sucesso():
    # Arrange
    repo_mock = MagicMock()
    item_mock = MagicMock(spec=Item)
    item_mock.id = 1
    repo_mock.obter_por_id.return_value = item_mock
    caso_uso = ObterItem(repo_mock)
    item_id = 1

    # Act
    item = caso_uso.executar(item_id)

    # Assert
    assert item is item_mock
    repo_mock.obter_por_id.assert_called_once_with(item_id)

def test_obter_item_nao_encontrado():
    # Arrange
    repo_mock = MagicMock()
    repo_mock.obter_por_id.return_value = None
    caso_uso = ObterItem(repo_mock)
    item_id = 999

    # Act
    item = caso_uso.executar(item_id)

    # Assert
    assert item is None
    repo_mock.obter_por_id.assert_called_once_with(item_id)

def test_obter_item_erro_repositorio():
    # Arrange
    repo_mock = MagicMock()
    erro_esperado = Exception("Erro no repositório")
    repo_mock.obter_por_id.side_effect = erro_esperado
    caso_uso = ObterItem(repo_mock)
    item_id = 1

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        caso_uso.executar(item_id)
    assert excinfo.value is erro_esperado