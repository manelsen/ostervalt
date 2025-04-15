import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from sqlalchemy.orm import relationship
from .base import Base


class StatusPersonagem(enum.Enum):
    ATIVO = "ativo"
    APOSENTADO = "aposentado"

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
    status = Column(Enum(StatusPersonagem), default=StatusPersonagem.ATIVO, nullable=False, server_default=StatusPersonagem.ATIVO.value)

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


class EstoqueLojaItemModel(Base):
    __tablename__ = "estoque_loja"
    __table_args__ = (UniqueConstraint('servidor_id', 'item_id', name='_servidor_item_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    servidor_id = Column(Integer, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("itens.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_especifico = Column(Integer, nullable=True) # Preço pode ser diferente do padrão do item

    item = relationship("ItemModel")


class ConfiguracaoServidorModel(Base):
    __tablename__ = "configuracoes_servidor"
    __table_args__ = (UniqueConstraint('servidor_id', 'chave', name='_servidor_chave_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    servidor_id = Column(Integer, nullable=False, index=True)
    chave = Column(String, nullable=False) # Ex: 'cargo_saldo', 'msg_trabalho', 'prob_crime'
    valor = Column(String, nullable=False) # Armazena como string, conversão na aplicação
