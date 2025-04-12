from ostervalt.nucleo.repositorios import RepositorioInventario, RepositorioItens
from ostervalt.nucleo.entidades.item import ItemInventario

class AdicionarItemInventario:
    def __init__(self, repositorio_inventario: RepositorioInventario, repositorio_itens: RepositorioItens):
        self.repositorio_inventario = repositorio_inventario
        self.repositorio_itens = repositorio_itens

    def executar(self, personagem_id: int, item_id: int, quantidade: int) -> ItemInventario:
        item = self.repositorio_itens.obter_por_id(item_id)
        if not item:
            raise ValueError(f"Item com ID {item_id} não encontrado.")
        
        item_inventario = ItemInventario(item_id=item_id, personagem_id=personagem_id, quantidade=quantidade)
        self.repositorio_inventario.adicionar_item(item_inventario)
        return item_inventario