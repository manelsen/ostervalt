import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.criar_personagem import CriarPersonagem

class DummyPersonagem:
    def __init__(self, nome, usuario_id, servidor_id):
        self.nome = nome
        self.usuario_id = usuario_id
        self.servidor_id = servidor_id

def test_criar_personagem_sucesso():
    repo_mock = MagicMock()
    repo_mock.obter_por_nome.return_value = None
    repo_mock.criar.return_value = DummyPersonagem("Teste", 1, 1)
    caso_uso = CriarPersonagem(repo_mock)
    personagem = caso_uso.executar("Teste", 1, 1)
    assert personagem.nome == "Teste"
    assert personagem.usuario_id == 1
    assert personagem.servidor_id == 1

def test_criar_personagem_nome_existente():
    repo_mock = MagicMock()
    repo_mock.obter_por_nome.return_value = DummyPersonagem("Teste", 1, 1)
    caso_uso = CriarPersonagem(repo_mock)
    with pytest.raises(Exception):
        caso_uso.executar("Teste", 1, 1)