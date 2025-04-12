from ostervalt.nucleo.repositorios import RepositorioPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem

class CriarPersonagem:
    def __init__(self, repositorio_personagens: RepositorioPersonagens):
        self.repositorio_personagens = repositorio_personagens

    def executar(self, nome: str, usuario_id: int, servidor_id: int) -> Personagem:
        personagem = Personagem(nome=nome, usuario_id=usuario_id, servidor_id=servidor_id)
        self.repositorio_personagens.adicionar(personagem)
        return personagem