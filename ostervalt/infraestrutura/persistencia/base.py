from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Database:
    def __init__(self, db_url: str = "sqlite:///ostervalt/dados/ostervalt.db"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def criar_tabelas(self):
        Base.metadata.create_all(bind=self.engine)