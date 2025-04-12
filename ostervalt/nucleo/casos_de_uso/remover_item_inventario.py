from ostervalt.nucleo.repositorios import RepositorioInventario
from ostervalt.nucleo.entidades.item import ItemInventario

class RemoverItemInventario:
    def __init__(self, repositorio_inventario: RepositorioInventario):
        self.repositorio_inventario = repositorio_inventario

    def executar(self, personagem_id: int, item_id: int) -> None:
        self.repositorio_inventario.remover_item(item_id, personagem_id)