from ostervalt.nucleo.repositorios import RepositorioInventario
from ostervalt.nucleo.entidades.item import ItemInventario
from typing import List

class ListarInventario:
    def __init__(self, repositorio_inventario: RepositorioInventario):
        self.repositorio_inventario = repositorio_inventario

    def executar(self, personagem_id: int) -> List[ItemInventario]:
        return self.repositorio_inventario.obter_itens(personagem_id)