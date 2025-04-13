import datetime
import random
import math

def verificar_cooldown(ultimo_tempo: datetime.datetime | None, intervalo_segundos: int, tempo_atual) -> bool: # tempo_atual sem tipo definido
    """
    Verifica se o cooldown de uma ação já expirou.

    Args:
        ultimo_tempo (datetime | None): Timestamp da última vez que a ação foi executada.
        intervalo_segundos (int): Intervalo de cooldown em segundos.
        tempo_atual: Timestamp atual. # Removido tipo datetime.datetime

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
        if dados_tier["nivel_min"] <= nivel_personagem <= dados_tier["nivel_max"]:
            tier_name = nome_tier
            break
    if tier_name:
        return tiers_config[tier_name]["recompensa"]
    return 0  # Recompensa padrão caso não encontre tier


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

def calcular_nivel(marcos: float) -> int:
    """
    Calcula o nível do personagem com base nos marcos.

    Args:
        marcos (float): Quantidade de marcos.

    Returns:
        int: Nível calculado.
    """
    level = min(20, math.floor(marcos) + 1)
    return level

def formatar_marcos(marcos_partes: int) -> str:
    """
    Formata a representação dos marcos para exibição.

    Args:
        marcos_partes (int): Partes de marcos.

    Returns:
        str: String formatada com a representação dos marcos.
    """
    full_marcos = marcos_partes // 16
    remaining_parts = marcos_partes % 16

    if remaining_parts == 0:
        return f"{full_marcos} Marcos"

    level = calcular_nivel(marcos_partes / 16)

    if level <= 4:
        return f"{full_marcos} Marcos"
    elif level <= 12:
        return f"{full_marcos} e {remaining_parts // 4}/4 Marcos"
    elif level <= 16:
        return f"{full_marcos} e {remaining_parts // 2}/8 Marcos"
    else:
        return f"{full_marcos} e {remaining_parts}/16 Marcos"
        return False, -perda
    return 0  # Recompensa padrão caso não encontre tier


def marcos_to_gain(level: int, config: dict) -> int:
    """
    Determina quantos marcos um personagem ganha ao usar o comando /up.

    Args:
        level (int): Nível atual do personagem.
        config (dict): Dicionário de configuração carregado.

    Returns:
        int: Quantidade de marcos a ganhar.
    """
    # Acesso à configuração agora é passado como argumento
    marcos_por_nivel = config.get("progressao", {}).get("marcos_por_nivel", {})
    if level <= 4:
        return marcos_por_nivel.get("1-4", 16)
    elif level <= 12:
        return marcos_por_nivel.get("5-12", 4)
    elif level <= 16:
        return marcos_por_nivel.get("13-16", 2)
    else:
        return marcos_por_nivel.get("17-20", 1)
