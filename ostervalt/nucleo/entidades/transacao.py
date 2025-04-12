from datetime import datetime
from enum import Enum
from typing import Optional

class TipoTransacao(Enum):
    DEPOSITO = 'depósito'
    SAQUE = 'saque'
    COMPRA = 'compra'

class Transacao:
    def __init__(self, id: int, usuario_id: int, tipo: TipoTransacao, valor: float, data: datetime):
        self.id = id
        self.usuario_id = usuario_id
        self.tipo = tipo
        self.valor = valor
        self.data = data