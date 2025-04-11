module OstervaltBot

# Este módulo principal encapsula toda a lógica do bot.

println("Carregando módulo OstervaltBot...")

# Importa pacotes externos necessários por qualquer um dos arquivos incluídos
# É mais seguro declarar os usings aqui no topo do módulo principal.
using Ekztazy, Dates, Random, Logging, LoggingExtras, YAML, JSON3, DataFrames, CSV, DotEnv, HTTP

# Inclui os arquivos. O código deles será executado neste escopo (OstervaltBot).
# A ordem é importante para garantir que definições (constantes, funções)
# estejam disponíveis quando outros arquivos incluídos precisarem delas.
try
    println("  Incluindo src/config.jl...")
    include("config.jl") # Define TOKEN, APPLICATION_ID, config, logger, etc.

    println("  Incluindo src/persistencia.jl...")
    include("persistencia.jl") # Define Cache, funcs de cache, carregar/salvar_dados_servidor, etc. (usa config)

    println("  Incluindo src/logica_jogo.jl...")
    include("logica_jogo.jl") # Define funcs de nível, marcos, permissões, tier, etc. (usa config, funcs de persistencia)

    println("  Incluindo src/comandos_discord.jl...")
    include("comandos_discord.jl") # Define todos os handlers (usam funcs de logica, persistencia, config, cliente)

    println("  Incluindo src/inicializacao.jl...")
    include("inicializacao.jl") # Define funcs de registro, handlers de evento, iniciar_bot (usa cliente, handlers)

catch e
    println("Erro fatal ao incluir arquivos em OstervaltBot.jl:")
    showerror(stdout, e)
    println()
    Base.show_backtrace(stdout, catch_backtrace())
    rethrow() # Propaga o erro
end

# Exporta a função principal para ser chamada externamente
# A função iniciar_bot foi definida quando inicializacao.jl foi incluído.
export iniciar_bot

println("Módulo OstervaltBot carregado com sucesso.")

end # module OstervaltBot