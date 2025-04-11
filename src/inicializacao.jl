# Inicialização do bot Discord e registro de comandos

using Ekztazy
include("config.jl")
include("persistencia.jl")
include("logica_jogo.jl")
include("comandos_discord.jl")

# Instanciação do cliente Discord
cliente = Client(TOKEN, UInt64(APPLICATION_ID), intents(GUILDS, GUILD_MESSAGES), version=9)

# Função para registrar handlers dos comandos
function registrar_handlers_comandos()
    @info "Registrando comandos"
    command!(handler_comando_criar, cliente, "criar", "Cria um novo personagem")
    command!(handler_comando_ajuda, cliente, "ajuda", "Mostra a mensagem de ajuda")
    command!(handler_comando_up, cliente, "up", "Adiciona Marcos a um personagem")
    command!(handler_comando_marcos, cliente, "marcos", "Mostra os Marcos de um personagem")
    command!(handler_comando_mochila, cliente, "mochila", "Mostra o inventário de um personagem")
    command!(handler_comando_comprar, cliente, "comprar", "Compra um item da loja")
    command!(handler_comando_dinheiro, cliente, "dinheiro", "Adiciona ou remove dinheiro de um personagem")
    command!(handler_comando_saldo, cliente, "saldo", "Mostra o saldo de um personagem")
    command!(handler_comando_pix, cliente, "pix", "Transfere dinheiro entre personagens")
    command!(handler_comando_trabalhar, cliente, "trabalhar", "Faz o personagem trabalhar para ganhar dinheiro")
    command!(handler_comando_crime, cliente, "crime", "Tenta cometer um crime para ganhar dinheiro")
    command!(handler_comando_estoque, cliente, "estoque", "Gerencia o estoque da loja")
    command!(handler_comando_loja, cliente, "loja", "Mostra os itens disponíveis na loja")
    command!(handler_comando_inserir, cliente, "inserir", "Insere um item no estoque")
    command!(handler_comando_remover, cliente, "remover", "Remove um item do estoque")
    command!(handler_comando_limpar_estoque, cliente, "limpar_estoque", "Limpa o estoque da loja")
    command!(handler_comando_mensagens, cliente, "mensagens", "Adiciona mensagens personalizadas")
    command!(handler_comando_tiers, cliente, "tiers", "Configura os tiers de níveis")
    command!(handler_comando_probabilidade_crime, cliente, "probabilidade_crime", "Define a probabilidade de sucesso no crime")
    command!(handler_comando_rip, cliente, "rip", "Remove um personagem permanentemente")
    command!(handler_comando_inss, cliente, "inss", "Aposenta um personagem")
    command!(handler_comando_cargos, cliente, "cargos", "Gerencia cargos especiais")
    @info "Comandos registrados com sucesso"
end

# Handler global de erros
function handler_erro_personalizado(c::Client, erro::Exception, args...)
    @error "Ocorreu um erro" exception=(erro, catch_backtrace())
    if isa(erro, HTTP.WebSockets.WebSocketError)
        @warn "Erro de WebSocket detectado. Tentando reconectar..."
        sleep(5)
        try
            start(c)
        catch erro_reconexao
            @error "Falha ao reconectar" exception=(erro_reconexao, catch_backtrace())
        end
    end
end

# Inicialização do bot
function iniciar_bot()
    try
        @info "Gerando gestor de erros..."
        add_handler!(cliente, Handler(handler_erro_personalizado, type=:OnError))
        @info "Gestor de erros gerado com sucesso. Inicializando comandos..."
        registrar_handlers_comandos()
        @info "Comandos inicializados com sucesso. Iniciando o bot..."
        start(cliente)
    catch e
        @error "Falha ao iniciar o bot" exception=(e, catch_backtrace())
    end
end

# Ponto de entrada
if abspath(PROGRAM_FILE) == @__FILE__
    iniciar_bot()
end