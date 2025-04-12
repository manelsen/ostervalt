# -*- coding: utf-8 -*-
from ostervalt.infraestrutura.configuracao.db import get_session

# Importar Repositórios
from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
from ostervalt.infraestrutura.persistencia.repositorio_itens import RepositorioItensSQLAlchemy
from ostervalt.infraestrutura.persistencia.repositorio_inventario import RepositorioInventarioSQLAlchemy

# Importar Casos de Uso
from ostervalt.nucleo.casos_de_uso.criar_personagem import CriarPersonagem
from ostervalt.nucleo.casos_de_uso.obter_personagem import ObterPersonagem
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens
from ostervalt.nucleo.casos_de_uso.realizar_trabalho import RealizarTrabalho
from ostervalt.nucleo.casos_de_uso.cometer_crime import CometerCrime
from ostervalt.nucleo.casos_de_uso.listar_inventario import ListarInventario
from ostervalt.nucleo.casos_de_uso.adicionar_item_inventario import AdicionarItemInventario
from ostervalt.nucleo.casos_de_uso.remover_item_inventario import RemoverItemInventario
from ostervalt.nucleo.casos_de_uso.obter_item import ObterItem
from ostervalt.nucleo.casos_de_uso.listar_itens import ListarItens

class Container:
    """Container simples para injeção de dependência."""
    def __init__(self):
        self._servicos = {}

    def registrar(self, nome: str, instancia):
        """Registra uma instância de serviço no container."""
        self._servicos[nome] = instancia

    def resolve(self, nome: str):
        """Resolve (retorna) uma instância de serviço pelo nome."""
        try:
            return self._servicos[nome]
        except KeyError:
            raise ValueError(f"Serviço '{nome}' não encontrado no container.")

def configurar_container() -> Container:
    """Configura e retorna o container de injeção de dependência."""
    container = Container()

    # --- Sessão do Banco de Dados (Fábrica) ---
    # Registra a função que obtém a sessão, não a sessão em si,
    # para garantir uma nova sessão por requisição/operação se necessário.
    # No contexto do bot, podemos passar a mesma sessão para todos os repositórios
    # dentro de um mesmo comando, mas obter uma nova sessão a cada comando.
    # Por simplicidade aqui, vamos registrar a função get_session.
    # Os repositórios podem chamar container.resolve('db_session_factory')()
    # Ou podemos instanciar a sessão aqui e passá-la diretamente.
    # Vamos optar pela segunda abordagem por simplicidade inicial no bot.
    db_session = get_session()
    container.registrar('db_session', db_session) # Registra a sessão atual

    # --- Repositórios ---
    repo_personagens = RepositorioPersonagensSQLAlchemy(db_session)
    repo_itens = RepositorioItensSQLAlchemy(db_session)
    repo_inventario = RepositorioInventarioSQLAlchemy(db_session)

    container.registrar('repo_personagens', repo_personagens)
    container.registrar('repo_itens', repo_itens)
    container.registrar('repo_inventario', repo_inventario)

    # --- Casos de Uso ---
    container.registrar('criar_personagem_uc', CriarPersonagem(repo_personagens))
    container.registrar('obter_personagem_uc', ObterPersonagem(repo_personagens))
    container.registrar('listar_personagens_uc', ListarPersonagens(repo_personagens))
    container.registrar('realizar_trabalho_uc', RealizarTrabalho(repo_personagens)) # Pode precisar de outros repos no futuro
    container.registrar('cometer_crime_uc', CometerCrime(repo_personagens)) # Pode precisar de outros repos no futuro
    container.registrar('listar_inventario_uc', ListarInventario(repo_inventario, repo_personagens))
    container.registrar('adicionar_item_inventario_uc', AdicionarItemInventario(repo_inventario, repo_itens, repo_personagens)) # Ajustado para incluir repo_personagens
    container.registrar('remover_item_inventario_uc', RemoverItemInventario(repo_inventario, repo_personagens)) # Ajustado para incluir repo_personagens
    container.registrar('obter_item_uc', ObterItem(repo_itens))
    container.registrar('listar_itens_uc', ListarItens(repo_itens))

    print("Container de injeção de dependência configurado.")
    return container

# Exemplo de uso (não executado aqui):
# if __name__ == "__main__":
#     meu_container = configurar_container()
#     criar_uc = meu_container.resolve('criar_personagem_uc')
#     # ... usar o caso de uso