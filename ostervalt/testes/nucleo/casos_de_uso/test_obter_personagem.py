import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.obter_personagem import ObterPersonagem

def test_obter_personagem_sucesso():
    repo_personagens = MagicMock()
    repo_personagens.obter_por_id.return_value = "personagem"
    caso_uso = ObterPersonagem(repo_personagens)
    personagem = caso_uso.executar(1)
    assert personagem == "personagem"

def test_obter_personagem_falha():
    repo_personagens = MagicMock()
    repo_personagens.obter_por_id.side_effect = Exception("Erro ao obter personagem")
    caso_uso = ObterPersonagem(repo_personagens)
    with pytest.raises(Exception):
        caso_uso.executar(1)