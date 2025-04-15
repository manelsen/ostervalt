from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from .models import ItemInventarioModel # Adicionado
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.nucleo.repositorios import RepositorioPersonagens
from .models import PersonagemModel
# from .base import Database # Removido - Não precisamos mais de Database aqui

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
        ultimo_crime=model.ultimo_crime,
        status=model.status # Adicionado
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
        ultimo_crime=personagem.ultimo_crime,
        status=personagem.status # Adicionado
    )


def _para_dict_backup(model: PersonagemModel) -> dict:
    """Converte um PersonagemModel (com inventário carregado) para um dict para backup."""
    inventario_formatado = [
        {"item_id": item_inv.item_id, "quantidade": item_inv.quantidade}
        for item_inv in model.inventario # Assume que inventario foi pré-carregado
    ]
    return {
        "id": model.id,
        "nome": model.nome,
        "usuario_id": model.usuario_id,
        "servidor_id": model.servidor_id,
        "marcos": model.marcos,
        "dinheiro": model.dinheiro,
        "nivel": model.nivel,
        "ultimo_trabalho": model.ultimo_trabalho.isoformat() if model.ultimo_trabalho else None,
        "ultimo_crime": model.ultimo_crime.isoformat() if model.ultimo_crime else None,
        "status": model.status.value if model.status else None, # Usar .value para o enum
        "inventario": inventario_formatado
    }


class RepositorioPersonagensSQLAlchemy(RepositorioPersonagens):
    def __init__(self, session: Session): # Modificado para receber Session
        self.session = session # Modificado para usar self.session

    def obter_por_id(self, personagem_id: int) -> Optional[Personagem]:
        # Removido db = self.db.SessionLocal() e try/finally
        model = self.session.query(PersonagemModel).filter(PersonagemModel.id == personagem_id).first() # Usa self.session
        return _para_entidade_personagem(model) if model else None

    def listar_por_usuario(self, usuario_id: int, servidor_id: int) -> List[Personagem]:
        # Removido db = self.db.SessionLocal() e try/finally
        modelos = self.session.query(PersonagemModel).filter( # Usa self.session
            PersonagemModel.usuario_id == usuario_id,
            PersonagemModel.servidor_id == servidor_id
        ).all()
        return [_para_entidade_personagem(model) for model in modelos]

    def adicionar(self, personagem: Personagem) -> None:
        # Removido db = self.db.SessionLocal() e try/finally
        model = _para_modelo_personagem(personagem)
        self.session.add(model) # Usa self.session
        self.session.commit() # Usa self.session
        self.session.refresh(model) # Usa self.session
        personagem.id = model.id

    def atualizar(self, personagem: Personagem) -> None:
        # Removido db = self.db.SessionLocal() e try/finally
        model = self.session.query(PersonagemModel).filter(PersonagemModel.id == personagem.id).first() # Usa self.session
        if model:
            model.nome = personagem.nome
            model.marcos = personagem.marcos
            model.dinheiro = personagem.dinheiro
            model.nivel = personagem.nivel
            model.ultimo_trabalho = personagem.ultimo_trabalho
            model.ultimo_crime = personagem.ultimo_crime
            model.status = personagem.status # Adicionado
            self.session.commit() # Usa self.session

    def remover(self, personagem_id: int) -> None:
        # Removido db = self.db.SessionLocal() e try/finally
        model = self.session.query(PersonagemModel).filter(PersonagemModel.id == personagem_id).first() # Usa self.session
        if model:
            self.session.delete(model) # Usa self.session
            self.session.commit() # Usa self.session

    def listar_por_servidor_para_backup(self, servidor_id: int) -> List[dict]:
        """Lista todos os personagens de um servidor com seus inventários para backup."""
        # Removido db = self.db.SessionLocal() e try/finally
        modelos = self.session.query(PersonagemModel).filter( # Usa self.session
            PersonagemModel.servidor_id == servidor_id
        ).options(
            joinedload(PersonagemModel.inventario) # Carrega o inventário junto
            # joinedload(PersonagemModel.inventario).joinedload(ItemInventarioModel.item) # Opcional: carregar detalhes do item se necessário, mas para backup só precisamos do ID
        ).all()
        return [_para_dict_backup(model) for model in modelos]
