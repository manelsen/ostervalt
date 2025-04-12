import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.obter_item import ObterItem

def test_obter_item_sucesso():
    repo_itens = MagicMock()
    repo_itens.obter_por_id.return_value = "item"
    caso_uso = ObterItem(repo_itens)
    item = caso_uso.executar(1)
    assert item == "item"

def test_obter_item_falha():
    repo_itens = MagicMock()
    repo_itens.obter_por_id.side_effect = Exception("Erro ao obter item")
    caso_uso = ObterItem(repo_itens)
    with pytest.raises(Exception):
        caso_uso.executar(1)