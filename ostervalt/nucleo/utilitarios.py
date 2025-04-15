import datetime
import random
import math

def verificar_cooldown(ultimo_tempo: datetime.datetime | None, intervalo_segundos: int, tempo_atual: datetime.datetime) -> bool:
    """
    Verifica se o cooldown de uma ação já expirou.

    Args:
        ultimo_tempo (datetime | None): Timestamp da última vez que a ação foi executada.
        intervalo_segundos (int): Intervalo de cooldown em segundos.
        tempo_atual (datetime): Timestamp atual.

    Returns:
        bool: True se o cooldown expirou ou se nunca foi executado antes, False caso contrário.
    """
    if ultimo_tempo:
        delta = tempo_atual - ultimo_tempo
        return delta.total_seconds() >= intervalo_segundos
    return True

def calcular_recompensa_trabalho(nivel_personagem: int, tiers_config: dict) -> int:
    """
    Calcula a recompensa em dinheiro para a ação de trabalhar, baseado no nível do personagem e na configuração de tiers.

    Args:
        nivel_personagem (int): Nível atual do personagem.
        tiers_config (dict): Dicionário de configuração dos tiers (ex: server_data["tiers"]).

    Returns:
        int: Valor da recompensa em dinheiro.
    """
    tier_name = None
    for nome_tier, dados_tier in tiers_config.items():
        if isinstance(dados_tier, dict) and "nivel_min" in dados_tier and "nivel_max" in dados_tier:
            if dados_tier["nivel_min"] <= nivel_personagem <= dados_tier["nivel_max"]:
                tier_name = nome_tier
                break
    if tier_name and isinstance(tiers_config.get(tier_name), dict) and "recompensa" in tiers_config[tier_name]:
        return tiers_config[tier_name]["recompensa"]
    return 0


def executar_logica_crime(probabilidade_sucesso: int, ganho_min: int, ganho_max: int, perda_min: int, perda_max: int) -> tuple[bool, int]:
    """
    Executa a lógica para simular a ação de cometer um crime, determinando se foi bem-sucedido e o resultado financeiro.

    Args:
        probabilidade_sucesso (int): Probabilidade de sucesso do crime (0-100).
        ganho_min (int): Ganho mínimo em caso de sucesso.
        ganho_max (int): Ganho máximo em caso de sucesso.
        perda_min (int): Perda mínima em caso de falha.
        perda_max (int): Perda máxima em caso de falha.

    Returns:
        tuple[bool, int]: Uma tupla contendo:
            - bool: True se o crime foi bem-sucedido, False se falhou.
            - int: Valor ganho (positivo) em caso de sucesso ou perdido (negativo) em caso de falha.
    """
    chance = random.randint(1, 100)
    if chance <= probabilidade_sucesso:
        recompensa = random.randint(ganho_min, ganho_max)
        return True, recompensa
    else:
        perda = random.randint(perda_min, perda_max)
        return False, -perda

# Função calculate_level
def calculate_level(marcos_val: int | float) -> int:
    """Calcula o nível com base nos marcos (assumindo marcos_val = total_partes / 16)."""
    if not isinstance(marcos_val, (int, float)) or marcos_val < 0: return 1
    level = math.floor(marcos_val) + 1
    return max(1, min(level, 20))

# Função formatar_marcos (lógica de fração corrigida para passar nos testes)
def formatar_marcos(marcos_partes: int) -> str:
    """
    Formata a representação dos marcos para exibição.

    Args:
        marcos_partes (int): Partes de marcos.

    Returns:
        str: String formatada com a representação dos marcos.
    """
    if not isinstance(marcos_partes, int) or marcos_partes < 0: return "0 Marcos"
    full_marcos = marcos_partes // 16
    remaining_parts = marcos_partes % 16
    level = calculate_level(marcos_partes / 16.0)

    if remaining_parts == 0:
        return f"{full_marcos} Marcos"

    # Testes esperam que níveis > 4 mostrem sempre /16
    if level <= 4:
        return f"{full_marcos} Marcos" # Níveis 1-4 não mostram partes
    else:
        return f"{full_marcos} e {remaining_parts}/16 Marcos"


# Função marcos_to_gain
def marcos_to_gain(level: int) -> int:
    """
    Determina quantos marcos um personagem ganha ao usar o comando /up.
    A lógica de progressão está definida aqui.

    Args:
        level (int): Nível atual do personagem.

    Returns:
        int: Quantidade de marcos a ganhar.
    """
    if level <= 4:
        return 16
    elif level <= 12:
        return 4
    elif level <= 16:
        return 2
    else: # Nível 17-20 (e acima, por segurança)
        return 1
