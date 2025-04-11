# Configuração e inicialização (variáveis de ambiente, logging)
using DotEnv, Logging, LoggingExtras

# Carregar .env
DotEnv.load!()

# Carregar variáveis de ambiente
const TOKEN = get(ENV, "DISCORD_TOKEN", "")
const APPLICATION_ID = parse(UInt64, get(ENV, "APPLICATION_ID", "0"))
const DATABASE_URL = get(ENV, "DATABASE_URL", "")
const LOG_LEVEL = get(ENV, "LOG_LEVEL", "INFO")
const GUILD = parse(Int, get(ENV, "GUILD", "0"))

# Configuração de logging
logger = ConsoleLogger(stdout, Logging.Info)
global_logger(logger)

if isempty(TOKEN) || APPLICATION_ID == 0
    error("Token do Discord ou Application ID não encontrado. Certifique-se de definir DISCORD_TOKEN e APPLICATION_ID no ambiente.")
end

function carregar_configuracao()
    YAML.load_file("config.yaml")
end

const config = carregar_configuracao()