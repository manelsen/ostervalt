from typing import List, Optional
from sqlalchemy.orm import Session
from nucleo.entidades.item import Item
from nucleo.repositorios import RepositorioItens
from .models import ItemModel
from .base import Database

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
    def __init__(self, database: Database):
        self.db = database

    def obter_por_id(self, item_id: int) -> Optional[Item]:
        db = self.db.SessionLocal()
        try:
            model = db.query(ItemModel).filter(ItemModel.id == item_id).first()
            return _para_entidade_item(model) if model else None
        finally:
            db.close()

    def listar_todos(self) -> List[Item]:
        db = self.db.SessionLocal()
        try:
            modelos = db.query(ItemModel).all()
            return [_para_entidade_item(model) for model in modelos]
        finally:
            db.close()

    def adicionar(self, item: Item) -> None:
        db = self.db.SessionLocal()
        try:
            model = _para_modelo_item(item)
            db.add(model)
            db.commit()
            db.refresh(model)
            item.id = model.id
        finally:
            db.close()

    def atualizar(self, item: Item) -> None:
        db = self.db.SessionLocal()
        try:
            model = db.query(ItemModel).filter(ItemModel.id == item.id).first()
            if model:
                model.nome = item.nome
                model.raridade = item.raridade
                model.valor = item.valor
                model.descricao = item.descricao
                db.commit()
        finally:
            db.close()

    def remover(self, item_id: int) -> None:
        db = self.db.SessionLocal()
        try:
            model = db.query(ItemModel).filter(ItemModel.id == item_id).first()
            if model:
                db.delete(model)
                db.commit()
        finally:
            db.close()