from typing import List, Optional
from sqlalchemy.orm import Session
from nucleo.entidades.inventario_item import InventarioItem
from nucleo.repositorios import RepositorioInventario
from .models import ItemInventarioModel, PersonagemModel, ItemModel
from .base import Database

def _para_entidade_inventario_item(model: ItemInventarioModel) -> InventarioItem:
    return InventarioItem(
        id=model.id,
        personagem_id=model.personagem_id,
        item_id=model.item_id,
        quantidade=model.quantidade
    )

def _para_modelo_inventario_item(inventario_item: InventarioItem) -> ItemInventarioModel:
    return ItemInventarioModel(
        id=inventario_item.id,
        personagem_id=inventario_item.personagem_id,
        item_id=inventario_item.item_id,
        quantidade=inventario_item.quantidade
    )

class RepositorioInventarioSQLAlchemy(RepositorioInventario):
    def __init__(self, database: Database):
        self.db = database

    def obter_por_id(self, inventario_item_id: int) -> Optional[InventarioItem]:
        db = self.db.SessionLocal()
        try:
            model = db.query(ItemInventarioModel).filter(ItemInventarioModel.id == inventario_item_id).first()
            return _para_entidade_inventario_item(model) if model else None
        finally:
            db.close()

    def listar_por_personagem(self, personagem_id: int) -> List[InventarioItem]:
        db = self.db.SessionLocal()
        try:
            modelos = db.query(ItemInventarioModel).filter(ItemInventarioModel.personagem_id == personagem_id).all()
            return [_para_entidade_inventario_item(modelo) for modelo in modelos]
        finally:
            db.close()

    def adicionar(self, inventario_item: InventarioItem) -> None:
        db = self.db.SessionLocal()
        try:
            model = _para_modelo_inventario_item(inventario_item)
            db.add(model)
            db.commit()
            db.refresh(model)
            inventario_item.id = model.id
        finally:
            db.close()

    def atualizar(self, inventario_item: InventarioItem) -> None:
        db = self.db.SessionLocal()
        try:
            model = db.query(ItemInventarioModel).filter(ItemInventarioModel.id == inventario_item.id).first()
            if model:
                model.personagem_id = inventario_item.personagem_id
                model.item_id = inventario_item.item_id
                model.quantidade = inventario_item.quantidade
                db.commit()
        finally:
            db.close()

    def remover(self, inventario_item_id: int) -> None:
        db = self.db.SessionLocal()
        try:
            model = db.query(ItemInventarioModel).filter(ItemInventarioModel.id == inventario_item_id).first()
            if model:
                db.delete(model)
                db.commit()
        finally:
            db.close()

    def remover_por_personagem(self, personagem_id: int) -> None:
        db = self.db.SessionLocal()
        try:
            modelos = db.query(ItemInventarioModel).filter(ItemInventarioModel.personagem_id == personagem_id).all()
            for model in modelos:
                db.delete(model)
            db.commit()
        finally:
            db.close()