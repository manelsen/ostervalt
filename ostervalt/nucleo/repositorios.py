from abc import ABC, abstractmethod
from typing import List, Optional
from .entidades.usuario import Usuario
from .entidades.transacao import Transacao
# from .entidades.relatorio import Relatorio # Removido - Entidade não encontrada
from .entidades.personagem import Personagem
from .entidades.item import Item, ItemInventario

class RepositorioPersonagens(ABC):
    @abstractmethod
    def obter_por_id(self, personagem_id: int) -> Optional[Personagem]:
        """Obtém um personagem pelo ID."""
        pass

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int, servidor_id: int) -> List[Personagem]:
        """Lista todos os personagens de um usuário em um servidor."""
        pass

    @abstractmethod
    def adicionar(self, personagem: Personagem) -> None:
        """Adiciona um novo personagem ao repositório."""
        pass

    @abstractmethod
    def atualizar(self, personagem: Personagem) -> None:
        """Atualiza os dados de um personagem existente."""
        pass

    @abstractmethod
    def remover(self, personagem_id: int) -> None:
        """Remove um personagem pelo ID."""
        pass

class RepositorioItens(ABC):
    @abstractmethod
    def obter_por_id(self, item_id: int) -> Optional[Item]:
        """Obtém um item pelo ID."""
        pass

    @abstractmethod
    def listar_por_raridade(self, raridade: str) -> List[Item]:
        """Lista itens por raridade."""
        pass

    @abstractmethod
    def adicionar(self, item: Item) -> None:
        """Adiciona um novo item ao repositório."""
        pass

    @abstractmethod
    def atualizar(self, item: Item) -> None:
        """Atualiza os dados de um item existente."""
        pass

class RepositorioInventario(ABC):
    @abstractmethod
    def obter_itens(self, personagem_id: int) -> List[ItemInventario]:
        """Obtém todos os itens no inventário de um personagem."""
        pass

    @abstractmethod
    def adicionar_item(self, item_inventario: ItemInventario) -> None:
        """Adiciona um item ao inventário do personagem."""
        pass

    @abstractmethod
    def remover_item(self, item_id: int, personagem_id: int) -> None:
        """Remove um item do inventário do personagem."""
        pass

    @abstractmethod
    def atualizar_quantidade(self, item_id: int, personagem_id: int, quantidade: int) -> None:
        """Atualiza a quantidade de um item no inventário."""
        pass
class RepositorioUsuarios(ABC):
    @abstractmethod
    def obter_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """Obtém um usuário pelo ID."""
        pass

    @abstractmethod
    def obter_por_email(self, email: str) -> Optional[Usuario]:
        """Obtém um usuário pelo email."""
        pass

    @abstractmethod
    def adicionar(self, usuario: Usuario) -> None:
        """Adiciona um novo usuário ao repositório."""
        pass

    @abstractmethod
    def atualizar(self, usuario: Usuario) -> None:
        """Atualiza os dados de um usuário existente."""
        pass

    @abstractmethod
    def remover(self, usuario_id: int) -> None:
        """Remove um usuário pelo ID."""
        pass

class RepositorioTransacoes(ABC):
    @abstractmethod
    def registrar_transacao(self, transacao: Transacao) -> None:
        """Registra uma nova transação financeira."""
        pass

    @abstractmethod
    def obter_historico(self, usuario_id: int, limite: int = 100) -> List[Transacao]:
        """Obtém o histórico de transações de um usuário."""
        pass

    @abstractmethod
    def reverter_transacao(self, transacao_id: int) -> None:
        """Reverte uma transação específica."""
        pass

class RepositorioRelatorios(ABC):
    @abstractmethod
    def gerar_relatorio_financeiro(self, periodo: str): # -> Relatorio: # Removido Type Hint - Entidade não encontrada
        """Gera um relatório financeiro consolidado para o período especificado."""
        pass

    @abstractmethod
    def gerar_relatorio_atividade(self, usuario_id: int): # -> Relatorio: # Removido Type Hint - Entidade não encontrada
        """Gera um relatório de atividade detalhado para um usuário."""
        pass