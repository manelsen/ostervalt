import datetime

from dataclasses import dataclass
from ostervalt.nucleo.entidades.personagem import Personagem

@dataclass
class ResultadoTrabalhoDTO:
    """
    Data Transfer Object para o resultado do caso de uso RealizarTrabalho.
    """
    personagem: Personagem
    mensagem: str
    recompensa: int

@dataclass
class ResultadoCrimeDTO:
    """
    Data Transfer Object para o resultado do caso de uso CometerCrime.
    """
    personagem: Personagem
    mensagem: str
    sucesso: bool
    resultado_financeiro: int

@dataclass
class ItemDTO:
    """Data Transfer Object para um item."""
    id: int
    nome: str
    descricao: str
    raridade: str
    valor: int

@dataclass
class ListaItensDTO:
    """Data Transfer Object para uma lista de itens."""
    itens: list[ItemDTO]

@dataclass
class ComandoDTO:
    """Data Transfer Object genérico para entrada de comandos."""
    discord_id: int
    parametros: dict | None = None # Parâmetros específicos do comando

# --- DTOs de Resultado Específicos ---

@dataclass
class ItemInventarioDTO:
    """DTO para um item dentro do inventário."""
    item_id: int
    nome_item: str
    quantidade: int
    descricao_item: str | None = None

@dataclass
class InventarioDTO:
    """DTO para o resultado do caso de uso ListarInventario."""
    nome_personagem: str
    itens: list[ItemInventarioDTO]

@dataclass
class PersonagemDTO:
    """DTO para informações de um personagem."""
    id: int
    nome: str
    nivel: int
    dinheiro: int
    experiencia: int = 0 # Valor padrão
    experiencia_necessaria: int = 100 # Valor padrão
    energia: int = 100 # Valor padrão
    energia_maxima: int = 100 # Valor padrão
    vida: int = 100 # Valor padrão
    vida_maxima: int = 100 # Valor padrão
    criado_em: datetime.datetime | None = None # Valor padrão

@dataclass
class ListaPersonagensDTO:
    """DTO para o resultado do caso de uso ListarPersonagens."""
    personagens: list[PersonagemDTO]