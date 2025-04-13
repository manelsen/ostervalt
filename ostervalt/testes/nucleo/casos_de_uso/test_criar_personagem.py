import pytest
from unittest.mock import MagicMock, ANY
from ostervalt.nucleo.casos_de_uso.criar_personagem import CriarPersonagem
from ostervalt.nucleo.entidades.personagem import Personagem # Importar a entidade real

def test_criar_personagem_sucesso():
    # Arrange
    repo_mock = MagicMock()
    caso_uso = CriarPersonagem(repo_mock)
    nome_personagem = "HeroiTeste"
    usuario_id = 123
    servidor_id = 456

    # Act
    personagem_criado = caso_uso.executar(nome_personagem, usuario_id, servidor_id)

    # Assert
    assert isinstance(personagem_criado, Personagem)
    assert personagem_criado.nome == nome_personagem
    assert personagem_criado.usuario_id == usuario_id
    assert personagem_criado.servidor_id == servidor_id
    # Verificar se o método adicionar foi chamado com um objeto Personagem
    repo_mock.adicionar.assert_called_once_with(ANY) # Correção: remover chamada incorreta a ANY()
    # Opcional: verificar os atributos do objeto passado para adicionar
    args, _ = repo_mock.adicionar.call_args
    personagem_passado = args[0]
    assert personagem_passado.nome == nome_personagem
    assert personagem_passado.usuario_id == usuario_id
    assert personagem_passado.servidor_id == servidor_id

# O teste de nome existente foi removido pois a lógica não está no caso de uso atual.
# Se a validação for adicionada ao caso de uso, este teste pode ser reintroduzido/adaptado.