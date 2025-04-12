import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.adicionar_item_inventario import AdicionarItemInventario

class DummyItemInventario:
    def __init__(self, personagem_id, item_id, quantidade):
        self.personagem_id = personagem_id
        self.item_id = item_id
        self.quantidade = quantidade

def test_adicionar_item_inventario_sucesso():
    repo_inv = MagicMock()
    repo_itens = MagicMock()
    repo_inv.adicionar_item.return_value = DummyItemInventario(1, 2, 3)
    caso_uso = AdicionarItemInventario(repo_inv, repo_itens)
    item = caso_uso.executar(1, 2, 3)
    assert item.personagem_id == 1
    assert item.item_id == 2
    assert item.quantidade == 3

def test_adicionar_item_inventario_falha():
    repo_inv = MagicMock()
    repo_itens = MagicMock()
    repo_inv.adicionar_item.side_effect = Exception("Erro ao adicionar item")
    caso_uso = AdicionarItemInventario(repo_inv, repo_itens)
    with pytest.raises(Exception):
        caso_uso.executar(1, 2, 3)