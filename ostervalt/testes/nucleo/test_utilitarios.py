import pytest
import datetime
from ostervalt.nucleo import utilitarios

def test_verificar_cooldown_true():
    ultimo = datetime.datetime.now() - datetime.timedelta(seconds=100)
    intervalo = 60
    tempo_atual = datetime.datetime.now()
    assert utilitarios.verificar_cooldown(ultimo, intervalo, tempo_atual) is True

def test_verificar_cooldown_false():
    ultimo = datetime.datetime.now()
    intervalo = 60
    tempo_atual = datetime.datetime.now()
    assert utilitarios.verificar_cooldown(ultimo, intervalo, tempo_atual) is False

def test_verificar_cooldown_none():
    intervalo = 60
    tempo_atual = datetime.datetime.now()
    assert utilitarios.verificar_cooldown(None, intervalo, tempo_atual) is True

def test_calcular_recompensa_trabalho():
    tiers = {1: 100, 2: 200}
    assert utilitarios.calcular_recompensa_trabalho(1, tiers) == 100
    assert utilitarios.calcular_recompensa_trabalho(2, tiers) == 200

def test_executar_logica_crime_sucesso():
    # Probabilidade 100% garante sucesso
    resultado, valor = utilitarios.executar_logica_crime(100, 10, 20, 1, 5)
    assert resultado is True
    assert 10 <= valor <= 20

def test_executar_logica_crime_falha():
    # Probabilidade 0% garante falha
    resultado, valor = utilitarios.executar_logica_crime(0, 10, 20, 1, 5)
    assert resultado is False
    assert 1 <= valor <= 5

def test_calcular_nivel():
    assert utilitarios.calcular_nivel(0) == 1
    assert utilitarios.calcular_nivel(100) >= 1

def test_formatar_marcos():
    assert isinstance(utilitarios.formatar_marcos(1000), str)