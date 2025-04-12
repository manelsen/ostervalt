import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.listar_itens import ListarItens

def test_listar_itens_sucesso():
    repo_itens = MagicMock()
    repo_itens.listar.return_value = ["item1", "item2"]
    caso_uso = ListarItens(repo_itens)
    itens = caso_uso.executar()
    assert itens == ["item1", "item2"]

def test_listar_itens_falha():
    repo_itens = MagicMock()
    repo_itens.listar.side_effect = Exception("Erro ao listar itens")
    caso_uso = ListarItens(repo_itens)
    with pytest.raises(Exception):
        caso_uso.executar()