import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens

def test_listar_personagens_sucesso():
    repo_personagens = MagicMock()
    repo_personagens.listar.return_value = ["p1", "p2"]
    caso_uso = ListarPersonagens(repo_personagens)
    personagens = caso_uso.executar()
    assert personagens == ["p1", "p2"]

def test_listar_personagens_falha():
    repo_personagens = MagicMock()
    repo_personagens.listar.side_effect = Exception("Erro ao listar personagens")
    caso_uso = ListarPersonagens(repo_personagens)
    with pytest.raises(Exception):
        caso_uso.executar()