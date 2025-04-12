from ostervalt.nucleo.repositorios import RepositorioItens
from ostervalt.nucleo.entidades.item import Item
from typing import Optional

class ObterItem:
    def __init__(self, repositorio_itens: RepositorioItens):
        self.repositorio_itens = repositorio_itens

    def executar(self, item_id: int) -> Optional[Item]:
        return self.repositorio_itens.obter_por_id(item_id)