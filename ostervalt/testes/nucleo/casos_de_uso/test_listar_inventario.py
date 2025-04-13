import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.listar_inventario import ListarInventario
from ostervalt.nucleo.entidades.item import ItemInventario

def test_listar_inventario_sucesso():
    # Arrange
    repo_mock = MagicMock()
    item1 = MagicMock(spec=ItemInventario)
    item2 = MagicMock(spec=ItemInventario)
    lista_esperada = [item1, item2]
    repo_mock.obter_itens.return_value = lista_esperada
    caso_uso = ListarInventario(repo_mock)
    personagem_id = 1

    # Act
    itens = caso_uso.executar(personagem_id)

    # Assert
    assert itens == lista_esperada
    repo_mock.obter_itens.assert_called_once_with(personagem_id)

def test_listar_inventario_vazio():
    # Arrange
    repo_mock = MagicMock()
    repo_mock.obter_itens.return_value = []  # Inventário vazio
    caso_uso = ListarInventario(repo_mock)
    personagem_id = 1

    # Act
    itens = caso_uso.executar(personagem_id)

    # Assert
    assert itens == []
    repo_mock.obter_itens.assert_called_once_with(personagem_id)

def test_listar_inventario_erro_repositorio():
    # Arrange
    repo_mock = MagicMock()
    erro_esperado = Exception("Erro no repositório")
    repo_mock.obter_itens.side_effect = erro_esperado
    caso_uso = ListarInventario(repo_mock)
    personagem_id = 1

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        caso_uso.executar(personagem_id)
    assert excinfo.value is erro_esperado