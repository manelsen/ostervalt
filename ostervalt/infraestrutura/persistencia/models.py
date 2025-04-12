from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class PersonagemModel(Base):
    __tablename__ = "personagens"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    usuario_id = Column(Integer, nullable=False)
    servidor_id = Column(Integer, nullable=False)
    marcos = Column(Integer, default=0)
    dinheiro = Column(Integer, default=0)
    nivel = Column(Integer, default=1)
    ultimo_trabalho = Column(DateTime)
    ultimo_crime = Column(DateTime)

    inventario = relationship("ItemInventarioModel", back_populates="personagem")

class ItemModel(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    raridade = Column(String, nullable=False)
    valor = Column(Integer, nullable=False)
    descricao = Column(String)

class ItemInventarioModel(Base):
    __tablename__ = "itens_inventario"

    id = Column(Integer, primary_key=True, index=True)
    personagem_id = Column(Integer, ForeignKey("personagens.id"))
    item_id = Column(Integer, ForeignKey("itens.id"))
    quantidade = Column(Integer, default=1)

    personagem = relationship("PersonagemModel", back_populates="inventario")
    item = relationship("ItemModel")