from datetime import datetime
from typing import Optional

class Personagem:
    def __init__(self, nome: str, id: Optional[int] = None, nivel: int = 1, dinheiro: int = 0, ultimo_tempo_trabalho: Optional[datetime] = None, ultimo_tempo_crime: Optional[datetime] = None, usuario_id: Optional[int] = None, servidor_id: Optional[int] = None):
        self.id = id # Pode ser None inicialmente, definido pelo repositório
        self.nome = nome
        self.nivel = nivel
        self.dinheiro = dinheiro
        self.ultimo_tempo_trabalho = ultimo_tempo_trabalho
        self.ultimo_tempo_crime = ultimo_tempo_crime # Adicionado
        self.usuario_id = usuario_id
        self.servidor_id = servidor_id