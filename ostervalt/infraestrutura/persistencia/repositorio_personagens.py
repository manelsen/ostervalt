from typing import List, Optional
from sqlalchemy.orm import Session
from nucleo.entidades.personagem import Personagem
from nucleo.repositorios import RepositorioPersonagens
from .models import PersonagemModel
from .base import Database

def _para_entidade_personagem(model: PersonagemModel) -> Personagem:
    return Personagem(
        id=model.id,
        nome=model.nome,
        usuario_id=model.usuario_id,
        servidor_id=model.servidor_id,
        marcos=model.marcos,
        dinheiro=model.dinheiro,
        nivel=model.nivel,
        ultimo_trabalho=model.ultimo_trabalho,
        ultimo_crime=model.ultimo_crime
    )

def _para_modelo_personagem(personagem: Personagem) -> PersonagemModel:
    return PersonagemModel(
        id=personagem.id,
        nome=personagem.nome,
        usuario_id=personagem.usuario_id,
        servidor_id=personagem.servidor_id,
        marcos=personagem.marcos,
        dinheiro=personagem.dinheiro,
        nivel=personagem.nivel,
        ultimo_trabalho=personagem.ultimo_trabalho,
        ultimo_crime=personagem.ultimo_crime
    )

class RepositorioPersonagensSQLAlchemy(RepositorioPersonagens):
    def __init__(self, database: Database):
        self.db = database

    def obter_por_id(self, personagem_id: int) -> Optional[Personagem]:
        db = self.db.SessionLocal()
        try:
            model = db.query(PersonagemModel).filter(PersonagemModel.id == personagem_id).first()
            return _para_entidade_personagem(model) if model else None
        finally:
            db.close()

    def listar_por_usuario(self, usuario_id: int, servidor_id: int) -> List[Personagem]:
        db = self.db.SessionLocal()
        try:
            modelos = db.query(PersonagemModel).filter(
                PersonagemModel.usuario_id == usuario_id,
                PersonagemModel.servidor_id == servidor_id
            ).all()
            return [_para_entidade_personagem(model) for model in modelos]
        finally:
            db.close()

    def adicionar(self, personagem: Personagem) -> None:
        db = self.db.SessionLocal()
        try:
            model = _para_modelo_personagem(personagem)
            db.add(model)
            db.commit()
            db.refresh(model)
            personagem.id = model.id
        finally:
            db.close()

    def atualizar(self, personagem: Personagem) -> None:
        db = self.db.SessionLocal()
        try:
            model = db.query(PersonagemModel).filter(PersonagemModel.id == personagem.id).first()
            if model:
                model.nome = personagem.nome
                model.marcos = personagem.marcos
                model.dinheiro = personagem.dinheiro
                model.nivel = personagem.nivel
                model.ultimo_trabalho = personagem.ultimo_trabalho
                model.ultimo_crime = personagem.ultimo_crime
                db.commit()
        finally:
            db.close()

    def remover(self, personagem_id: int) -> None:
        db = self.db.SessionLocal()
        try:
            model = db.query(PersonagemModel).filter(PersonagemModel.id == personagem_id).first()
            if model:
                db.delete(model)
                db.commit()
        finally:
            db.close()