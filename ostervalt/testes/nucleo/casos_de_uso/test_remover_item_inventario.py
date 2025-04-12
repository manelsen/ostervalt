import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.remover_item_inventario import RemoverItemInventario

def test_remover_item_inventario_sucesso():
    repo_inv = MagicMock()
    repo_inv.remover_item.return_value = True
    caso_uso = RemoverItemInventario(repo_inv)
    resultado = caso_uso.executar(1, 2, 3)
    assert resultado is True

def test_remover_item_inventario_falha():
    repo_inv = MagicMock()
    repo_inv.remover_item.side_effect = Exception("Erro ao remover item")
    caso_uso = RemoverItemInventario(repo_inv)
    with pytest.raises(Exception):
        caso_uso.executar(1, 2, 3)