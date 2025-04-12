import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.listar_inventario import ListarInventario

def test_listar_inventario_sucesso():
    repo_inv = MagicMock()
    repo_inv.listar_por_personagem.return_value = ["item1", "item2"]
    caso_uso = ListarInventario(repo_inv)
    itens = caso_uso.executar(1)
    assert itens == ["item1", "item2"]

def test_listar_inventario_falha():
    repo_inv = MagicMock()
    repo_inv.listar_por_personagem.side_effect = Exception("Erro ao listar inventário")
    caso_uso = ListarInventario(repo_inv)
    with pytest.raises(Exception):
        caso_uso.executar(1)