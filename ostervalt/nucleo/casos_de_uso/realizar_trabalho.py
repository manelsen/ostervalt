import datetime
import random
from ostervalt.nucleo.repositorios import RepositorioPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.nucleo.utilitarios import verificar_cooldown, calcular_recompensa_trabalho
from ostervalt.infraestrutura.configuracao.configuracao import Configuracao  # Importa a classe do módulo
from .dtos import ResultadoTrabalhoDTO

class RealizarTrabalho:
    def __init__(self, repositorio_personagens: RepositorioPersonagens):
        self.repositorio_personagens = repositorio_personagens


    def executar(
        self,
        personagem_id: int,
        intervalo_trabalhar: int,
        tiers_config: dict,
        mensagens_trabalho: list[str],
        tempo_atual=None
    ) -> ResultadoTrabalhoDTO: # Adicionado tempo_atual como argumento opcional
        personagem = self.repositorio_personagens.obter_por_id(personagem_id)
        if not personagem:
            raise ValueError(f"Personagem com ID {personagem_id} não encontrado.")

        ultimo_trabalho = personagem.ultimo_trabalho
        if tempo_atual is None: # Se tempo_atual não foi passado, usa datetime.datetime.now()
            tempo_atual = datetime.datetime.now()

        if not verificar_cooldown(ultimo_trabalho, intervalo_trabalhar, tempo_atual=tempo_atual): # Passar tempo_atual para verificar_cooldown
            # Calcular tempo restante corretamente
            delta_segundos = (tempo_atual - ultimo_trabalho).total_seconds()
            tempo_restante = intervalo_trabalhar - delta_segundos
            # Formatar para hh:mm:ss (aproximado)
            tempo_restante_formatado = str(datetime.timedelta(seconds=int(tempo_restante)))
            raise ValueError(f"Ação de trabalho está em cooldown. Tempo restante: {tempo_restante_formatado}.")

        nivel_personagem = personagem.nivel
        recompensa = calcular_recompensa_trabalho(nivel_personagem, tiers_config)

        personagem.dinheiro += recompensa
        personagem.ultimo_trabalho = tempo_atual
        self.repositorio_personagens.atualizar(personagem) # Assuming 'atualizar' method exists

        mensagem = random.choice(mensagens_trabalho)
        
        mensagem_final = f"{mensagem}\nVocê ganhou {recompensa} moedas. Saldo atual: {personagem.dinheiro} moedas."

        return ResultadoTrabalhoDTO(
            personagem=personagem,
            mensagem=mensagem_final,
            recompensa=recompensa
        )