from ostervalt.nucleo.repositorios import RepositorioPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem
from typing import Optional

class ObterPersonagem:
    def __init__(self, repositorio_personagens: RepositorioPersonagens):
        self.repositorio_personagens = repositorio_personagens

    def executar(self, personagem_id: int) -> Optional[Personagem]:
        return self.repositorio_personagens.obter_por_id(personagem_id)