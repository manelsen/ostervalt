import pytest
from unittest.mock import MagicMock, ANY
# Imports absolutos a partir da raiz do projeto
from ostervalt.nucleo.casos_de_uso.adicionar_item_inventario import AdicionarItemInventario
from ostervalt.nucleo.entidades.item import ItemInventario

def test_adicionar_item_inventario_sucesso():
    # Arrange
    repo_inv = MagicMock()
    repo_itens = MagicMock()
    item_mock = MagicMock()  # Mock do item que existe
    repo_itens.obter_por_id.return_value = item_mock
    caso_uso = AdicionarItemInventario(repo_inv, repo_itens)
    personagem_id = 1
    item_id = 2
    quantidade = 3

    # Act
    item_inventario = caso_uso.executar(personagem_id, item_id, quantidade)

    # Assert
    assert isinstance(item_inventario, ItemInventario)
    assert item_inventario.personagem_id == personagem_id
    assert item_inventario.item_id == item_id
    assert item_inventario.quantidade == quantidade
    repo_itens.obter_por_id.assert_called_once_with(item_id)
    repo_inv.adicionar_item.assert_called_once_with(ANY) # Correção: remover chamada incorreta a ANY()

def test_adicionar_item_inventario_item_nao_existe():
    # Arrange
    repo_inv = MagicMock()
    repo_itens = MagicMock()
    repo_itens.obter_por_id.return_value = None  # Item não existe
    caso_uso = AdicionarItemInventario(repo_inv, repo_itens)
    personagem_id = 1
    item_id = 999  # ID inválido
    quantidade = 1

    # Act & Assert
    with pytest.raises(ValueError, match=f"Item com ID {item_id} não encontrado"):
        caso_uso.executar(personagem_id, item_id, quantidade)

def test_adicionar_item_inventario_erro_repositorio():
    # Arrange
    repo_inv = MagicMock()
    repo_itens = MagicMock()
    item_mock = MagicMock()
    repo_itens.obter_por_id.return_value = item_mock
    erro_esperado = Exception("Erro no repositório")
    repo_inv.adicionar_item.side_effect = erro_esperado
    caso_uso = AdicionarItemInventario(repo_inv, repo_itens)
    personagem_id = 1
    item_id = 2
    quantidade = 3

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        caso_uso.executar(personagem_id, item_id, quantidade)
    assert excinfo.value is erro_esperado