from sqlalchemy.orm import Session
from typing import List, Optional

from .models import EstoqueLojaItemModel, ItemModel

class RepositorioEstoqueLoja:
    def __init__(self, session: Session):
        self.session = session

    def adicionar(self, item_estoque: EstoqueLojaItemModel) -> EstoqueLojaItemModel:
        self.session.add(item_estoque)
        self.session.commit()
        self.session.refresh(item_estoque)
        return item_estoque

    def obter_por_servidor_e_item(self, servidor_id: int, item_id: int) -> Optional[EstoqueLojaItemModel]:
        return self.session.query(EstoqueLojaItemModel).filter_by(servidor_id=servidor_id, item_id=item_id).first()

    def listar_por_servidor(self, servidor_id: int) -> List[EstoqueLojaItemModel]:
        return self.session.query(EstoqueLojaItemModel).filter_by(servidor_id=servidor_id).all()

    def atualizar(self, item_estoque: EstoqueLojaItemModel) -> EstoqueLojaItemModel:
        self.session.commit()
        self.session.refresh(item_estoque)
        return item_estoque

    def remover(self, item_estoque: EstoqueLojaItemModel) -> None:
        self.session.delete(item_estoque)
        self.session.commit()

    def remover_por_servidor_e_item(self, servidor_id: int, item_id: int) -> bool:
        item = self.obter_por_servidor_e_item(servidor_id, item_id)
        if item:
            self.remover(item)
            return True
        return False

    def limpar_estoque_servidor(self, servidor_id: int) -> None:
        """Remove todos os itens do estoque de um servidor específico."""
        self.session.query(EstoqueLojaItemModel).filter_by(servidor_id=servidor_id).delete()
        self.session.commit()
