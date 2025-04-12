from ostervalt.nucleo.repositorios import RepositorioPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem

class RealizarTrabalho:
    def __init__(self, repositorio_personagens: RepositorioPersonagens):
        self.repositorio_personagens = repositorio_personagens

    def executar(self, personagem_id: int) -> Personagem:
        personagem = self.repositorio_personagens.obter_por_id(personagem_id)
        if personagem:
            # Lógica de trabalho a ser implementada
            return personagem
        else:
            raise ValueError(f"Personagem com ID {personagem_id} não encontrado.")