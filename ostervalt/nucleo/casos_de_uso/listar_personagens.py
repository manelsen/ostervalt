from ostervalt.nucleo.repositorios import RepositorioPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem
from typing import List

class ListarPersonagens:
    def __init__(self, repositorio_personagens: RepositorioPersonagens):
        self.repositorio_personagens = repositorio_personagens

    def executar(self, usuario_id: int, servidor_id: int) -> List[Personagem]:
        return self.repositorio_personagens.listar_por_usuario(usuario_id, servidor_id)