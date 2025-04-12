from ostervalt.nucleo.repositorios import RepositorioItens
from ostervalt.nucleo.entidades.item import Item
from typing import List

class ListarItens:
    def __init__(self, repositorio_itens: RepositorioItens):
        self.repositorio_itens = repositorio_itens

    def executar(self) -> List[Item]:
        return self.repositorio_itens.listar_por_raridade(raridade=None) # Implementar lógica de raridade se necessário