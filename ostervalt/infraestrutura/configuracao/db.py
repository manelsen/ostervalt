# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from ostervalt.infraestrutura.persistencia.base import Base # Importa a Base dos modelos

load_dotenv()

# Carrega a URL do banco de dados do .env ou usa um padrão SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ostervalt.db")

# Configuração do SQLAlchemy
# echo=True para logar queries SQL (útil para debug)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}, echo=False)

# Cria uma fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def criar_tabelas():
    """Cria todas as tabelas no banco de dados definidas nos modelos."""
    print("Criando tabelas no banco de dados (se não existirem)...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas verificadas/criadas.")

def get_session() -> Session:
    """Retorna uma nova sessão do banco de dados."""
    return SessionLocal()

# Você pode chamar criar_tabelas() uma vez na inicialização do seu app,
# por exemplo, no ostervalt.py antes de iniciar o bot.
# criar_tabelas()