import datetime

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