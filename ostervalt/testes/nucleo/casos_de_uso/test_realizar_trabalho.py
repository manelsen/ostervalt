import pytest
import datetime
from unittest.mock import MagicMock, patch
from ostervalt.nucleo.casos_de_uso.realizar_trabalho import RealizarTrabalho
from ostervalt.nucleo.repositorios import RepositorioPersonagens
from ostervalt.nucleo.entidades.personagem import Personagem
from ostervalt.nucleo.casos_de_uso.dtos import ResultadoTrabalhoDTO

# Mock da entidade Personagem para os testes
def criar_personagem_mock(id=1, nivel=5, dinheiro=100, ultimo_trabalho=None):
    p = MagicMock(spec=Personagem)
    p.id = id
    p.nivel = nivel
    p.dinheiro = dinheiro
    p.ultimo_trabalho = ultimo_trabalho
    return p

@pytest.fixture
def repo_personagens_mock():
    return MagicMock(spec=RepositorioPersonagens)

@pytest.fixture
def tiers_config_mock():
    return {
        "t1": {"nivel_min": 1, "nivel_max": 5, "recompensa": 100},
        "t2": {"nivel_min": 6, "nivel_max": 10, "recompensa": 200}
    }

@pytest.fixture
def mensagens_trabalho_mock():
    return ["Você trabalhou.", "Bom trabalho!"]

@pytest.fixture
def intervalo_trabalhar_mock():
    return 3600 # 1 hora

# Teste de sucesso
def test_realizar_trabalho_sucesso(repo_personagens_mock, tiers_config_mock, mensagens_trabalho_mock, intervalo_trabalhar_mock):
    personagem = criar_personagem_mock(nivel=3, ultimo_trabalho=None)
    repo_personagens_mock.obter_por_id.return_value = personagem

    # Instancia o caso de uso apenas com o repositório
    caso_de_uso = RealizarTrabalho(repositorio_personagens=repo_personagens_mock)

    # Chama executar com os parâmetros necessários
    resultado = caso_de_uso.executar(
        personagem_id=personagem.id,
        intervalo_trabalhar=intervalo_trabalhar_mock,
        tiers_config=tiers_config_mock,
        mensagens_trabalho=mensagens_trabalho_mock
    )

    repo_personagens_mock.obter_por_id.assert_called_once_with(personagem.id)
    repo_personagens_mock.atualizar.assert_called_once()
    assert resultado.recompensa == 100 # Nível 3 cai no tier t1
    assert personagem.dinheiro == 100 + 100 # Dinheiro inicial + recompensa
    assert personagem.ultimo_trabalho is not None
    assert resultado.mensagem in [f"{msg}\nVocê ganhou 100 moedas. Saldo atual: 200 moedas." for msg in mensagens_trabalho_mock]

# Teste personagem não encontrado
def test_realizar_trabalho_personagem_nao_encontrado(repo_personagens_mock, tiers_config_mock, mensagens_trabalho_mock, intervalo_trabalhar_mock):
    repo_personagens_mock.obter_por_id.return_value = None
    caso_de_uso = RealizarTrabalho(repositorio_personagens=repo_personagens_mock)

    with pytest.raises(ValueError, match="Personagem com ID 999 não encontrado."):
        caso_de_uso.executar(
            personagem_id=999,
            intervalo_trabalhar=intervalo_trabalhar_mock,
            tiers_config=tiers_config_mock,
            mensagens_trabalho=mensagens_trabalho_mock
        )

# Teste cooldown não terminou
def test_realizar_trabalho_cooldown_nao_terminou(repo_personagens_mock, tiers_config_mock, mensagens_trabalho_mock, intervalo_trabalhar_mock):
    tempo_agora = datetime.datetime.now()
    ultimo_trabalho_recente = tempo_agora - datetime.timedelta(seconds=intervalo_trabalhar_mock / 2)
    personagem = criar_personagem_mock(ultimo_trabalho=ultimo_trabalho_recente)
    repo_personagens_mock.obter_por_id.return_value = personagem

    caso_de_uso = RealizarTrabalho(repositorio_personagens=repo_personagens_mock)

    with pytest.raises(ValueError, match="Ação de trabalho está em cooldown."):
        caso_de_uso.executar(
            personagem_id=personagem.id,
            intervalo_trabalhar=intervalo_trabalhar_mock,
            tiers_config=tiers_config_mock,
            mensagens_trabalho=mensagens_trabalho_mock,
            tempo_atual=tempo_agora # Passa o tempo atual para o teste
        )

# Teste com configuração de tier faltando ou inválida (deve retornar recompensa 0)
def test_realizar_trabalho_configuracao_faltando(repo_personagens_mock, mensagens_trabalho_mock, intervalo_trabalhar_mock):
    personagem = criar_personagem_mock(nivel=7) # Nível que não está nos tiers vazios
    repo_personagens_mock.obter_por_id.return_value = personagem
    caso_de_uso = RealizarTrabalho(repositorio_personagens=repo_personagens_mock)

    resultado = caso_de_uso.executar(
        personagem_id=personagem.id,
        intervalo_trabalhar=intervalo_trabalhar_mock,
        tiers_config={}, # Tiers vazios
        mensagens_trabalho=mensagens_trabalho_mock
    )

    assert resultado.recompensa == 0
    assert personagem.dinheiro == 100 # Dinheiro inicial não muda
    assert personagem.ultimo_trabalho is not None