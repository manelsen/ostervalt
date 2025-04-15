import pytest
import datetime
from unittest.mock import MagicMock, patch
from ostervalt.nucleo import utilitarios # Importa o módulo

# Testes para verificar_cooldown
@pytest.mark.parametrize("ultimo_tempo, intervalo, tempo_atual, esperado", [
    (datetime.datetime(2023, 1, 1, 12, 0, 0), 3600, datetime.datetime(2023, 1, 1, 13, 0, 0), True),  # Exatamente 1 hora depois
    (datetime.datetime(2023, 1, 1, 12, 0, 0), 3600, datetime.datetime(2023, 1, 1, 13, 0, 1), True),  # Mais de 1 hora depois
    (datetime.datetime(2023, 1, 1, 12, 0, 0), 3600, datetime.datetime(2023, 1, 1, 12, 59, 59), False), # Menos de 1 hora depois
    (None, 3600, datetime.datetime(2023, 1, 1, 13, 0, 0), True),                                  # Nunca executado antes
])
def test_verificar_cooldown(ultimo_tempo, intervalo, tempo_atual, esperado):
    assert utilitarios.verificar_cooldown(ultimo_tempo, intervalo, tempo_atual) == esperado

# Testes para calcular_recompensa_trabalho
@pytest.mark.parametrize("nivel, tiers_config, esperado", [
    (1, {"t1": {"nivel_min": 1, "nivel_max": 5, "recompensa": 100}}, 100),
    (5, {"t1": {"nivel_min": 1, "nivel_max": 5, "recompensa": 100}}, 100),
    (6, {"t1": {"nivel_min": 1, "nivel_max": 5, "recompensa": 100}}, 0), # Nível fora do tier
    (10, {"t1": {"nivel_min": 1, "nivel_max": 5, "recompensa": 100}, "t2": {"nivel_min": 6, "nivel_max": 10, "recompensa": 200}}, 200),
    (10, {}, 0), # Sem tiers definidos
    (3, {"t1": {"nivel_min": 1, "nivel_max": 5}}, 0), # Tier sem recompensa definida
    (3, {"t1": "não é dict"}, 0), # Configuração de tier inválida
])
def test_calcular_recompensa_trabalho(nivel, tiers_config, esperado):
    assert utilitarios.calcular_recompensa_trabalho(nivel, tiers_config) == esperado

# Testes para executar_logica_crime
# Mockar random.randint para tornar o teste determinístico
@patch('ostervalt.nucleo.utilitarios.random.randint')
@pytest.mark.parametrize("chance_roll, prob_sucesso, ganho_min, ganho_max, perda_min, perda_max, esperado_sucesso, esperado_resultado", [
    (50, 50, 100, 200, 50, 100, True, 150),  # Sucesso (roll <= prob), valor médio
    (51, 50, 100, 200, 50, 100, False, -75), # Falha (roll > prob), valor médio
    (1, 50, 100, 100, 50, 50, True, 100),    # Sucesso (roll baixo), valor fixo
    (100, 50, 100, 100, 50, 50, False, -50),  # Falha (roll alto), valor fixo
    (70, 100, 10, 10, 1, 1, True, 10),       # Sucesso garantido
    (70, 0, 10, 10, 1, 1, False, -1),        # Falha garantida
])
def test_executar_logica_crime(mock_randint, chance_roll, prob_sucesso, ganho_min, ganho_max, perda_min, perda_max, esperado_sucesso, esperado_resultado):
    # Configura o mock para retornar primeiro o roll da chance, depois o roll do resultado financeiro
    if chance_roll <= prob_sucesso:
        # Simula o cálculo do ganho (ex: valor médio)
        mock_randint.side_effect = [chance_roll, (ganho_min + ganho_max) // 2]
    else:
        # Simula o cálculo da perda (ex: valor médio)
        mock_randint.side_effect = [chance_roll, (perda_min + perda_max) // 2]

    sucesso, resultado = utilitarios.executar_logica_crime(prob_sucesso, ganho_min, ganho_max, perda_min, perda_max)
    assert sucesso == esperado_sucesso
    # Para o resultado financeiro, verificamos se o mock foi chamado corretamente
    # e o valor retornado é o esperado (baseado no side_effect)
    if esperado_sucesso:
        assert resultado == (ganho_min + ganho_max) // 2
    else:
        assert resultado == -((perda_min + perda_max) // 2)

# Testes para calculate_level (usando o nome correto da função)
@pytest.mark.parametrize("marcos_val, esperado", [
    (0, 1), (0.0, 1),
    (15/16, 1),
    (16/16, 2), (1.0, 2),
    (24/16, 2), (1.5, 2),
    (31/16, 2),
    (32/16, 3), (2.0, 3),
    (304/16, 20), (19.0, 20),
    (312/16, 20), (19.5, 20),
    (320/16, 20), (20.0, 20),
    (400/16, 20), (25.0, 20), # Teste de limite superior
    (-1, 1), # Teste de valor inválido
])
def test_calculate_level(marcos_val, esperado):
    assert utilitarios.calculate_level(marcos_val) == esperado

# Testes para formatar_marcos (usando o nome correto da função)
@pytest.mark.parametrize("marcos_partes, esperado", [
    (0, "0 Marcos"),
    (15, "0 Marcos"),
    (16, "1 Marcos"),
    (31, "1 Marcos"),
    (32, "2 Marcos"),
    (35, "2 Marcos"),
    (64, "4 Marcos"),
    (68, "4 e 4/16 Marcos"), # Nível 5, mostra /16
    (79, "4 e 15/16 Marcos"),# Nível 5, mostra /16
    (192, "12 Marcos"),
    (194, "12 e 2/16 Marcos"), # Nível 13, mostra /16
    (207, "12 e 15/16 Marcos"),# Nível 13, mostra /16
    (256, "16 Marcos"),
    (257, "16 e 1/16 Marcos"), # Nível 17, mostra /16
    (271, "16 e 15/16 Marcos"),# Nível 17, mostra /16
    (320, "20 Marcos"),
    (-10, "0 Marcos"), # Teste de valor inválido
])
def test_formatar_marcos(marcos_partes, esperado):
    # Não precisamos mais mockar calculate_level aqui, pois formatar_marcos usa a versão correta
    assert utilitarios.formatar_marcos(marcos_partes) == esperado


# Testes para marcos_to_gain (usando o nome correto e sem config)
@pytest.mark.parametrize("level, esperado", [
    (1, 16), (4, 16),   # Nível 1-4
    (5, 4), (12, 4),    # Nível 5-12
    (13, 2), (16, 2),   # Nível 13-16
    (17, 1), (20, 1),   # Nível 17-20
    (25, 1),            # Nível acima de 20 (deve retornar o último valor)
])
def test_marcos_to_gain(level, esperado):
    assert utilitarios.marcos_to_gain(level) == esperado # Chamada sem config

def test_marcos_to_gain_niveis_intermediarios():
    assert utilitarios.marcos_to_gain(3) == 16
    assert utilitarios.marcos_to_gain(8) == 4
    assert utilitarios.marcos_to_gain(15) == 2
    assert utilitarios.marcos_to_gain(18) == 1