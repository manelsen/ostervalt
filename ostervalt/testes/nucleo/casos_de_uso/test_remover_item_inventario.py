import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.remover_item_inventario import RemoverItemInventario

def test_remover_item_inventario_sucesso():
    # Arrange
    repo_mock = MagicMock()
    caso_uso = RemoverItemInventario(repo_mock)
    personagem_id = 1
    item_id = 2

    # Act
    caso_uso.executar(personagem_id, item_id)

    # Assert
    repo_mock.remover_item.assert_called_once_with(item_id, personagem_id)

def test_remover_item_inventario_erro_repositorio():
    # Arrange
    repo_mock = MagicMock()
    erro_esperado = Exception("Erro no repositório")
    repo_mock.remover_item.side_effect = erro_esperado
    caso_uso = RemoverItemInventario(repo_mock)
    personagem_id = 1
    item_id = 2

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        caso_uso.executar(personagem_id, item_id)
    assert excinfo.value is erro_esperado