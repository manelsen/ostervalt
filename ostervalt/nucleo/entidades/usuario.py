from datetime import datetime
from typing import Optional

class Usuario:
    def __init__(self, id: int, email: str, senha_hash: str, data_criacao: datetime):
        self.id = id
        self.email = email
        self.senha_hash = senha_hash
        self.data_criacao = data_criacao