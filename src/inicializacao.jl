# Inicialização do bot Discord e registro de comandos
# Este arquivo é incluído diretamente no módulo OstervaltBot.

using Ekztazy, Logging, HTTP, Dates # Pacotes externos necessários

# Imports relativos/absolutos removidos

# Não precisa de export aqui, a função iniciar_bot será exportada por OstervaltBot.jl

# Instanciação do cliente Discord (agora no escopo OstervaltBot)
# A constante 'cliente' precisa ser definida antes de ser usada nos handlers e registro.
# Presumindo que config.jl foi incluído antes e definiu TOKEN e APPLICATION_ID.
const cliente = Client(TOKEN, UInt64(APPLICATION_ID), intents(GUILDS, GUILD_MESSAGES), version=9)

"""
    registrar_comandos_guild(cliente::Client, id_guilda::UInt64)

Registra todos os comandos de aplicação (slash commands) para uma guild específica.
"""
function registrar_comandos_guild(cliente::Client, id_guilda::UInt64)
    @info "Registrando comandos para a guild $id_guilda"
    # Definições dos comandos
    # 'APPLICATION_ID' está acessível no escopo OstervaltBot
    commands = [
        ApplicationCommand(
            name = "criar", description = "Cria um novo personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "nome", description = "Nome do novo personagem", required = true)]
        ),
        ApplicationCommand(name = "ajuda", description = "Mostra a mensagem de ajuda", application_id = APPLICATION_ID),
        ApplicationCommand(
            name = "up", description = "Adiciona Marcos a um personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "marcos", description = "Mostra os Marcos de um personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "mochila", description = "Mostra o inventário de um personagem", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "personagem", description = "Nome do personagem", required = true),
                Option(type = 3, name = "item", description = "Nome do item (opcional)", required = false)
            ]
        ),
        ApplicationCommand(
            name = "comprar", description = "Compra um item da loja", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "personagem", description = "Nome do personagem", required = true),
                Option(type = 3, name = "item", description = "Nome do item", required = true)
            ]
        ),
        ApplicationCommand(
            name = "dinheiro", description = "Adiciona ou remove dinheiro de um personagem", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "personagem", description = "Nome do personagem", required = true),
                Option(type = 4, name = "quantidade", description = "Quantidade de dinheiro (use número negativo para remover)", required = true)
            ]
        ),
        ApplicationCommand(
            name = "saldo", description = "Mostra o saldo de um personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "pix", description = "Transfere dinheiro entre personagens", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "de_personagem", description = "Nome do personagem que envia", required = true),
                Option(type = 3, name = "para_personagem", description = "Nome do personagem que recebe", required = true),
                Option(type = 4, name = "quantidade", description = "Quantidade de dinheiro a transferir", required = true)
            ]
        ),
        ApplicationCommand(
            name = "trabalhar", description = "Faz o personagem trabalhar para ganhar dinheiro", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "crime", description = "Tenta cometer um crime para ganhar dinheiro", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "cargos", description = "Gerencia cargos especiais", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "tipo", description = "Tipo de permissão (saldo, marcos, loja, view)", required = true),
                Option(type = 3, name = "acao", description = "Ação a ser realizada (add, remove)", required = true),
                Option(type = 3, name = "cargo", description = "Nome do cargo", required = true)
            ]
        ),
        ApplicationCommand(
            name = "estoque", description = "Gerencia o estoque da loja", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 4, name = "comum", description = "Quantidade de itens comuns", required = true),
                Option(type = 4, name = "incomum", description = "Quantidade de itens incomuns", required = true),
                Option(type = 4, name = "raro", description = "Quantidade de itens raros", required = true),
                Option(type = 4, name = "muito_raro", description = "Quantidade de itens muito raros", required = true)
            ]
        ),
        ApplicationCommand(name = "loja", description = "Mostra os itens disponíveis na loja", application_id = APPLICATION_ID),
        ApplicationCommand(
            name = "inserir", description = "Insere um item no estoque", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "raridade", description = "Raridade do item (common, uncommon, rare, very rare)", required = true),
                Option(type = 3, name = "item", description = "Nome do item", required = true),
                Option(type = 4, name = "quantidade", description = "Quantidade do item", required = true),
                Option(type = 4, name = "valor", description = "Valor do item (opcional)", required = false)
            ]
        ),
        ApplicationCommand(
            name = "remover", description = "Remove um item do estoque", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "item", description = "Nome do item", required = true),
                Option(type = 4, name = "quantidade", description = "Quantidade a remover (opcional, remove tudo se omitido)", required = false)
            ]
        ),
        ApplicationCommand(name = "limpar_estoque", description = "Limpa o estoque da loja", application_id = APPLICATION_ID),
        ApplicationCommand(name = "backup", description = "Cria um backup dos dados do servidor", application_id = APPLICATION_ID),
        ApplicationCommand(
            name = "mensagens", description = "Adiciona mensagens personalizadas", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "tipo", description = "Tipo de mensagem (trabalho, crime)", required = true),
                Option(type = 3, name = "mensagem", description = "Mensagem a ser adicionada", required = true)
            ]
        ),
        ApplicationCommand(
            name = "tiers", description = "Configura os tiers de níveis", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "tier", description = "Nome do tier", required = true),
                Option(type = 4, name = "nivel_min", description = "Nível mínimo do tier", required = true),
                Option(type = 4, name = "nivel_max", description = "Nível máximo do tier", required = true),
                Option(type = 4, name = "recompensa", description = "Recompensa do tier", required = true)
            ]
        ),
        ApplicationCommand(
            name = "probabilidade_crime", description = "Define a probabilidade de sucesso no crime", application_id = APPLICATION_ID,
            opcoes = [Option(type = 4, name = "probabilidade", description = "Probabilidade de sucesso (0-100)", required = true)]
        ),
        ApplicationCommand(
            name = "rip", description = "Remove um personagem permanentemente", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "inss", description = "Aposenta um personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        )
    ]
    try
        Ekztazy.bulk_overwrite_application_commands(cliente, id_guilda, commands)
        @info "Comandos registrados com sucesso para a guild $id_guilda"
    catch e
        @error "Erro ao registrar comandos para a guild $id_guilda" exception=(e, catch_backtrace())
    end
end

"""
    registrar_comandos_globais(cliente::Client)

Registra os comandos de aplicação globais (disponíveis em todas as guilds).
"""
function registrar_comandos_globais(cliente::Client)
    @info "Registrando comandos globalmente"
    # Definições dos comandos globais
    commands = [
        ApplicationCommand(
            name = "criar", description = "Cria um novo personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "nome", description = "Nome do novo personagem", required = true)]
        ),
        ApplicationCommand(name = "ajuda", description = "Mostra a mensagem de ajuda", application_id = APPLICATION_ID),
        ApplicationCommand(
            name = "up", description = "Adiciona Marcos a um personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "marcos", description = "Mostra os Marcos de um personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "mochila", description = "Mostra o inventário de um personagem", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "personagem", description = "Nome do personagem", required = true),
                Option(type = 3, name = "item", description = "Nome do item (opcional)", required = false)
            ]
        ),
        ApplicationCommand(
            name = "comprar", description = "Compra um item da loja", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "personagem", description = "Nome do personagem", required = true),
                Option(type = 3, name = "item", description = "Nome do item", required = true)
            ]
        ),
        ApplicationCommand(
            name = "dinheiro", description = "Adiciona ou remove dinheiro de um personagem", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "personagem", description = "Nome do personagem", required = true),
                Option(type = 4, name = "quantidade", description = "Quantidade de dinheiro (use número negativo para remover)", required = true)
            ]
        ),
        ApplicationCommand(
            name = "saldo", description = "Mostra o saldo de um personagem", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "pix", description = "Transfere dinheiro entre personagens", application_id = APPLICATION_ID,
            opcoes = [
                Option(type = 3, name = "de_personagem", description = "Nome do personagem que envia", required = true),
                Option(type = 3, name = "para_personagem", description = "Nome do personagem que recebe", required = true),
                Option(type = 4, name = "quantidade", description = "Quantidade de dinheiro a transferir", required = true)
            ]
        ),
        ApplicationCommand(
            name = "trabalhar", description = "Faz o personagem trabalhar para ganhar dinheiro", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        ),
        ApplicationCommand(
            name = "crime", description = "Tenta cometer um crime para ganhar dinheiro", application_id = APPLICATION_ID,
            opcoes = [Option(type = 3, name = "personagem", description = "Nome do personagem", required = true)]
        )
    ]
    try
        @info "Tentando registrar comandos globalmente"
        Ekztazy.bulk_overwrite_application_commands(cliente, commands)
        @info "Comandos registrados globalmente com sucesso"
    catch e
        @error "Erro ao registrar comandos globalmente" exception=(e, catch_backtrace())
    end
end

"""
    registrar_handlers_comandos(cliente::Client)

Registra os handlers para cada comando de aplicação no cliente Discord.
As funções handler agora estão no mesmo escopo (OstervaltBot).
"""
function registrar_handlers_comandos(cliente::Client)
    @info "Registrando handlers dos comandos"
    # Usa os nomes diretos das funções handler (sem prefixo de módulo)
    command!(handler_comando_criar, cliente, "criar", "Cria um novo personagem")
    command!(backhandler_comando_up, cliente, "backup", "Cria um backup dos dados do servidor")
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
    command!(limpar_handler_comando_estoque, cliente, "limpar_estoque", "Limpa o estoque da loja")
    command!(handler_comando_mensagens, cliente, "mensagens", "Adiciona mensagens personalizadas")
    command!(handler_comando_tiers, cliente, "tiers", "Configura os tiers de níveis")
    command!(prob_handler_comando_crime, cliente, "probabilidade_crime", "Define a probabilidade de sucesso no crime")
    command!(handler_comando_rip, cliente, "rip", "Remove um personagem permanentemente")
    command!(handler_comando_inss, cliente, "inss", "Aposenta um personagem")
    command!(handler_comando_cargos, cliente, "cargos", "Gerencia cargos especiais")
    @info "Handlers dos comandos registrados com sucesso"
end

"""
    handler_erro_personalizado(c::Client, erro::Exception, args...)

Handler global de erros. Loga o erro e tenta reconectar em caso de erro de WebSocket.
"""
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

"""
    ao_entrar_guild_handler(contexto)

Handler para o evento `GUILD_CREATE`. Registra os comandos específicos da guild.
"""
function ao_entrar_guild_handler(contexto)
    id_guilda = UInt64(contexto.guild.id)
    @info "Bot conectado/entrou na guild: $id_guilda. Registrando comandos específicos da guild..."
    try
        registrar_comandos_guild(cliente, id_guilda) # Função no mesmo escopo
    catch e
        @error "Erro ao registrar comandos para a guild $id_guilda" exception=(e, catch_backtrace())
    end
end

"""
    iniciar_bot()

Função principal que inicializa o bot, registra handlers e inicia a conexão com o Discord.
"""
function iniciar_bot()
    try
        @info "Configurando handlers de eventos..."
        add_handler!(cliente, Handler(handler_erro_personalizado, type=:OnError))
        add_handler!(cliente, Handler(ao_entrar_guild_handler, type=:GuildCreate))
        @info "Handlers de eventos configurados."

        @info "Registrando handlers dos comandos de aplicação..."
        registrar_handlers_comandos(cliente) # Função no mesmo escopo
        @info "Handlers dos comandos registrados."

        # Opcional: Registrar comandos globais (pode demorar para propagar)
        # registrar_comandos_globais(cliente)

        @info "Iniciando conexão com o Discord..."
        start(cliente)
        @info "Bot conectado e pronto."

    catch e
        @error "Falha crítica ao iniciar ou durante a execução do bot" exception=(e, catch_backtrace())
    finally
        @info "Bot encerrando."
    end
end

# Fim do código de inicializacao.jl (sem 'end' de módulo)