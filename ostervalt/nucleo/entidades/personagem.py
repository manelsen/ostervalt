from datetime import datetime
from typing import Optional
from ostervalt.infraestrutura.persistencia.models import StatusPersonagem # Adicionado

class Personagem:
    def __init__(self, nome: str, id: Optional[int] = None, nivel: int = 1, dinheiro: int = 0, ultimo_trabalho: Optional[datetime] = None, ultimo_crime: Optional[datetime] = None, usuario_id: Optional[int] = None, servidor_id: Optional[int] = None, status: StatusPersonagem = StatusPersonagem.ATIVO, marcos: int = 0): # Adicionado status e marcos, renomeado ultimo_tempo_*
        self.id = id # Pode ser None inicialmente, definido pelo repositório
        self.nome = nome
        self.nivel = nivel
        self.dinheiro = dinheiro
        self.ultimo_trabalho = ultimo_trabalho
        self.ultimo_crime = ultimo_crime
        self.usuario_id = usuario_id
        self.servidor_id = servidor_id
        self.status = status # Adicionado
        self.marcos = marcos # Adicionado