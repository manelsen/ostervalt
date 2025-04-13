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
    tiers_config = {
        "tier1": {"nivel_min": 1, "nivel_max": 5, "recompensa": 100},
        "tier2": {"nivel_min": 6, "nivel_max": 10, "recompensa": 200},
    }
    assert utilitarios.calcular_recompensa_trabalho(3, tiers_config) == 100
    assert utilitarios.calcular_recompensa_trabalho(8, tiers_config) == 200
    assert utilitarios.calcular_recompensa_trabalho(15, tiers_config) == 0 # Nível fora dos tiers

def test_executar_logica_crime_sucesso():
    # Probabilidade 100% garante sucesso
    resultado, valor = utilitarios.executar_logica_crime(100, 10, 20, 1, 5)
    assert resultado is True
    assert 10 <= valor <= 20

def test_executar_logica_crime_falha():
    # Probabilidade 0% garante falha
    resultado, valor = utilitarios.executar_logica_crime(0, 10, 20, 1, 5)
    assert resultado is False
    assert -5 <= valor <= -1 # Valor deve ser negativo e dentro do range de perda

@pytest.mark.parametrize("marcos, nivel_esperado", [
    (0, 1),         # Marcos = 0 -> Nível 1
    (15/16, 1),     # Menos de 1 marco completo -> Nível 1
    (16/16, 2),     # 1 marco completo -> Nível 2
    (1.5 * 16 / 16, 2), # 1.5 marcos -> Nível 2
    (31/16, 2),     # Quase 2 marcos -> Nível 2
    (32/16, 3),     # 2 marcos completos -> Nível 3
    (19 * 16 / 16, 20), # 19 marcos -> Nível 20
    (19.5 * 16 / 16, 20), # 19.5 marcos -> Nível 20
    (20 * 16 / 16, 20), # 20 marcos -> Nível 20 (Limite máximo)
    (25 * 16 / 16, 20), # Mais de 20 marcos -> Nível 20 (Limite máximo)
])
def test_calcular_nivel(marcos, nivel_esperado):
    assert utilitarios.calcular_nivel(marcos) == nivel_esperado

@pytest.mark.parametrize("marcos_partes, nivel, esperado", [
    (0, 1, "0 Marcos"),                 # Nível 1, 0 partes
    (15, 1, "0 Marcos"),                # Nível 1, 15 partes
    (16, 2, "1 Marcos"),                # Nível 2, 16 partes (1 completo)
    (31, 2, "1 Marcos"),                # Nível 2, 31 partes
    (32, 3, "2 Marcos"),                # Nível 3, 32 partes (2 completos)
    (35, 3, "2 Marcos"),                # Nível 3, 35 partes
    (64, 5, "4 Marcos"),          # Nível 5 (Tier 2), 64 partes (4 completos) - Aceito sem fração 0
    (68, 5, "4 e 1/4 Marcos"),          # Nível 5, 68 partes
    (79, 5, "4 e 3/4 Marcos"),          # Nível 5, 79 partes
    (192, 13, "12 Marcos"),       # Nível 13 (Tier 3), 192 partes (12 completos) - Aceito sem fração 0
    (194, 13, "12 e 1/8 Marcos"),       # Nível 13, 194 partes
    (207, 13, "12 e 7/8 Marcos"),       # Nível 13, 207 partes
    (256, 17, "16 Marcos"),      # Nível 17 (Tier 4), 256 partes (16 completos) - Aceito sem fração 0
    (257, 17, "16 e 1/16 Marcos"),      # Nível 17, 257 partes
    (271, 17, "16 e 15/16 Marcos"),     # Nível 17, 271 partes
    (320, 20, "20 Marcos"),      # Nível 20, 320 partes (20 completos) - Aceito sem fração 0
])
def test_formatar_marcos(marcos_partes, nivel, esperado):
    # Mockar calcular_nivel para forçar o nível desejado para o teste de formatação
    original_calcular_nivel = utilitarios.calcular_nivel
    utilitarios.calcular_nivel = lambda m: nivel
    try:
        assert utilitarios.formatar_marcos(marcos_partes) == esperado
    finally:
        # Restaurar a função original
        utilitarios.calcular_nivel = original_calcular_nivel

# Testes para marcos_to_gain
@pytest.mark.parametrize("level, esperado", [
    (1, 16), (4, 16),   # Nível 1-4
    (5, 4), (12, 4),    # Nível 5-12
    (13, 2), (16, 2),   # Nível 13-16
    (17, 1), (20, 1),   # Nível 17-20
    (25, 1),            # Nível acima de 20 (deve retornar o último valor)
])
def test_marcos_to_gain(level, esperado):
    config = {
        "progressao": {
            "marcos_por_nivel": {
                "1-4": 16,
                "5-12": 4,
                "13-16": 2,
                "17-20": 1
            }
        }
    }
    assert utilitarios.marcos_to_gain(level, config) == esperado

def test_marcos_to_gain_config_ausente():
    # Testa o comportamento se a configuração estiver ausente ou incompleta
    assert utilitarios.marcos_to_gain(5, {}) == 4 # Deve usar valor padrão se chave não existe? A implementação atual usa .get com padrão
    assert utilitarios.marcos_to_gain(5, {"progressao": {}}) == 4
    assert utilitarios.marcos_to_gain(5, {"progressao": {"marcos_por_nivel": {}}}) == 4 # Assume padrão 4 para 5-12 se não especificado? Sim.