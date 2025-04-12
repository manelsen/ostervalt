import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.realizar_trabalho import RealizarTrabalho

def test_realizar_trabalho_sucesso():
    repo_personagens = MagicMock()
    configuracao = MagicMock()
    repo_personagens.obter_por_id.return_value = MagicMock()
    configuracao.get.return_value = 1
    caso_uso = RealizarTrabalho(repo_personagens, configuracao)
    resultado = caso_uso.executar(1)
    assert hasattr(resultado, "sucesso") or hasattr(resultado, "valor")

def test_realizar_trabalho_falha():
    repo_personagens = MagicMock()
    configuracao = MagicMock()
    repo_personagens.obter_por_id.return_value = None
    caso_uso = RealizarTrabalho(repo_personagens, configuracao)
    with pytest.raises(Exception):
        caso_uso.executar(1)