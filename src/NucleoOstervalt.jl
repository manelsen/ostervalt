module NucleoOstervalt

include("ServicoCache.jl")
include("PersistenciaDados.jl")
include("Configuracoes.jl")
include("GerenciamentoPersonagens.jl")
include("Acoes.jl")
include("Economia.jl")
include("InventarioLoja.jl")
include("LogicaJogo.jl")
include("Permissoes.jl")
include("UtilitariosDiscord.jl")
include("ComandosDiscord.jl")

using Ekztazy, YAML, JSON3, Dates, Random, DataFrames, CSV, Logging, LoggingExtras, DotEnv, Debugger
using .Configuracoes
using .ServicoCache
using .PersistenciaDados
using .GerenciamentoPersonagens
using .Acoes
using .Economia
using .InventarioLoja
using .LogicaJogo
using .Permissoes
using .UtilitariosDiscord
using .ComandosDiscord

# Configuração de logging
logger = ConsoleLogger(stdout, Logging.Info)
global_logger(logger)

# Carregar .env
DotEnv.load!()

# Carregar variáveis de ambiente
const TOKEN = get(ENV, "DISCORD_TOKEN", "")
const APPLICATION_ID = parse(UInt64, get(ENV, "APPLICATION_ID", "0"))
const DATABASE_URL = get(ENV, "DATABASE_URL", "")
const LOG_LEVEL = get(ENV, "LOG_LEVEL", "INFO")
const GUILD = parse(Int, get(ENV, "GUILD", "0"))

if isempty(TOKEN) || APPLICATION_ID == 0
    error("Token do Discord ou Application ID não encontrado. Certifique-se de definir DISCORD_TOKEN e APPLICATION_ID no ambiente.")
end

# Inicialização do cliente Discord
cliente = Client(TOKEN, UInt64(APPLICATION_ID), intents(GUILDS, GUILD_MESSAGES), version=9)

# Registrar comandos Discord
ComandosDiscord.registrar_comandos(cliente)

# Incluir handlers de eventos e comandos
Ekztazy.add_handler!(cliente, on_interaction_create) do contexto
    # Lógica para lidar com interações (comandos slash)
    if haskey(contexto.interaction.data, "name")
        nome_comando = contexto.interaction.data.name
        # Chamar o handler apropriado com base no nome do comando
        if nome_comando == "saldo"
            ComandosDiscord.handler_comando_saldo(contexto)
        elseif nome_comando == "dinheiro"
            ComandosDiscord.handler_comando_dinheiro(contexto)
        # Adicionar outros comandos conforme necessário
        end
    end
end

Ekztazy.start(cliente)
end # do módulo
