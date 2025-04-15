from typing import List, Optional
from sqlalchemy.orm import Session
from ostervalt.nucleo.entidades.item import Item
from ostervalt.nucleo.repositorios import RepositorioItens
from .models import ItemModel
# from .base import Database # Removido

def _para_entidade_item(model: ItemModel) -> Item:
    return Item(
        id=model.id,
        nome=model.nome,
        raridade=model.raridade,
        valor=model.valor,
        descricao=model.descricao
    )

def _para_modelo_item(item: Item) -> ItemModel:
    return ItemModel(
        id=item.id,
        nome=item.nome,
        raridade=item.raridade,
        valor=item.valor,
        descricao=item.descricao
    )

class RepositorioItensSQLAlchemy(RepositorioItens):
    def __init__(self, session: Session): # Modificado para receber Session
        self.session = session # Modificado para usar self.session

    def obter_por_id(self, item_id: int) -> Optional[Item]:
        # Removido db = self.db.SessionLocal() e try/finally
        model = self.session.query(ItemModel).filter(ItemModel.id == item_id).first() # Usa self.session
        return _para_entidade_item(model) if model else None

    def listar_todos(self) -> List[Item]: # Adicionado método que faltava na interface? (Verificar repositorios.py)
        # Removido db = self.db.SessionLocal() e try/finally
        modelos = self.session.query(ItemModel).all() # Usa self.session
        return [_para_entidade_item(model) for model in modelos]

    def listar_por_raridade(self, raridade: str) -> List[Item]:
        # Removido db = self.db.SessionLocal() e try/finally
        modelos = self.session.query(ItemModel).filter(ItemModel.raridade == raridade).all() # Usa self.session
        return [_para_entidade_item(modelo) for modelo in modelos]

    def adicionar(self, item: Item) -> None:
        # Removido db = self.db.SessionLocal() e try/finally
        model = _para_modelo_item(item)
        self.session.add(model) # Usa self.session
        self.session.commit() # Usa self.session
        self.session.refresh(model) # Usa self.session
        item.id = model.id

    def atualizar(self, item: Item) -> None:
        # Removido db = self.db.SessionLocal() e try/finally
        model = self.session.query(ItemModel).filter(ItemModel.id == item.id).first() # Usa self.session
        if model:
            model.nome = item.nome
            model.raridade = item.raridade
            model.valor = item.valor
            model.descricao = item.descricao
            self.session.commit() # Usa self.session

    def remover(self, item_id: int) -> None:
        # Removido db = self.db.SessionLocal() e try/finally
        model = self.session.query(ItemModel).filter(ItemModel.id == item_id).first() # Usa self.session
        if model:
            self.session.delete(model) # Usa self.session
            self.session.commit() # Usa self.session

    # Método adicional não presente na interface RepositorioItens, mas usado em AdminCog
    def obter_por_nome(self, nome: str) -> Optional[Item]:
        model = self.session.query(ItemModel).filter(ItemModel.nome == nome).first()
        return _para_entidade_item(model) if model else None