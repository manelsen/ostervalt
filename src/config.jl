# Configuração e inicialização (variáveis de ambiente, logging)
# Este arquivo é incluído diretamente no módulo OstervaltBot.

using DotEnv, Logging, LoggingExtras, YAML

# Não precisa de export aqui, pois as constantes estarão no escopo OstervaltBot

# Carregar .env
DotEnv.load!()

# Carregar variáveis de ambiente
const TOKEN = get(ENV, "DISCORD_TOKEN", "")
const APPLICATION_ID = parse(UInt64, get(ENV, "APPLICATION_ID", "0"))
const DATABASE_URL = get(ENV, "DATABASE_URL", "")
const LOG_LEVEL = get(ENV, "LOG_LEVEL", "INFO")
const GUILD = parse(Int, get(ENV, "GUILD", "0"))

# Configuração de logging
const logger = ConsoleLogger(stdout, Logging.Info) # Tornar logger constante
global_logger(logger)

if isempty(TOKEN) || APPLICATION_ID == 0
    error("Token do Discord ou Application ID não encontrado. Certifique-se de definir DISCORD_TOKEN e APPLICATION_ID no ambiente.")
end

function carregar_configuracao()
    try
        return YAML.load_file("config.yaml")
    catch e
        @error "Erro ao carregar config.yaml. Verifique se o arquivo existe e está formatado corretamente." exception=(e, catch_backtrace())
        return Dict() # Retorna um dicionário vazio em caso de erro
    end
end

const config = carregar_configuracao()

# Fim do código de config.jl (sem 'end' de módulo)