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