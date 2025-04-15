from typing import List, Optional
from sqlalchemy.orm import Session
from ostervalt.infraestrutura.persistencia.models import ItemInventarioModel as InventarioItemEntity # Renomeado alias para clareza
from ostervalt.nucleo.repositorios import RepositorioInventario
from ostervalt.nucleo.entidades.item import ItemInventario # Importar entidade do núcleo
from .models import ItemInventarioModel, PersonagemModel, ItemModel
# from .base import Database # Removido

def _para_entidade_inventario_item(model: ItemInventarioModel) -> ItemInventario: # Retorna entidade do núcleo
    return ItemInventario(
        id=model.id,
        personagem_id=model.personagem_id,
        item_id=model.item_id,
        quantidade=model.quantidade
    )

def _para_modelo_inventario_item(inventario_item: ItemInventario) -> ItemInventarioModel: # Recebe entidade do núcleo
    return ItemInventarioModel(
        id=inventario_item.id,
        personagem_id=inventario_item.personagem_id,
        item_id=inventario_item.item_id,
        quantidade=inventario_item.quantidade
    )

class RepositorioInventarioSQLAlchemy(RepositorioInventario):
    def __init__(self, session: Session): # Modificado para receber Session
        self.session = session # Modificado para usar self.session

    # Métodos internos que retornam Modelos (usados por outros métodos aqui)
    def _obter_modelo_por_id(self, inventario_item_id: int) -> Optional[ItemInventarioModel]:
        return self.session.query(ItemInventarioModel).filter(ItemInventarioModel.id == inventario_item_id).first()

    def _listar_modelos_por_personagem(self, personagem_id: int) -> List[ItemInventarioModel]:
        return self.session.query(ItemInventarioModel).filter(ItemInventarioModel.personagem_id == personagem_id).all()

    def _obter_modelo_por_item_e_personagem(self, item_id: int, personagem_id: int) -> Optional[ItemInventarioModel]:
         return self.session.query(ItemInventarioModel).filter(
             ItemInventarioModel.item_id == item_id,
             ItemInventarioModel.personagem_id == personagem_id
         ).first()

    # --- Implementação da Interface RepositorioInventario ---

    def obter_itens(self, personagem_id: int) -> List[ItemInventario]:
        modelos = self._listar_modelos_por_personagem(personagem_id)
        return [_para_entidade_inventario_item(modelo) for modelo in modelos]

    def adicionar_item(self, item_inventario: ItemInventario) -> None:
        # Verificar se já existe um item igual no inventário para atualizar a quantidade
        modelo_existente = self._obter_modelo_por_item_e_personagem(item_inventario.item_id, item_inventario.personagem_id)
        if modelo_existente:
            modelo_existente.quantidade += item_inventario.quantidade
            self.session.commit()
            # Atualizar ID no objeto entidade se necessário (embora não seja comum para adicionar)
            item_inventario.id = modelo_existente.id
        else:
            # Adicionar novo item
            model = _para_modelo_inventario_item(item_inventario)
            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
            item_inventario.id = model.id # Atualiza o ID no objeto entidade

    def remover_item(self, item_id: int, personagem_id: int) -> None:
        model = self._obter_modelo_por_item_e_personagem(item_id, personagem_id)
        if model:
            self.session.delete(model)
            self.session.commit()

    def atualizar_quantidade(self, item_id: int, personagem_id: int, quantidade: int) -> None:
        model = self._obter_modelo_por_item_e_personagem(item_id, personagem_id)
        if model:
            if quantidade > 0:
                model.quantidade = quantidade
                self.session.commit()
            else: # Se quantidade for 0 ou menos, remover o item
                self.remover_item(item_id, personagem_id)

    # --- Métodos Adicionais (não na interface, podem ser úteis internamente ou removidos) ---

    # def obter_por_id(self, inventario_item_id: int) -> Optional[ItemInventarioModel]: # Retorna Modelo, não Entidade
    #     return self._obter_modelo_por_id(inventario_item_id)

    # def listar_por_personagem(self, personagem_id: int) -> List[ItemInventarioModel]: # Retorna Modelos
    #     return self._listar_modelos_por_personagem(personagem_id)

    # def adicionar(self, inventario_item: ItemInventario) -> None: # Redundante com adicionar_item
    #     model = _para_modelo_inventario_item(inventario_item)
    #     self.session.add(model)
    #     self.session.commit()
    #     self.session.refresh(model)
    #     inventario_item.id = model.id

    # def atualizar(self, inventario_item: ItemInventario) -> None: # Usar atualizar_quantidade
    #     model = self._obter_modelo_por_id(inventario_item.id)
    #     if model:
    #         model.personagem_id = inventario_item.personagem_id
    #         model.item_id = inventario_item.item_id
    #         model.quantidade = inventario_item.quantidade
    #         self.session.commit()

    # def remover(self, inventario_item_id: int) -> None: # Usar remover_item
    #     model = self._obter_modelo_por_id(inventario_item_id)
    #     if model:
    #         self.session.delete(model)
    #         self.session.commit()

    def remover_por_personagem(self, personagem_id: int) -> None:
        # Este método pode ser útil, mantém
        modelos = self._listar_modelos_por_personagem(personagem_id)
        for model in modelos:
            self.session.delete(model)
        self.session.commit()