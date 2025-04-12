import pytest
from unittest.mock import MagicMock
from ostervalt.nucleo.casos_de_uso.cometer_crime import CometerCrime

class DummyResultadoCrimeDTO:
    def __init__(self, sucesso, valor):
        self.sucesso = sucesso
        self.valor = valor

def test_cometer_crime_sucesso():
    repo_personagens = MagicMock()
    configuracao = MagicMock()
    repo_personagens.obter_por_id.return_value = MagicMock()
    configuracao.get.return_value = 100  # Probabilidade de sucesso máxima
    caso_uso = CometerCrime(repo_personagens, configuracao)
    resultado = caso_uso.executar(1)
    assert hasattr(resultado, "sucesso")

def test_cometer_crime_falha():
    repo_personagens = MagicMock()
    configuracao = MagicMock()
    repo_personagens.obter_por_id.return_value = None  # Personagem não encontrado
    caso_uso = CometerCrime(repo_personagens, configuracao)
    with pytest.raises(Exception):
        caso_uso.executar(1)