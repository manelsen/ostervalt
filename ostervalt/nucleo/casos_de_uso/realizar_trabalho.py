import datetime
import random
from ostervalt.nucleo.repositorios import RepositorioPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.nucleo.utilitarios import verificar_cooldown, calcular_recompensa_trabalho
from ostervalt.infraestrutura.configuracao import Configuracao  # Assuming config is injected
from .dtos import ResultadoTrabalhoDTO

class RealizarTrabalho:
    def __init__(self, repositorio_personagens: RepositorioPersonagens, configuracao: Configuracao):
        self.repositorio_personagens = repositorio_personagens
        self.configuracao = configuracao

    def executar(self, personagem_id: int) -> ResultadoTrabalhoDTO:
        personagem = self.repositorio_personagens.obter_por_id(personagem_id)
        if not personagem:
            raise ValueError(f"Personagem com ID {personagem_id} não encontrado.")

        intervalo_trabalhar = self.configuracao.obter("limites").get("intervalo_trabalhar")
        ultimo_tempo_trabalho = personagem.ultimo_tempo_trabalho
        tempo_atual = datetime.datetime.now()

        if not verificar_cooldown(ultimo_tempo_trabalho, intervalo_trabalhar, tempo_atual):
            tempo_restante = intervalo_trabalhar - delta.total_seconds()
            tempo_restante_formatado = datetime.timedelta(seconds=tempo_restante)
            raise ValueError(f"Ação de trabalho está em cooldown. Tempo restante: {tempo_restante_formatado}.") # Melhorar mensagem de erro

        nivel_personagem = personagem.nivel
        tiers_config = self.configuracao.obter("tiers")
        recompensa = calcular_recompensa_trabalho(nivel_personagem, tiers_config)

        personagem.dinheiro += recompensa
        personagem.ultimo_tempo_trabalho = tempo_atual
        self.repositorio_personagens.atualizar(personagem) # Assuming 'atualizar' method exists

        mensagens_trabalho = self.configuracao.obter("messages").get("trabalho") or ["Você trabalhou duro e ganhou sua recompensa!"]
        mensagem = random.choice(mensagens_trabalho)

        mensagem_final = f"{mensagem}\nVocê ganhou {recompensa} moedas. Saldo atual: {personagem.dinheiro} moedas."

        return ResultadoTrabalhoDTO(
            personagem=personagem,
            mensagem=mensagem_final,
            recompensa=recompensa
        )