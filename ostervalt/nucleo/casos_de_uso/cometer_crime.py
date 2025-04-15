import datetime
import random
from ostervalt.nucleo.repositorios import RepositorioPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.nucleo.utilitarios import verificar_cooldown, executar_logica_crime
from ostervalt.infraestrutura.configuracao.configuracao import Configuracao # Importa a classe do módulo
from .dtos import ResultadoCrimeDTO

class CometerCrime:
    def __init__(self, repositorio_personagens: RepositorioPersonagens, configuracao: Configuracao):
        self.repositorio_personagens = repositorio_personagens
        self.configuracao = configuracao

    def executar(self, personagem_id: int, tempo_atual=None) -> ResultadoCrimeDTO: # Adicionado tempo_atual como argumento opcional
        personagem = self.repositorio_personagens.obter_por_id(personagem_id)
        if not personagem:
            raise ValueError(f"Personagem com ID {personagem_id} não encontrado.")

        intervalo_crime = self.configuracao.obter("limites").get("intervalo_crime")
        ultimo_crime = personagem.ultimo_crime
        if tempo_atual is None: # Se tempo_atual não foi passado, usa datetime.now()
            tempo_atual = datetime.datetime.now()

        if not verificar_cooldown(ultimo_crime, intervalo_crime, tempo_atual): # Passar tempo_atual posicionalmente
            delta = tempo_atual - ultimo_crime # Calcular delta aqui
            tempo_restante = intervalo_crime - delta.total_seconds()
            tempo_restante_formatado = datetime.timedelta(seconds=tempo_restante)
            raise ValueError(f"Ação de crime está em cooldown. Tempo restante: {tempo_restante_formatado}.") # Melhorar mensagem de erro

        probabilidade_crime = self.configuracao.obter("probabilidades").get("crime") or 50 # Default probability
        ganho_min_crime = 100
        ganho_max_crime = 500
        perda_min_crime = 50
        perda_max_crime = 250

        crime_bem_sucedido, resultado_financeiro = executar_logica_crime(
            probabilidade_crime, ganho_min_crime, ganho_max_crime, perda_min_crime, perda_max_crime
        )

        personagem.dinheiro += resultado_financeiro
        personagem.ultimo_crime = tempo_atual
        self.repositorio_personagens.atualizar(personagem) # Assuming 'atualizar' method exists

        mensagens_crime = self.configuracao.obter("messages").get("crime") or ["Você tentou cometer um crime..."]
        mensagem_base = random.choice(mensagens_crime)

        if crime_bem_sucedido:
            mensagem_resultado = f"{mensagem_base}\nSucesso! Você ganhou {resultado_financeiro} moedas."
        else:
            mensagem_resultado = f"{mensagem_base}\nVocê foi pego! Perdeu {abs(resultado_financeiro)} moedas."

        mensagem_final = f"{mensagem_resultado}\nSaldo atual: {personagem.dinheiro} moedas."

        return ResultadoCrimeDTO(
            personagem=personagem,
            mensagem=mensagem_final,
            sucesso=crime_bem_sucedido,
            resultado_financeiro=resultado_financeiro
        )