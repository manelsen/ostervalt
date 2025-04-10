using Ekztazy, YAML, JSON3, Dates, Random, DataFrames, CSV, Logging, LoggingExtras, DotEnv, Debugger

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

function load_config()
    YAML.load_file("config.yaml")
end

const config = load_config()

"""
    Cache

Estrutura para armazenamento em cache de dados temporários.

# Campos
- `data::Dict{String, Any}`: Dados armazenados em cache.
- `ttl::Int`: Tempo de vida do cache em segundos.
- `last_update::DateTime`: Momento da última atualização do cache.
"""
mutable struct Cache
    data::Dict{String, Any}
    ttl::Int
    last_update::DateTime
end

"""
    get_cache(key::String, cache::Cache) -> Any

Obtém um valor do cache se ainda estiver válido.

- `key`: Chave de busca.
- `cache`: Instância de Cache.

Retorna o valor armazenado ou `nothing` se expirado ou não encontrado.
"""
function get_cache(key::String, cache::Cache)
    if haskey(cache.data, key) && (now() - cache.last_update).value < cache.ttl
        return cache.data[key]
    end
    return nothing
end

"""
    set_cache(key::String, value::Any, cache::Cache)

Armazena um valor no cache e atualiza o timestamp.

- `key`: Chave de armazenamento.
- `value`: Valor a ser armazenado.
- `cache`: Instância de Cache.
"""
function set_cache(key::String, value::Any, cache::Cache)
    cache.data[key] = value
    cache.last_update = now()
end

const server_data_cache = Cache(Dict(), 300, now())

"""
    load_server_data(server_id::String) -> Dict

Carrega os dados persistentes de um servidor Discord a partir de arquivo JSON.
Utiliza cache para otimizar leituras frequentes.

- `server_id`: ID do servidor Discord.

Retorna um dicionário com todos os dados do servidor.
"""
function load_server_data(server_id::String)
    cached_data = get_cache(server_id, server_data_cache)
    if !isnothing(cached_data)
        return cached_data
    end

    data = Dict()
    if isfile("server_data_$server_id.json")
        open("server_data_$server_id.json", "r") do f
            data = JSON3.read(f, Dict)
        end
    end

    data["characters"]    = get(data, "characters",    Dict())
    data["stock_items"]   = get(data, "stock_items",   Dict())
    data["special_roles"] = get(data, "special_roles", Dict())
    
    for key in ["saldo", "marcos", "loja"]
        data["special_roles"][key] = get(data["special_roles"], key, UInt64[])
    end
    
    data["shop_items"]          = get(data, "shop_items", nothing)
    data["messages"]            = get(data, "messages", get(config, "messages", Dict()))
    data["tiers"]               = get(data, "tiers", get(config, "tiers", Dict()))
    data["aposentados"]         = get(data, "aposentados", Dict())
    data["prices"]              = get(data, "prices", Dict())
    data["probabilidade_crime"] = get(data, "probabilidade_crime", get(get(config, "probabilidades", Dict()), "crime", 50))

    set_cache(server_id, data, server_data_cache)
    return data
end

"""
    save_server_data(server_id::String, data::Dict)

Salva os dados do servidor Discord em arquivo JSON e atualiza o cache.

- `server_id`: ID do servidor Discord.
- `data`: Dicionário de dados a serem salvos.
"""
function save_server_data(server_id::String, data::Dict)
    open("server_data_$server_id.json", "w") do f
        JSON3.write(f, data)
    end
    set_cache(server_id, data, server_data_cache)
    @info "Dados do servidor $server_id salvos e cache atualizado."
end

"""
    update_item_price(server_id::String, item_name::String, value::String)

Atualiza o preço de um item na base de dados do servidor.

- `server_id`: ID do servidor Discord.
- `item_name`: Nome do item.
- `value`: Novo valor do item (string).
"""
function update_item_price(server_id::String, item_name::String, value::String)
    data = load_server_data(server_id)
    data["prices"] = get(data, "prices", Dict())
    data["prices"][item_name] = value
    save_server_data(server_id, data)
    @info "Preço atualizado para $item_name: $value moedas"
end

"""
    calculate_level(marcos::Float64) -> Int

Calcula o nível de um personagem a partir da quantidade de Marcos.

- `marcos`: Quantidade de Marcos (pontos de experiência).

Retorna o nível correspondente (máximo 20).
"""
function calculate_level(marcos::Float64)
    min(20, floor(Int, marcos) + 1)
end

"""
    marcos_to_gain(level::Int) -> Int

Retorna a quantidade de Marcos a ser ganha para o próximo nível, de acordo com a configuração.

- `level`: Nível atual do personagem.

Retorna a quantidade de Marcos a ser adicionada.
"""
function marcos_to_gain(level::Int)
    marcos_por_nivel = get(get(config, "progressao", Dict()), "marcos_por_nivel", Dict())
    if level <= 4
        return get(marcos_por_nivel, "1-4", 16)
    elseif level <= 12
        return get(marcos_por_nivel, "5-12", 4)
    elseif level <= 16
        return get(marcos_por_nivel, "13-16", 2)
    else
        return get(marcos_por_nivel, "17-20", 1)
    end
end

"""
    format_marcos(marcos_parts::Int) -> String

Formata a quantidade de partes de Marcos em uma string legível, considerando frações e níveis.

- `marcos_parts`: Quantidade de partes de Marcos (1 Marco = 16 partes).

Retorna uma string formatada para exibição ao usuário.
"""
function format_marcos(marcos_parts::Int)
    full_marcos = div(marcos_parts, 16)
    remaining_parts = mod(marcos_parts, 16)

    if remaining_parts == 0
        return "$full_marcos Marcos"
    end

    level = calculate_level(marcos_parts / 16)

    if level <= 4
        return "$full_marcos Marcos"
    elseif level <= 12
        return "$full_marcos e $(div(remaining_parts, 4))/4 Marcos"
    elseif level <= 16
        return "$full_marcos e $(div(remaining_parts, 2))/8 Marcos"
    else
        return "$full_marcos e $remaining_parts/16 Marcos"
    end
end

"""
    check_permissions(member::Ekztazy.Member, character::Union{String, Nothing}, permission_type::String, server_data::Dict, allow_owner::Bool=true) -> Bool

Verifica se o membro possui permissão para executar determinada ação, considerando dono do personagem, administrador ou cargo especial.

- `member`: Membro do Discord.
- `character`: Nome do personagem (ou `nothing`).
- `permission_type`: Tipo de permissão ("marcos", "saldo", "loja", etc).
- `server_data`: Dados do servidor.
- `allow_owner`: Se `true`, permite que o dono do personagem execute a ação.

Retorna `true` se permitido, `false` caso contrário.
"""
function check_permissions(member::Ekztazy.Member, character::Union{String, Nothing}, permission_type::String, server_data::Dict, allow_owner::Bool=true)
    user_id = string(member.user.id)
    is_owner = !isnothing(character) && haskey(get(server_data["characters"], user_id, Dict()), character)
    is_admin = :administrator in member.permissions
    has_special_role = any(role -> role.id in get(server_data["special_roles"], permission_type, UInt64[]), member.roles)
    return allow_owner ? (is_owner || is_admin || has_special_role) : (is_admin || has_special_role)
end

"""
    get_tier(nivel::Int, server_data::Dict) -> Union{String, Nothing}

Obtém o nome do tier correspondente ao nível informado, de acordo com a configuração do servidor.

- `nivel`: Nível do personagem.
- `server_data`: Dados do servidor.

Retorna o nome do tier ou `nothing` se não houver correspondência.
"""
function get_tier(nivel::Int, server_data::Dict)
    for (tier_name, tier_data) in get(server_data, "tiers", Dict())
        if tier_data["nivel_min"] <= nivel && nivel <= tier_data["nivel_max"]
            return tier_name
        end
    end
    return nothing
end

"""
    wait_for_message(ctx) -> Union{String, Nothing}

Aguarda a resposta do usuário no canal do contexto, com timeout de 30 segundos.

- `ctx`: Contexto da interação.

Retorna o conteúdo da mensagem respondida ou `nothing` em caso de timeout.
"""
function wait_for_message(ctx)
    future = wait_for(ctx.client, :MessageCreate;
                      check=(event_ctx) -> event_ctx.author.id == ctx.interaction.member.user.id &&
                                           event_ctx.channel_id == ctx.interaction.channel_id,
                      timeout=30)
    if future === nothing
        reply(ctx.client, ctx, content="Tempo esgotado para responder.")
        return nothing
    else
        return future.message.content
    end
end
"""
    criar_command_handler(ctx)

Handler do comando /criar. Cria um novo personagem para o usuário a partir do nome fornecido.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da criação.
"""
function criar_command_handler(ctx)
    @info "Comando /criar foi acionado"

    options = ctx.interaction.data.options

    if isnothing(options) || isempty(options)
        return reply(client, ctx, content="Por favor, forneça um nome para o personagem.")
    end

    nome = options[1].value
    server_id = string(ctx.interaction.guild_id)
    user_id = string(ctx.interaction.member.user.id)

    resultado = criar_personagem(server_id, user_id, nome)
    
    reply(client, ctx, content=resultado)
    @info "Resultado da criação do personagem: $resultado"
end

"""
    ajuda_command_handler(ctx)

Handler do comando /ajuda. Exibe a mensagem de ajuda com a lista de comandos disponíveis.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com a mensagem de ajuda.
"""
function ajuda_command_handler(ctx)
    @info "Comando /ajuda foi acionado"
    mensagem_ajuda = gerar_mensagem_ajuda()
    reply(client, ctx, content=mensagem_ajuda)
    @info "Resposta de ajuda enviada com sucesso"
end

function get_item_description(server_data::Dict, item_name::String)
function get_item_description(server_data::Dict, item_name::String)
    for (_, rarity_items) in get(server_data, "stock_items", Dict())
        if item_name in get(rarity_items, "Name", [])
            index = findfirst(==(item_name), rarity_items["Name"])
            return get(rarity_items, "Text", [])[index]
        end
    end
    return "Descrição não disponível."
end

# Função duplicada removida: criar_personagem
        "dinheiro" => 0,
        "nivel" => 1,
        "last_work_time" => nothing,
        "last_crime_time" => nothing,
        "estrelas" => 0
    )

    user_characters[nome] = new_character
    server_data["characters"][user_id] = user_characters

    save_server_data(server_id, server_data)

    return "Personagem $nome criado com sucesso e vinculado à sua conta Discord! Nível inicial: 1"
end

function gerar_mensagem_ajuda()
    comandos = [
        ("criar", "Cria um novo personagem. Mas cuidado, não crie muitos! Números grandes me assustam..."),
        ("up", "Adiciona Marcos ao seu personagem. É como contar XP, mas menos assustador."),
        ("marcos", "Mostra os Marcos e nível do seu personagem. Prometo não contar errado!"),
        ("mochila", "Lista os itens no inventário do seu personagem. Espero que não tenha nada perigoso aí dentro!"),
        ("comprar", "Compra um item da loja. Lembre-se, gastar demais pode ser assustador!"),
        ("dinheiro", "Adiciona ou remove dinheiro do saldo de um personagem. Por favor, use com responsabilidade!"),
        ("saldo", "Mostra quanto dinheiro seu personagem tem. Não se preocupe, não vou roubá-lo!"),
        ("pix", "Transfere moedas entre personagens. É como magia, mas com números!"),
        ("trabalhar", "Seu personagem trabalha para ganhar dinheiro. Trabalhar é menos assustador que aventuras, certo?"),
        ("crime", "Arrisque ganhar ou perder dinheiro. Mas crime não compensa e é muito, muito assustador!")
    ]

    mensagem = "Oi! Eu sou Ostervalt, Contador e Guarda-Livros do Reino de Tremond. Estou um pouco nervoso, mas vou tentar explicar os comandos disponíveis. Por favor, não grite!\n\n"

    for (nome, descricao) in comandos
        mensagem *= "/$(nome) - $(descricao)\n\n"
    end

    mensagem *= "\nLembre-se, se precisar de mais ajuda, é só chamar! Mas, por favor, não grite. Coelhos têm ouvidos sensíveis!"

    return mensagem
end

function criar_command_handler(ctx)
    @info "Comando /criar foi acionado"

    options = ctx.interaction.data.options

    if isnothing(options) || isempty(options)
        return reply(client, ctx, content="Por favor, forneça um nome para o personagem.")
    end

    nome = options[1].value
    server_id = string(ctx.interaction.guild_id)
    user_id = string(ctx.interaction.member.user.id)

    resultado = criar_personagem(server_id, user_id, nome)
    
    reply(client, ctx, content=resultado)
    @info "Resultado da criação do personagem: $resultado"
end

function ajuda_command_handler(ctx)
    @info "Comando /ajuda foi acionado"
    mensagem_ajuda = gerar_mensagem_ajuda()
    reply(client, ctx, content=mensagem_ajuda)
    @info "Resposta de ajuda enviada com sucesso"
end

"""
    up_command_handler(ctx)

Handler do comando /up. Adiciona Marcos ao personagem informado, atualizando o nível se necessário.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação.
"""
function up_command_handler(ctx)
    @info "Comando /up foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do personagem.")
    end

    character = ctx.interaction.data.options[1].value
    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    if !check_permissions(ctx.interaction.member, character, "marcos", server_data, false)
        return reply(client, ctx, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    character_found = false
    for (user_id, characters) in server_data["characters"]
        if haskey(characters, character)
            character_data = characters[character]
            current_level = character_data["nivel"]
            marcos_to_add = marcos_to_gain(current_level)

            character_data["marcos"] += marcos_to_add
            new_marcos = character_data["marcos"]
            new_level = calculate_level(new_marcos / 16)

            if new_level > current_level
                character_data["nivel"] = new_level
                reply(client, ctx, content="$character subiu para o nível $new_level!")
            else
                fraction_added = marcos_to_add == 4 ? "1/4 de Marco" :
                                 marcos_to_add == 2 ? "1/8 de Marco" :
                                 marcos_to_add == 1 ? "1/16 de Marco" :
                                 "$marcos_to_add Marcos"

                reply(client, ctx, content="Adicionado $fraction_added para $character. Total: $(format_marcos(new_marcos)) (Nível $new_level)")
            end

            save_server_data(server_id, server_data)
            character_found = true
            break
        end
    end

    if !character_found
        reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    marcos_command_handler(ctx)

Handler do comando /marcos. Exibe a quantidade de Marcos e o nível do personagem informado.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com a quantidade de Marcos e nível.
"""
function marcos_command_handler(ctx)
    @info "Comando /marcos foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do personagem.")
    end

    character = ctx.interaction.data.options[1].value
    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    if !check_permissions(ctx.interaction.member, character, "marcos", server_data, false)
        return reply(client, ctx, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    character_found = false
    for (user_id, characters) in server_data["characters"]
        if haskey(characters, character)
            character_data = characters[character]
            marcos = character_data["marcos"]
            level = calculate_level(marcos / 16)
            reply(client, ctx, content="$character tem $(format_marcos(marcos)) (Nível $level)")
            character_found = true
            break
        end
    end

    if !character_found
        reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    mochila_command_handler(ctx)

Handler do comando /mochila. Exibe o inventário do personagem informado, ou a descrição de um item específico.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com a lista de itens ou descrição detalhada.
"""
function mochila_command_handler(ctx)
    @info "Comando /mochila foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do personagem.")
    end

    character = ctx.interaction.data.options[1].value
    item = length(ctx.interaction.data.options) > 1 ? ctx.interaction.data.options[2].value : nothing

    server_id = string(ctx.interaction.guild_id)
    user_id = string(ctx.interaction.member.user.id)
    server_data = load_server_data(server_id)

    if !check_permissions(ctx.interaction.member, character, "view", server_data, true)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    character_data = get(get(server_data["characters"], user_id, Dict()), character, nothing)
    if isnothing(character_data)
        return reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    inventory = get(character_data, "inventory", [])
    if isempty(inventory)
        return reply(client, ctx, content="O inventário de $character está vazio.")
    end

    if !isnothing(item)
        if item in inventory
            item_count = count(==(item), inventory)
            item_description = get_item_description(server_data, item)
            reply(client, ctx, content="**$item** (x$item_count)\nDescrição: $item_description")
        else
            reply(client, ctx, content="O item '$item' não está na mochila de $character.")
        end
    else
        item_counts = Dict{String, Int}()
        for i in inventory
            item_counts[i] = get(item_counts, i, 0) + 1
        end
        
        items_formatted = join(["**$item** (x$count)" for (item, count) in item_counts], ", ")
        reply(client, ctx, content="Inventário de $character: $items_formatted")
    end
end

"""
    comprar_command_handler(ctx)

Handler do comando /comprar. Permite que um personagem compre um item da loja, descontando o valor e atualizando o estoque.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da compra.
"""
function comprar_command_handler(ctx)
    @info "Comando /comprar foi acionado"

    if length(ctx.interaction.data.options) < 2
        return reply(client, ctx, content="Uso incorreto. Use: /comprar <personagem> <item>")
    end

    character = ctx.interaction.data.options[1].value
    item = ctx.interaction.data.options[2].value

    server_id = string(ctx.interaction.guild_id)
    user_id = string(ctx.interaction.member.user.id)
    server_data = load_server_data(server_id)

    if !check_permissions(ctx.interaction.member, character, "view", server_data, true)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    user_characters = get(server_data["characters"], user_id, Dict())
    if !haskey(user_characters, character)
        return reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    if isempty(get(server_data, "stock_items", Dict()))
        return reply(client, ctx, content="A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
    end

    character_data = user_characters[character]
    item_found = false
    for (rarity, items) in server_data["stock_items"]
        if item in items["Name"]
            item_index = findfirst(==(item), items["Name"])
            if items["Quantity"][item_index] > 0
                item_value = parse(Int, items["Value"][item_index])

                if character_data["dinheiro"] < item_value
                    return reply(client, ctx, content="$character não tem dinheiro suficiente para comprar $item. Preço: $item_value, Dinheiro disponível: $(character_data["dinheiro"])")
                end

                character_data["dinheiro"] -= item_value
                push!(character_data["inventory"], item)

                items["Quantity"][item_index] -= 1

                reply(client, ctx, content="$character comprou $item por $item_value moedas. Dinheiro restante: $(character_data["dinheiro"])")
                save_server_data(server_id, server_data)
                item_found = true
            else
                reply(client, ctx, content="Desculpe, $item está fora de estoque.")
                item_found = true
            end
            break
        end
    end

    if !item_found
        reply(client, ctx, content="Item '$item' não encontrado na loja.")
    end
end

"""
    dinheiro_command_handler(ctx)

Handler do comando /dinheiro. Adiciona ou remove dinheiro do saldo de um personagem.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o novo saldo ou mensagem de erro.
"""
function dinheiro_command_handler(ctx)
    @info "Comando /dinheiro foi acionado"

    if length(ctx.interaction.data.options) < 2
        return reply(client, ctx, content="Uso incorreto. Use: /dinheiro <personagem> <quantidade>")
    end

    character = ctx.interaction.data.options[1].value
    amount = parse(Int, ctx.interaction.data.options[2].value)

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    if !check_permissions(ctx.interaction.member, character, "saldo", server_data, false)
        return reply(client, ctx, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    character_found = false
    for (user_id, characters) in server_data["characters"]
        if haskey(characters, character)
            character_data = characters[character]
            character_data["dinheiro"] += amount

            if amount > 0
                reply(client, ctx, content="Adicionado $amount moedas ao saldo de $character. Novo saldo: $(character_data["dinheiro"]) moedas.")
            else
                reply(client, ctx, content="Removido $(abs(amount)) moedas do saldo de $character. Novo saldo: $(character_data["dinheiro"]) moedas.")
            end

            save_server_data(server_id, server_data)
            character_found = true
            break
        end
    end

    if !character_found
        reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    saldo_command_handler(ctx)

Handler do comando /saldo. Exibe o saldo de moedas do personagem informado.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o saldo do personagem.
"""
function saldo_command_handler(ctx)
    @info "Comando /saldo foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do personagem.")
    end

    character = ctx.interaction.data.options[1].value
    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    if !check_permissions(ctx.interaction.member, character, "view", server_data, true)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    user_id = string(ctx.interaction.member.user.id)
    user_characters = get(server_data["characters"], user_id, Dict())

    if haskey(user_characters, character)
        character_data = user_characters[character]
        money = get(character_data, "dinheiro", 0)
        reply(client, ctx, content="$character tem $money moedas.")
    else
        reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    pix_command_handler(ctx)

Handler do comando /pix. Transfere moedas de um personagem para outro, validando saldo e restrições.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da transferência.
"""
function pix_command_handler(ctx)
    @info "Comando /pix foi acionado"

    if length(ctx.interaction.data.options) < 3
        return reply(client, ctx, content="Uso incorreto. Use: /pix <de_personagem> <para_personagem> <quantidade>")
    end

    from_character = ctx.interaction.data.options[1].value
    to_character = ctx.interaction.data.options[2].value
    amount = parse(Int, ctx.interaction.data.options[3].value)

    if amount <= 0
        return reply(client, ctx, content="A quantidade deve ser maior que zero.")
    end

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    user_id = string(ctx.interaction.member.user.id)
    user_characters = get(server_data["characters"], user_id, Dict())

    if !haskey(user_characters, from_character)
        return reply(client, ctx, content="Você não possui um personagem chamado $from_character.")
    end

    if any(char -> char == to_character, keys(user_characters))
        return reply(client, ctx, content="Não é possível transferir moedas para um de seus próprios personagens.")
    end

    recipient_found = false
    recipient_data = nothing
    for (user_id_recipient, characters) in server_data["characters"]
        if haskey(characters, to_character) && user_id_recipient != user_id
            recipient_data = characters[to_character]
            recipient_found = true
            break
        end
    end

    if !recipient_found
        return reply(client, ctx, content="O personagem destinatário '$to_character' não foi encontrado ou é de sua propriedade.")
    end

    sender_data = user_characters[from_character]

    if sender_data["dinheiro"] < amount
        return reply(client, ctx, content="$from_character não tem moedas suficientes. Saldo disponível: $(sender_data["dinheiro"])")
    end

    sender_data["dinheiro"] -= amount
    recipient_data["dinheiro"] += amount

    save_server_data(server_id, server_data)

    reply(client, ctx, content="Transferência realizada com sucesso!\n$from_character enviou $amount moedas para $to_character.\nNovo saldo de $from_character: $(sender_data["dinheiro"]) moedas.")
end

"""
    trabalhar_command_handler(ctx)

Handler do comando /trabalhar. Permite que o personagem trabalhe para ganhar moedas, respeitando limites de tempo e tiers.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com a recompensa do trabalho ou mensagem de erro.
"""
"""
    trabalhar_command_handler(ctx)

Handler do comando /trabalhar. Permite que o personagem trabalhe para ganhar moedas, respeitando limites de tempo e tiers.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com a recompensa do trabalho ou mensagem de erro.
"""
function trabalhar_command_handler(ctx)
    @info "Comando /trabalhar foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do personagem.")
    end

    character = ctx.interaction.data.options[1].value
    server_id = string(ctx.interaction.guild_id)
    user_id = string(ctx.interaction.member.user.id)
    server_data = load_server_data(server_id)

    if !check_permissions(ctx.interaction.member, character, "view", server_data, true)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    user_characters = get(server_data["characters"], user_id, Dict())
    if !haskey(user_characters, character)
        return reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    character_data = user_characters[character]

    last_work_time = get(character_data, "last_work_time", nothing)
    now = Dates.now()
    intervalo_trabalhar = get(get(config, "limites", Dict()), "intervalo_trabalhar", 86400)
    if !isnothing(last_work_time)
        delta = now - DateTime(last_work_time)
        if Dates.value(delta) < intervalo_trabalhar * 1000
            return reply(client, ctx, content=get(config["messages"]["erros"], "acao_frequente", "Você já trabalhou recentemente. Aguarde um pouco para trabalhar novamente."))
        end
    end

    nivel = get(character_data, "nivel", 0)
    tier_name = get_tier(nivel, server_data)
    if isnothing(tier_name)
        return reply(client, ctx, content="Nenhum tier definido para o seu nível. Contate um administrador.")
    end

    tier = server_data["tiers"][tier_name]
    recompensa = tier["recompensa"]
    character_data["dinheiro"] += recompensa
    character_data["last_work_time"] = string(now)

    mensagens = get(get(server_data, "messages", Dict()), "trabalho", get(config["messages"], "trabalho", []))
    mensagem = isempty(mensagens) ? "Você trabalhou duro e ganhou sua recompensa!" : rand(mensagens)

    save_server_data(server_id, server_data)
    reply(client, ctx, content="$mensagem\nVocê ganhou $recompensa moedas. Saldo atual: $(character_data["dinheiro"]) moedas.")
end

"""
    crime_command_handler(ctx)

Handler do comando /crime. Permite que o personagem tente cometer um crime para ganhar ou perder moedas, respeitando limites e probabilidades.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado do crime.
"""
function crime_command_handler(ctx)
    @info "Comando /crime foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do personagem.")
    end

    character = ctx.interaction.data.options[1].value
    server_id = string(ctx.interaction.guild_id)
    user_id = string(ctx.interaction.member.user.id)
    server_data = load_server_data(server_id)

    if !check_permissions(ctx.interaction.member, character, "view", server_data, true)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    user_characters = get(server_data["characters"], user_id, Dict())
    if !haskey(user_characters, character)
        return reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    character_data = user_characters[character]

    last_crime_time = get(character_data, "last_crime_time", nothing)
    now = Dates.now()
    intervalo_crime = get(get(config, "limites", Dict()), "intervalo_crime", 86400)
    if !isnothing(last_crime_time)
        delta = now - DateTime(last_crime_time)
        if Dates.value(delta) < intervalo_crime * 1000
            return reply(client, ctx, content=get(config["messages"]["erros"], "acao_frequente", "Você já cometeu um crime recentemente. Aguarde um pouco para tentar novamente."))
        end
    end

    probabilidade = get(server_data, "probabilidade_crime", get(get(config, "probabilidades", Dict()), "crime", 50))
    chance = rand(1:100)

    mensagens = get(get(server_data, "messages", Dict()), "crime", get(config["messages"], "crime", []))
    mensagem = isempty(mensagens) ? "Você tentou cometer um crime..." : rand(mensagens)

    if chance <= probabilidade
        recompensa = rand(100:500)
        character_data["dinheiro"] += recompensa
        resultado = "Sucesso! Você ganhou $recompensa moedas."
    else
        perda = rand(50:250)
        character_data["dinheiro"] = max(0, character_data["dinheiro"] - perda)
        resultado = "Você foi pego! Perdeu $perda moedas."
    end

    character_data["last_crime_time"] = string(now)

    # Incrementar o atributo oculto 'estrelas'
    character_data["estrelas"] = get(character_data, "estrelas", 0) + 1

    save_server_data(server_id, server_data)
    reply(client, ctx, content="$mensagem\n$resultado\nSaldo atual: $(character_data["dinheiro"]) moedas.")
end

"""
    cargos_command_handler(ctx)

Handler do comando /cargos. Gerencia cargos especiais para permissões de saldo, marcos e loja.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de cargos.
"""
function cargos_command_handler(ctx)
    @info "Comando /cargos foi acionado"

    if length(ctx.interaction.data.options) < 3
        return reply(client, ctx, content="Uso incorreto. Use: /cargos <tipo> <acao> <cargo>")
    end

    tipo = ctx.interaction.data.options[1].value
    acao = ctx.interaction.data.options[2].value
    cargo_name = ctx.interaction.data.options[3].value

    user = ctx.interaction.member
    guild = ctx.interaction.guild_id |> (t -> get_guild(client, t)) |> fetch |> (u -> u.val)
    channel = ctx.interaction.channel_id |> (r -> get_channel(client, r)) |> fetch |> (s -> s.val)
    permissions = Ekztazy.permissions_in(user, guild, channel)

    if !has_permission(permissions, PERM_ADMINISTRATOR)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    if !(tipo in ["saldo", "marcos", "loja"])
        return reply(client, ctx, content="Tipo inválido. Use 'saldo', 'marcos' ou 'loja'.")
    end

    if !(acao in ["add", "remove"])
        return reply(client, ctx, content="Ação inválida. Use 'add' ou 'remove'.")
    end

    cargo = findfirst(r -> lowercase(r.name) == lowercase(cargo_name), guild.roles)
    if isnothing(cargo)
        return reply(client, ctx, content="Cargo não encontrado.")
    end

    if !haskey(server_data["special_roles"], tipo)
        server_data["special_roles"][tipo] = UInt64[]
    end

    if acao == "add"
        if !(cargo.id in server_data["special_roles"][tipo])
            push!(server_data["special_roles"][tipo], cargo.id)
            reply(client, ctx, content="Cargo $(cargo.name) adicionado às permissões de $tipo.")
        else
            reply(client, ctx, content="Cargo $(cargo.name) já está nas permissões de $tipo.")
        end
    elseif acao == "remove"
        if cargo.id in server_data["special_roles"][tipo]
            filter!(id -> id != cargo.id, server_data["special_roles"][tipo])
            reply(client, ctx, content="Cargo $(cargo.name) removido das permissões de $tipo.")
        else
            reply(client, ctx, content="Cargo $(cargo.name) não estava nas permissões de $tipo.")
        end
    end

    save_server_data(server_id, server_data)
    @info "Comando cargos concluído. Dados atualizados: $(server_data["special_roles"])"
end

"""
    estoque_command_handler(ctx)

Handler do comando /estoque. Gerencia o estoque da loja, permitindo abastecimento e definição de preços.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de estoque.
"""
function estoque_command_handler(ctx)
    @info "Comando /estoque foi acionado"

    if length(ctx.interaction.data.options) < 4
        return reply(client, ctx, content="Uso incorreto. Use: /estoque <comum> <incomum> <raro> <muito_raro>")
    end

    common = ctx.interaction.data.options[1].value
    uncommon = ctx.interaction.data.options[2].value
    rare = ctx.interaction.data.options[3].value
    very_rare = ctx.interaction.data.options[4].value

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)
    
    if !check_permissions(ctx.interaction.member, nothing, "loja", server_data)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    server_data["stock_items"] = Dict()

    rarities = Dict(
        "common" => common,
        "uncommon" => uncommon,
        "rare" => rare,
        "very rare" => very_rare
    )

    csv_file = isfile("items_$(server_id).csv") ? "items_$(server_id).csv" : "items.csv"

    try
        all_items = CSV.read(csv_file, DataFrame)
    catch
        return reply(client, ctx, content="Erro: O arquivo de itens '$csv_file' não foi encontrado.")
    end

    reply(client, ctx, content="Criando novo estoque. Por favor, defina os preços para cada item.")

    for (rarity, count) in rarities
        available_items = filter(row -> row.Rarity == rarity, all_items)
        available_count = nrow(available_items)

        if available_count < count
            count = available_count
        end

        if count > 0
            items = available_items[rand(1:nrow(available_items), count), :]
            server_data["stock_items"][rarity] = Dict(
                "Name" => items.Name,
                "Value" => String[],
                "Quantity" => fill(1, count),
                "Text" => items.Text
            )

            for name in server_data["stock_items"][rarity]["Name"]
                price_set = false
                attempts = 0
                while !price_set && attempts < 3
                    reply(client, ctx, content="Digite o preço para $name (em moedas):")
                    response = wait_for_message(ctx)
                    if response === nothing
                        break
                    end
                    try
                        price = parse(Int, response)
                        push!(server_data["stock_items"][rarity]["Value"], string(price))
                        update_item_price(server_id, name, string(price))
                        reply(client, ctx, content="Preço de $name definido como $price moedas e salvo.")
                        price_set = true
                    catch
                        reply(client, ctx, content="Por favor, digite um número inteiro válido.")
                        attempts += 1
                    end
                end

                if !price_set
                    preco_padrao = get(get(config, "precos_padroes", Dict()), "item_padrao", 100)
                    reply(client, ctx, content="Falha ao definir preço para $name. Definindo preço padrão de $preco_padrao moedas.")
                    push!(server_data["stock_items"][rarity]["Value"], string(preco_padrao))
                    update_item_price(server_id, name, string(preco_padrao))
                end
            end
        end
    end

    save_server_data(server_id, server_data)

    summary = "Novo estoque criado com:\n"
    for (rarity, items) in server_data["stock_items"]
        summary *= "- $(length(items["Name"])) itens $rarity\n"
    end

    reply(client, ctx, content=summary)
    reply(client, ctx, content="Estoque atualizado com sucesso e valores salvos!")
end

"""
    loja_command_handler(ctx)

Handler do comando /loja. Exibe os itens disponíveis na loja para o personagem selecionado.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com a lista de itens da loja e saldo do personagem.
"""
function loja_command_handler(ctx)
    @info "Comando /loja foi acionado"

    server_id = string(ctx.interaction.guild_id)
    user_id = string(ctx.interaction.member.user.id)
    server_data = load_server_data(server_id)

    if isempty(get(server_data, "stock_items", Dict()))
        return reply(client, ctx, content="A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
    end

    user_characters = get(server_data["characters"], user_id, Dict())
    if isempty(user_characters)
        return reply(client, ctx, content="Você não tem nenhum personagem. Crie um personagem primeiro antes de acessar a loja.")
    end

    reply(client, ctx, content="Escolha o personagem para ver a loja:")
    for character in keys(user_characters)
        reply(client, ctx, content=character)
    end

    response = wait_for_message(ctx)
    if response === nothing
        return
    end
    selected_character = strip(response)

    if !haskey(user_characters, selected_character)
        return reply(client, ctx, content="Personagem inválido selecionado.")
    end

    all_items = []
    for (rarity, items) in server_data["stock_items"]
        for (name, value, quantity, text) in zip(items["Name"], items["Value"], items["Quantity"], items["Text"])
            if quantity > 0
                push!(all_items, Dict(
                    "Name" => name,
                    "Value" => value,
                    "Quantity" => quantity,
                    "Text" => text
                ))
            end
        end
    end

    if isempty(all_items)
        return reply(client, ctx, content="Não há itens disponíveis na loja no momento.")
    end

    for item in all_items
        reply(client, ctx, content="""
        **$(item["Name"])**
        Preço: $(item["Value"]) moedas
        Quantidade: $(item["Quantity"])
        Descrição: $(item["Text"])
        """)
    end

    reply(client, ctx, content="Seu dinheiro: $(user_characters[selected_character]["dinheiro"]) moedas")
end

"""
    inserir_command_handler(ctx)

Handler do comando /inserir. Permite inserir um novo item no estoque da loja, definindo raridade, quantidade e valor.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de inserção.
"""
"""
    inserir_command_handler(ctx)

Handler do comando /inserir. Permite inserir um novo item no estoque da loja, definindo raridade, quantidade e valor.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de inserção.
"""
"""
    inserir_command_handler(ctx)

Handler do comando /inserir. Permite inserir um novo item no estoque da loja, definindo raridade, quantidade e valor.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de inserção.
"""
function inserir_command_handler(ctx)
    @info "Comando /inserir foi acionado"

    if length(ctx.interaction.data.options) < 3
        return reply(client, ctx, content="Uso incorreto. Use: /inserir <raridade> <item> <quantidade> [valor]")
    end

    raridade = ctx.interaction.data.options[1].value
    item = ctx.interaction.data.options[2].value
    quantidade = parse(Int, ctx.interaction.data.options[3].value)
    valor = length(ctx.interaction.data.options) >= 4 ? ctx.interaction.data.options[4].value : nothing

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)
    
    if !check_permissions(ctx.interaction.member, nothing, "loja", server_data)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    if !haskey(server_data, "stock_items") || isempty(server_data["stock_items"])
        server_data["stock_items"] = Dict()
    end
    
    if !haskey(server_data["stock_items"], raridade)
        server_data["stock_items"][raridade] = Dict(
            "Name" => String[],
            "Value" => String[],
            "Quantity" => Int[],
            "Text" => String[]
        )
    end

    stock = server_data["stock_items"][raridade]

    if item in stock["Name"]
        index = findfirst(==(item), stock["Name"])
        stock["Quantity"][index] += quantidade
        if !isnothing(valor)
            stock["Value"][index] = string(valor)
            update_item_price(server_id, item, string(valor))
        end
    else
        push!(stock["Name"], item)
        push!(stock["Quantity"], quantidade)
        if !isnothing(valor)
            push!(stock["Value"], string(valor))
            update_item_price(server_id, item, string(valor))
        else
            price = get(get(server_data, "prices", Dict()), item, string(get(get(config, "precos_padroes", Dict()), "item_padrao", 100)))
            push!(stock["Value"], price)
        end
        push!(stock["Text"], "Descrição não disponível")
    end

    save_server_data(server_id, server_data)
    reply(client, ctx, content="Item '$item' inserido no estoque com sucesso.")
end

"""
    remover_command_handler(ctx)

Handler do comando /remover. Permite remover um item do estoque da loja, parcial ou totalmente.

- `ctx`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de remoção.
"""
function remover_command_handler(ctx)
    @info "Comando /remover foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do item a ser removido.")
    end

    item = ctx.interaction.data.options[1].value
    quantidade = length(ctx.interaction.data.options) >= 2 ? parse(Int, ctx.interaction.data.options[2].value) : nothing

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)
    
    if !check_permissions(ctx.interaction.member, nothing, "loja", server_data)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end
    
    item_found = false
    for (rarity, stock) in get(server_data, "stock_items", Dict())
        if item in stock["Name"]
            index = findfirst(==(item), stock["Name"])
            if isnothing(quantidade) || quantidade >= stock["Quantity"][index]
                deleteat!(stock["Name"], index)
                deleteat!(stock["Value"], index)
                deleteat!(stock["Quantity"], index)
                deleteat!(stock["Text"], index)
                reply(client, ctx, content="Item '$item' removido completamente do estoque.")
            else
                stock["Quantity"][index] -= quantidade
                reply(client, ctx, content="Removido $quantidade de '$item'. Quantidade restante: $(stock["Quantity"][index])")
            end
            item_found = true
            break
        end
    end

    if !item_found
        reply(client, ctx, content="Item '$item' não encontrado no estoque.")
    end

    save_server_data(server_id, server_data)
end

"""
    limpar_estoque_command_handler(ctx)

Handler do comando /limpar_estoque. Limpa completamente o estoque da loja do servidor.

- `ctx`: Contexto da interação Discord.

Responde ao usuário confirmando a limpeza do estoque.
"""
"""
    limpar_estoque_command_handler(ctx)

Handler do comando /limpar_estoque. Limpa completamente o estoque da loja do servidor.

- `ctx`: Contexto da interação Discord.

Responde ao usuário confirmando a limpeza do estoque.
"""
function limpar_estoque_command_handler(ctx)
    @info "Comando /limpar_estoque foi acionado"

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)
    
    if !check_permissions(ctx.interaction.member, nothing, "loja", server_data)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    server_data["stock_items"] = Dict()
    save_server_data(server_id, server_data)

    reply(client, ctx, content="O estoque foi limpo com sucesso.")
end

function backup_command_handler(ctx)
    @info "Comando /backup foi acionado"
    user    = ctx.interaction.member
    guild   = ctx.interaction.guild_id   |> (t -> get_guild(client, t))   |> fetch |> (u -> u.val)
    channel = ctx.interaction.channel_id |> (r -> get_channel(client, r)) |> fetch |> (s -> s.val)
    permissions = Ekztazy.permissions_in(user, guild, channel)
    if !has_permission(permissions, PERM_ADMINISTRATOR)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    backup_data = ctx.interaction.guild_id |> string |> load_server_data |> JSON3.write
    
    if length(backup_data) <= 2000
        reply(client, ctx, content="```json\n$backup_data\n```")
    else
        open("backup_$(ctx.interaction.guild_id).json", "w") do f
            JSON3.write(f, backup_data)
        end
        reply(client, ctx, content="O backup é muito grande para ser enviado como mensagem. Um arquivo foi criado no servidor.")
    end
end

function mensagens_command_handler(ctx)
    @info "Comando /mensagens foi acionado"

    if length(ctx.interaction.data.options) < 2
        return reply(client, ctx, content="Uso incorreto. Use: /mensagens <tipo> <mensagem>")
    end

    tipo = ctx.interaction.data.options[1].value
    mensagem = ctx.interaction.data.options[2].value

    user    = ctx.interaction.member
    guild   = ctx.interaction.guild_id   |> (t -> get_guild(client, t))   |> fetch |> (u -> u.val)
    channel = ctx.interaction.channel_id |> (r -> get_channel(client, r)) |> fetch |> (s -> s.val)
    permissions = Ekztazy.permissions_in(user, guild, channel)
    if !has_permission(permissions, PERM_ADMINISTRATOR)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    if !haskey(server_data, "messages")
        server_data["messages"] = Dict("trabalho" => String[], "crime" => String[])
    end

    push!(get!(server_data["messages"], tipo, String[]), mensagem)
    save_server_data(server_id, server_data)
    reply(client, ctx, content="Mensagem adicionada ao tipo $tipo com sucesso.")
end

function tiers_command_handler(ctx)
    @info "Comando /tiers foi acionado"

    if length(ctx.interaction.data.options) < 4
        return reply(client, ctx, content="Uso incorreto. Use: /tiers <tier> <nivel_min> <nivel_max> <recompensa>")
    end

    tier = ctx.interaction.data.options[1].value
    nivel_min = parse(Int, ctx.interaction.data.options[2].value)
    nivel_max = parse(Int, ctx.interaction.data.options[3].value)
    recompensa = parse(Int, ctx.interaction.data.options[4].value)

    user    = ctx.interaction.member
    guild   = ctx.interaction.guild_id   |> (t -> get_guild(client, t))   |> fetch |> (u -> u.val)
    channel = ctx.interaction.channel_id |> (r -> get_channel(client, r)) |> fetch |> (s -> s.val)
    permissions = Ekztazy.permissions_in(user, guild, channel)
    if !has_permission(permissions, PERM_ADMINISTRATOR)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    if !haskey(server_data, "tiers")
        server_data["tiers"] = Dict()
    end

    server_data["tiers"][tier] = Dict(
        "nivel_min" => nivel_min,
        "nivel_max" => nivel_max,
        "recompensa" => recompensa
    )

    save_server_data(server_id, server_data)
    reply(client, ctx, content="Tier '$tier' definido para níveis $nivel_min-$nivel_max com recompensa de $recompensa moedas.")
end

function prob_crime_command_handler(ctx)
    @info "Comando /probabilidade_crime foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça a probabilidade de sucesso do crime.")
    end

    probabilidade = parse(Int, ctx.interaction.data.options[1].value)

    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)
    
    if !check_permissions(ctx.interaction.member, nothing, "loja", server_data)
        return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end
    
    if !(0 <= probabilidade <= 100)
        return reply(client, ctx, content="Por favor, insira um valor entre 0 e 100.")
    end

    server_data["probabilidade_crime"] = probabilidade
    save_server_data(server_id, server_data)
    reply(client, ctx, content="Probabilidade de sucesso no crime definida para $probabilidade%.")
end

function rip_command_handler(ctx)
    @info "Comando /rip foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do personagem.")
    end

    character = ctx.interaction.data.options[1].value
    server_id = string(ctx.interaction.guild_id)
    server_data = load_server_data(server_id)

    user    = ctx.interaction.member
    guild   = ctx.interaction.guild_id   |> (t -> get_guild(client, t))   |> fetch |> (u -> u.val)
    channel = ctx.interaction.channel_id |> (r -> get_channel(client, r)) |> fetch |> (s -> s.val)
    permissions = Ekztazy.permissions_in(user, guild, channel)

    if !has_permission(permissions, PERM_ADMINISTRATOR) && !check_permissions(ctx.interaction.member, character, "marcos", server_data, false)
        if !check_permissions(ctx.interaction.member, character, "view", server_data, true)
            return reply(client, ctx, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        end
    end

    character_found = false
    owner_id = ""
    for (user_id, characters) in server_data["characters"]
        if haskey(characters, character)
            owner_id = user_id
            character_found = true
            break
        end
    end

    if !character_found
        return reply(client, ctx, content="Personagem $character não encontrado.")
    end

    reply(client, ctx, content="Tem certeza que deseja eliminar o personagem $character? Responda 'sim' para confirmar.")

    response = wait_for_message(ctx)
    if response === nothing || lowercase(strip(response)) != "sim"
        return reply(client, ctx, content="Eliminação cancelada.")
    end

    delete!(server_data["characters"][owner_id], character)
    if isempty(server_data["characters"][owner_id])
        delete!(server_data["characters"], owner_id)
    end

    save_server_data(server_id, server_data)
    reply(client, ctx, content="Personagem $character foi eliminado com sucesso.")
end

function inss_command_handler(ctx)
    @info "Comando /inss foi acionado"

    if isempty(ctx.interaction.data.options)
        return reply(client, ctx, content="Por favor, forneça o nome do personagem.")
    end

    character = ctx.interaction.data.options[1].value
    server_id = string(ctx.interaction.guild_id)
    user_id = string(ctx.interaction.member.user.id)
    server_data = load_server_data(server_id)

    user_characters = get(server_data["characters"], user_id, Dict())
    if !haskey(user_characters, character)
        return reply(client, ctx, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    if !haskey(server_data, "aposentados")
        server_data["aposentados"] = Dict()
    end

    server_data["aposentados"][character] = user_characters[character]
    delete!(user_characters, character)

    if isempty(user_characters)
        delete!(server_data["characters"], user_id)
    else
        server_data["characters"][user_id] = user_characters
    end

    save_server_data(server_id, server_data)
    reply(client, ctx, content="Personagem $character foi aposentado com sucesso e seus dados foram preservados.")
end

function register_guild_commands(client::Client, guild_id::UInt64)
    commands = [
        ApplicationCommand(
            name = "criar",
            description = "Cria um novo personagem",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "nome",
                    description = "Nome do novo personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "ajuda",
            description = "Mostra a mensagem de ajuda",
            application_id = APPLICATION_ID,
        ),
        ApplicationCommand(
            name = "up",
            description = "Adiciona Marcos a um personagem",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "marcos",
            description = "Mostra os Marcos de um personagem",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "mochila",
            description = "Mostra o inventário de um personagem",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "item",
                    description = "Nome do item (opcional)",
                    required = false
                )
            ]
        ),
        ApplicationCommand(
            name = "comprar",
            description = "Compra um item da loja",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "item",
                    description = "Nome do item",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "dinheiro",
            description = "Adiciona ou remove dinheiro de um personagem",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "quantidade",
                    description = "Quantidade de dinheiro (use número negativo para remover)",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "saldo",
            description = "Mostra o saldo de um personagem",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "pix",
            description = "Transfere dinheiro entre personagens",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "de_personagem",
                    description = "Nome do personagem que envia",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "para_personagem",
                    description = "Nome do personagem que recebe",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "quantidade",
                    description = "Quantidade de dinheiro a transferir",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "trabalhar",
            description = "Faz o personagem trabalhar para ganhar dinheiro",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "crime",
            description = "Tenta cometer um crime para ganhar dinheiro",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "cargos",
            description = "Gerencia cargos especiais",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "tipo",
                    description = "Tipo de permissão (saldo, marcos, loja)",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "acao",
                    description = "Ação a ser realizada (add, remove)",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "cargo",
                    description = "Nome do cargo",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "estoque",
            description = "Gerencia o estoque da loja",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 4,  # Integer
                    name = "comum",
                    description = "Quantidade de itens comuns",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "incomum",
                    description = "Quantidade de itens incomuns",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "raro",
                    description = "Quantidade de itens raros",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "muito_raro",
                    description = "Quantidade de itens muito raros",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "loja",
            description = "Mostra os itens disponíveis na loja",
            application_id = APPLICATION_ID
        ),
        ApplicationCommand(
            name = "inserir",
            description = "Insere um item no estoque",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "raridade",
                    description = "Raridade do item",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "item",
                    description = "Nome do item",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "quantidade",
                    description = "Quantidade do item",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "valor",
                    description = "Valor do item (opcional)",
                    required = false
                )
            ]
        ),
        ApplicationCommand(
            name = "remover",
            description = "Remove um item do estoque",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "item",
                    description = "Nome do item",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "quantidade",
                    description = "Quantidade a remover (opcional)",
                    required = false
                )
            ]
        ),
        ApplicationCommand(
            name = "limpar_estoque",
            description = "Limpa o estoque da loja",
            application_id = APPLICATION_ID
        ),
        ApplicationCommand(
            name = "backup",
            description = "Cria um backup dos dados do servidor",
            application_id = APPLICATION_ID
        ),
        ApplicationCommand(
            name = "mensagens",
            description = "Adiciona mensagens personalizadas",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "tipo",
                    description = "Tipo de mensagem (trabalho, crime)",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "mensagem",
                    description = "Mensagem a ser adicionada",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "tiers",
            description = "Configura os tiers de níveis",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "tier",
                    description = "Nome do tier",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "nivel_min",
                    description = "Nível mínimo do tier",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "nivel_max",
                    description = "Nível máximo do tier",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "recompensa",
                    description = "Recompensa do tier",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "probabilidade_crime",
            description = "Define a probabilidade de sucesso no crime",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 4,  # Integer
                    name = "probabilidade",
                    description = "Probabilidade de sucesso (0-100)",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "rip",
            description = "Remove um personagem permanentemente",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "inss",
            description = "Aposenta um personagem",
            application_id = APPLICATION_ID,
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        )
    ]

    try
        Ekztazy.bulk_overwrite_application_commands(client, guild_id, commands)
    catch e
        @error "Erro ao registrar comandos para a guild $guild_id" exception=(e, catch_backtrace())
    end
end

function register_commands_for_all_guilds(client::Client)
    @info "Registrando comandos globalmente"
    commands = [
        ApplicationCommand(
            name = "criar",
            description = "Cria um novo personagem",
            options = [
                Option(
                    type = 3,  # String
                    name = "nome",
                    description = "Nome do novo personagem",
                    required = true
                )
            ]
        ),        
        ApplicationCommand(
            name = "ajuda",
            description = "Mostra a mensagem de ajuda"
        ),
        ApplicationCommand(
            name = "up",
            description = "Adiciona Marcos a um personagem",
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "marcos",
            description = "Mostra os Marcos de um personagem",
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "mochila",
            description = "Mostra o inventário de um personagem",
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "item",
                    description = "Nome do item (opcional)",
                    required = false
                )
            ]
        ),
        ApplicationCommand(
            name = "comprar",
            description = "Compra um item da loja",
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "item",
                    description = "Nome do item",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "dinheiro",
            description = "Adiciona ou remove dinheiro de um personagem",
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "quantidade",
                    description = "Quantidade de dinheiro (use número negativo para remover)",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "saldo",
            description = "Mostra o saldo de um personagem",
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "pix",
            description = "Transfere dinheiro entre personagens",
            options = [
                Option(
                    type = 3,  # String
                    name = "de_personagem",
                    description = "Nome do personagem que envia",
                    required = true
                ),
                Option(
                    type = 3,  # String
                    name = "para_personagem",
                    description = "Nome do personagem que recebe",
                    required = true
                ),
                Option(
                    type = 4,  # Integer
                    name = "quantidade",
                    description = "Quantidade de dinheiro a transferir",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "trabalhar",
            description = "Faz o personagem trabalhar para ganhar dinheiro",
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        ),
        ApplicationCommand(
            name = "crime",
            description = "Tenta cometer um crime para ganhar dinheiro",
            options = [
                Option(
                    type = 3,  # String
                    name = "personagem",
                    description = "Nome do personagem",
                    required = true
                )
            ]
        )
    ]
    try
        @info "Tentando registrar comandos globalmente"
        Ekztazy.bulk_overwrite_application_commands(client, commands)
        @info "Comandos registrados globalmente com sucesso"
    catch e
        @error "Erro ao registrar comandos globalmente" exception=(e, catch_backtrace())
    end
end

# Configuração do cliente
client = Client(TOKEN, UInt64(APPLICATION_ID), intents(GUILDS, GUILD_MESSAGES), version=9)

# Adicionar handlers para cada comando
function register_command_handles()
    @info "Registrando comandos"
    command!(criar_command_handler, client, "criar", "Cria um novo personagem")
    command!(backup_command_handler, client, "backup", "Cria um backup dos dados do servidor")
    command!(ajuda_command_handler, client, "ajuda", "Mostra a mensagem de ajuda")
    command!(up_command_handler, client, "up", "Adiciona Marcos a um personagem")
    command!(marcos_command_handler, client, "marcos", "Mostra os Marcos de um personagem")
    command!(mochila_command_handler, client, "mochila", "Mostra o inventário de um personagem")
    command!(comprar_command_handler, client, "comprar", "Compra um item da loja")
    command!(dinheiro_command_handler, client, "dinheiro", "Adiciona ou remove dinheiro de um personagem")
    command!(saldo_command_handler, client, "saldo", "Mostra o saldo de um personagem")
    command!(pix_command_handler, client, "pix", "Transfere dinheiro entre personagens")
    command!(trabalhar_command_handler, client, "trabalhar", "Faz o personagem trabalhar para ganhar dinheiro")
    command!(crime_command_handler, client, "crime", "Tenta cometer um crime para ganhar dinheiro")
    command!(estoque_command_handler, client, "estoque", "Gerencia o estoque da loja")
    command!(loja_command_handler, client, "loja", "Mostra os itens disponíveis na loja")
    command!(inserir_command_handler, client, "inserir", "Insere um item no estoque")
    command!(remover_command_handler, client, "remover", "Remove um item do estoque")
    command!(limpar_estoque_command_handler, client, "limpar_estoque", "Limpa o estoque da loja")
    command!(mensagens_command_handler, client, "mensagens", "Adiciona mensagens personalizadas")
    command!(tiers_command_handler, client, "tiers", "Configura os tiers de níveis")
    command!(prob_crime_command_handler, client, "probabilidade_crime", "Define a probabilidade de sucesso no crime")
    command!(rip_command_handler, client, "rip", "Remove um personagem permanentemente")
    command!(inss_command_handler, client, "inss", "Aposenta um personagem")
    command!(cargos_command_handler, client, "cargos", "Gerencia cargos especiais")
    @info "Comandos registrados com sucesso"
end

# Handler para quando o bot entrar em uma nova guild
on_guild_create!(client) do ctx
    guild_id = UInt64(ctx.guild.id)
    @info "Bot entrou na guild: $guild_id. Registrando comandos..."
    try
        register_guild_commands(client, guild_id)
    catch e
        @error "Erro ao registrar comandos para a nova guild" exception=(e, catch_backtrace())
    end
end

# Tratamento de erros global
function custom_error_handler(c::Client, e::Exception, args...)
    @error "Ocorreu um erro" exception=(e, catch_backtrace())
    if isa(e, HTTP.WebSockets.WebSocketError)
        @warn "Erro de WebSocket detectado. Tentando reconectar..."
        sleep(5)  # Espera 5 segundos antes de tentar reconectar
        try
            start(c)
        catch reconnect_error
            @error "Falha ao reconectar" exception=(reconnect_error, catch_backtrace())
        end
    end
end

# Inicialização do bot
try
    @info "Gerando gestor de erros..."
    add_handler!(client, Handler(custom_error_handler, type=:OnError))
    @info "Gestor de erros gerado com sucesso. Inicializando comandos..."
    register_command_handles()
    @info "Comandos inicializados com sucesso. Iniciando o bot..."

    start(client)
catch e
    @error "Falha ao iniciar o bot" exception=(e, catch_backtrace())
end