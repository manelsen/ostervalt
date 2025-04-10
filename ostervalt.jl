using Discord
using YAML
using JSON3
using Dates
using Random
using DataFrames
using CSV
using Logging

# Configuração de logging
logger = SimpleLogger(stdout, Logging.Info)
global_logger(logger)

# Carregar variáveis de ambiente
const TOKEN = get(ENV, "DISCORD_TOKEN", "")
const DATABASE_URL = get(ENV, "DATABASE_URL", "")
const LOG_LEVEL = get(ENV, "LOG_LEVEL", "INFO")

if isempty(TOKEN)
    error("Token do Discord não encontrado. Certifique-se de definir DISCORD_TOKEN no ambiente.")
end

# Carregar configuração
function load_config()
    YAML.load_file("config.yaml")
end

const config = load_config()

# Sistema de Cache
mutable struct Cache
    data::Dict{String, Any}
    ttl::Int
    last_update::DateTime
end

function get_cache(key::String, cache::Cache)
    if haskey(cache.data, key) && (now() - cache.last_update).value < cache.ttl
        return cache.data[key]
    end
    return nothing
end

function set_cache(key::String, value::Any, cache::Cache)
    cache.data[key] = value
    cache.last_update = now()
end

const server_data_cache = Cache(Dict(), 300, now())

# Funções auxiliares
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

    # Garantir que todas as chaves necessárias existam
    data["characters"] = get(data, "characters", Dict())
    data["stock_items"] = get(data, "stock_items", Dict())
    data["special_roles"] = get(data, "special_roles", Dict())
    
    for key in ["saldo", "marcos", "loja"]
        data["special_roles"][key] = get(get(data, "special_roles", Dict()), key, [])
    end
    
    data["shop_items"] = get(data, "shop_items", nothing)
    data["messages"] = get(data, "messages", get(config, "messages", Dict()))
    data["tiers"] = get(data, "tiers", get(config, "tiers", Dict()))
    data["aposentados"] = get(data, "aposentados", Dict())
    data["prices"] = get(data, "prices", Dict())
    data["probabilidade_crime"] = get(data, "probabilidade_crime", get(get(config, "probabilidades", Dict()), "crime", 50))

    set_cache(server_id, data, server_data_cache)
    return data
end

function save_server_data(server_id::String, data::Dict)
    open("server_data_$server_id.json", "w") do f
        JSON3.write(f, data)
    end
    set_cache(server_id, data, server_data_cache)
    @info "Dados do servidor $server_id salvos e cache atualizado."
end

function update_item_price(server_id::String, item_name::String, value::String)
    data = load_server_data(server_id)
    data["prices"] = get(data, "prices", Dict())
    data["prices"][item_name] = value
    save_server_data(server_id, data)
    @info "Preço atualizado para $item_name: $value moedas"
end

function calculate_level(marcos::Float64)
    min(20, floor(Int, marcos) + 1)
end

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

function check_permissions(member::Discord.Member, character::Union{String, Nothing}, permission_type::String, server_data::Dict, allow_owner::Bool=true)
    user_id = string(member.user.id)
    is_owner = !isnothing(character) && haskey(get(server_data["characters"], user_id, Dict()), character)
    is_admin = :administrator in member.permissions
    has_special_role = any(role -> role.id in get(get(server_data["special_roles"], permission_type, []), [], Int64[]), member.roles)
    return allow_owner ? (is_owner || is_admin || has_special_role) : (is_admin || has_special_role)
end

function get_tier(nivel::Int, server_data::Dict)
    for (tier_name, tier_data) in get(server_data, "tiers", Dict())
        if tier_data["nivel_min"] <= nivel <= tier_data["nivel_max"]
            return tier_name
        end
    end
    return nothing
end

# Comandos do bot
function criar(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 1
        reply(c, m, "Por favor, forneça um nome para o personagem.")
        return
    end

    nome = join(args, " ")
    server_id = string(m.guild_id)
    user_id = string(m.author.id)
    server_data = load_server_data(server_id)

    limite_personagens = get(get(config, "limites", Dict()), "personagens_por_usuario", 2)
    user_characters = get(get(server_data["characters"], user_id, Dict()), Dict())

    if length(user_characters) >= limite_personagens
        reply(c, m, "Você já possui $limite_personagens personagens. Não é possível criar mais.")
        return
    end

    if haskey(user_characters, nome)
        reply(c, m, "Você já tem um personagem com o nome $nome. Por favor, escolha outro nome.")
        return
    end

    new_character = Dict(
        "marcos" => 0,
        "inventory" => [],
        "dinheiro" => 0,
        "nivel" => 0,
        "last_work_time" => nothing,
        "last_crime_time" => nothing,
        "estrelas" => 0
    )

    user_characters[nome] = new_character
    server_data["characters"][user_id] = user_characters

    save_server_data(server_id, server_data)

    reply(c, m, "Personagem $nome criado com sucesso e vinculado à sua conta Discord!")
end

function cargos(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 3
        reply(c, m, "Uso correto: !cargos <tipo> <acao> <cargo>")
        return
    end

    tipo, acao, cargo_name = args[1:3]

    if !(:administrator in m.member.permissions)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)

    if !(tipo in ["saldo", "marcos", "loja"])
        reply(c, m, "Tipo inválido. Use 'saldo', 'marcos' ou 'loja'.")
        return
    end

    if !(acao in ["add", "remove"])
        reply(c, m, "Ação inválida. Use 'add' ou 'remove'.")
        return
    end

    cargo = findfirst(r -> lowercase(r.name) == lowercase(cargo_name), m.guild.roles)
    if isnothing(cargo)
        reply(c, m, "Cargo não encontrado.")
        return
    end

    if !haskey(server_data["special_roles"], tipo)
        server_data["special_roles"][tipo] = Int64[]
    end

    if acao == "add"
        if !(cargo.id in server_data["special_roles"][tipo])
            push!(server_data["special_roles"][tipo], cargo.id)
            reply(c, m, "Cargo $(cargo.name) adicionado às permissões de $tipo.")
        else
            reply(c, m, "Cargo $(cargo.name) já está nas permissões de $tipo.")
        end
    elseif acao == "remove"
        if cargo.id in server_data["special_roles"][tipo]
            filter!(id -> id != cargo.id, server_data["special_roles"][tipo])
            reply(c, m, "Cargo $(cargo.name) removido das permissões de $tipo.")
        else
            reply(c, m, "Cargo $(cargo.name) não estava nas permissões de $tipo.")
        end
    end

    save_server_data(server_id, server_data)
    @info "Comando cargos concluído. Dados atualizados: $(server_data["special_roles"])"
end

function estoque(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 4
        reply(c, m, "Uso correto: !estoque <common> <uncommon> <rare> <very_rare>")
        return
    end

    common, uncommon, rare, very_rare = parse.(Int, args[1:4])

    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)
    
    if !check_permissions(m.member, nothing, "loja", server_data)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
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
        reply(c, m, "Erro: O arquivo de itens '$csv_file' não foi encontrado.")
        return
    end

    reply(c, m, "Criando novo estoque. Por favor, defina os preços para cada item.")

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

            reply(c, m, "Definindo preços para itens $rarity:")
            for name in server_data["stock_items"][rarity]["Name"]
                price_set = false
                attempts = 0
                while !price_set && attempts < 3
                    reply(c, m, "Digite o preço para $name (em moedas):")
                    response = readline()
                    try
                        price = parse(Int, response)
                        push!(server_data["stock_items"][rarity]["Value"], string(price))
                        update_item_price(server_id, name, string(price))
                        reply(c, m, "Preço de $name definido como $price moedas e salvo.")
                        price_set = true
                    catch
                        reply(c, m, "Por favor, digite um número inteiro válido.")
                        attempts += 1
                    end
                end

                if !price_set
                    preco_padrao = get(get(config, "precos_padroes", Dict()), "item_padrao", 100)
                    reply(c, m, "Falha ao definir preço para $name. Definindo preço padrão de $preco_padrao moedas.")
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

    reply(c, m, summary)
    reply(c, m, "Estoque atualizado com sucesso e valores salvos!")
end

function inserir(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 3
        reply(c, m, "Uso correto: !inserir <raridade> <item> <quantidade> [valor]")
        return
    end

    raridade, item = args[1:2]
    quantidade = parse(Int, args[3])
    valor = length(args) >= 4 ? parse(Int, args[4]) : nothing

    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)
    
    if !check_permissions(m.member, nothing, "loja", server_data)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    if !haskey(server_data, "stock_items") || isempty(server_data["stock_items"])
        server_data["stock_items"] = Dict()
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
        reply(c, m, "Item '$item' inserido no estoque com sucesso.")
    end
    
    function remover(c::Client, m::Discord.Message)
        args = split(m.content)[2:end]
        if length(args) < 1
            reply(c, m, "Uso correto: !remover <item> [quantidade]")
            return
        end
    
        item = args[1]
        quantidade = length(args) >= 2 ? parse(Int, args[2]) : nothing
    
        server_id = string(m.guild_id)
        server_data = load_server_data(server_id)
        
        if !check_permissions(m.member, nothing, "loja", server_data)
            reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
            return
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
                    reply(c, m, "Item '$item' removido completamente do estoque.")
                else
                    stock["Quantity"][index] -= quantidade
                    reply(c, m, "Removido $quantidade de '$item'. Quantidade restante: $(stock["Quantity"][index])")
                end
                item_found = true
                break
            end
        end
    
        if !item_found
            reply(c, m, "Item '$item' não encontrado no estoque.")
        end
    
        save_server_data(server_id, server_data)
    end
    
    function loja(c::Client, m::Discord.Message)
        server_id = string(m.guild_id)
        user_id = string(m.author.id)
        server_data = load_server_data(server_id)
    
        if isempty(get(server_data, "stock_items", Dict()))
            reply(c, m, "A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
            return
        end
    
        user_characters = get(get(server_data["characters"], user_id, Dict()), Dict())
        if isempty(user_characters)
            reply(c, m, "Você não tem nenhum personagem. Crie um personagem primeiro antes de acessar a loja.")
            return
        end
    
        reply(c, m, "Escolha o personagem para ver a loja:")
        for character in keys(user_characters)
            reply(c, m, character)
        end
    
        response = readline()
        selected_character = strip(response)
    
        if !haskey(user_characters, selected_character)
            reply(c, m, "Personagem inválido selecionado.")
            return
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
            reply(c, m, "Não há itens disponíveis na loja no momento.")
            return
        end
    
        for item in all_items
            reply(c, m, """
            **$(item["Name"])**
            Preço: $(item["Value"]) moedas
            Quantidade: $(item["Quantity"])
            Descrição: $(item["Text"])
            """)
        end
    
        reply(c, m, "Seu dinheiro: $(user_characters[selected_character]["dinheiro"]) moedas")
    end
    
    function up(c::Client, m::Discord.Message)
        args = split(m.content)[2:end]
        if length(args) < 1
            reply(c, m, "Por favor, forneça o nome do personagem.")
            return
        end
    
        character = join(args, " ")
        server_id = string(m.guild_id)
        server_data = load_server_data(server_id)
    
        if !check_permissions(m.member, character, "marcos", server_data, false)
            reply(c, m, get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
            return
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
                    reply(c, m, "$character subiu para o nível $new_level!")
                else
                    fraction_added = if marcos_to_add == 4
                        "1/4 de Marco"
                    elseif marcos_to_add == 2
                        "1/8 de Marco"
                    elseif marcos_to_add == 1
                        "1/16 de Marco"
                    else
                        "$marcos_to_add Marcos"
                    end
    
                    reply(c, m, "Adicionado $fraction_added para $character. Total: $(format_marcos(new_marcos)) (Nível $new_level)")
                end
    
                save_server_data(server_id, server_data)
                character_found = true
                break
            end
        end
    
        if !character_found
            reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
        end
    end
    
    function marcos(c::Client, m::Discord.Message)
        args = split(m.content)[2:end]
        if length(args) < 1
            reply(c, m, "Por favor, forneça o nome do personagem.")
            return
        end
    
        character = join(args, " ")
        server_id = string(m.guild_id)
        server_data = load_server_data(server_id)
    
        if !check_permissions(m.member, character, "marcos", server_data, false)
            reply(c, m, get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
            return
        end
    
        character_found = false
        for (user_id, characters) in server_data["characters"]
            if haskey(characters, character)
                character_data = characters[character]
                marcos = character_data["marcos"]
                level = calculate_level(marcos / 16)
                reply(c, m, "$character tem $(format_marcos(marcos)) (Nível $level)")
                character_found = true
                break
            end
        end
    
        if !character_found
            reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
        end
    end
    
    function mochila(c::Client, m::Discord.Message)
        args = split(m.content)[2:end]
        if length(args) < 1
            reply(c, m, "Por favor, forneça o nome do personagem.")
            return
        end
    
        character = args[1]
        item = length(args) > 1 ? join(args[2:end], " ") : nothing
    
        server_id = string(m.guild_id)
        user_id = string(m.author.id)
        server_data = load_server_data(server_id)
    
        if !check_permissions(m.member, character, "view", server_data, true)
            reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
            return
        end
    
        character_data = get(get(server_data["characters"], user_id, Dict()), character, nothing)
        if isnothing(character_data)
            reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
            return
        end
    
        inventory = get(character_data, "inventory", [])
        if isempty(inventory)
            reply(c, m, "O inventário de $character está vazio.")
            return
        end
    
        if !isnothing(item)
            if item in inventory
                item_count = count(==(item), inventory)
                item_description = get_item_description(server_data, item)
                reply(c, m, "**$item** (x$item_count)\nDescrição: $item_description")
            else
                reply(c, m, "O item '$item' não está na mochila de $character.")
            end
        else
            item_counts = Dict{String, Int}()
            for i in inventory
                item_counts[i] = get(item_counts, i, 0) + 1
            end
            
            items_formatted = join(["**$item** (x$count)" for (item, count) in item_counts], ", ")
            reply(c, m, "Inventário de $character: $items_formatted")
        end
    end
    
    function get_item_description(server_data::Dict, item_name::String)
        for (_, rarity_items) in get(server_data, "stock_items", Dict())
            if item_name in get(rarity_items, "Name", [])
                index = findfirst(==(item_name), rarity_items["Name"])
                return get(rarity_items, "Text", [])[index]
            end
        end
        return "Descrição não disponível."
    end
    
    function comprar(c::Client, m::Discord.Message)
        args = split(m.content)[2:end]
        if length(args) < 2
            reply(c, m, "Uso correto: !comprar <personagem> <item>")
            return
        end
    
        character = args[1]
        item = join(args[2:end], " ")
    
        server_id = string(m.guild_id)
        user_id = string(m.author.id)
        server_data = load_server_data(server_id)
    
        if !check_permissions(m.member, character, "view", server_data, true)
            reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
            return
        end
    
        user_characters = get(server_data["characters"], user_id, Dict())
        if !haskey(user_characters, character)
            reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
            return
        end
    
        if isempty(get(server_data, "stock_items", Dict()))
            reply(c, m, "A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
            return
        end
    
        character_data = user_characters[character]
        item_found = false
        for (rarity, items) in server_data["stock_items"]
            if item in items["Name"]
                item_index = findfirst(==(item), items["Name"])
                if items["Quantity"][item_index] > 0
                    item_value = parse(Int, items["Value"][item_index])
    
                    if character_data["dinheiro"] < item_value
                        reply(c, m, "$character não tem dinheiro suficiente para comprar $item. Preço: $item_value, Dinheiro disponível: $(character_data["dinheiro"])")
                        return
                    end
    
                    character_data["dinheiro"] -= item_value
                    push!(character_data["inventory"], item)
    
                    items["Quantity"][item_index] -= 1
    
                    reply(c, m, "$character comprou $item por $item_value moedas. Dinheiro restante: $(character_data["dinheiro"])")
                    save_server_data(server_id, server_data)
                    item_found = true
                else
                    reply(c, m, "Desculpe, $item está fora de estoque.")
                    item_found = true
                end
                break
            end
        end
    
        if !item_found
            reply(c, m, "Item '$item' não encontrado na loja.")
        end
    end
    
    function dinheiro(c::Client, m::Discord.Message)
        args = split(m.content)[2:end]
        if length(args) < 2
            reply(c, m, "Uso correto: !dinheiro <personagem> <quantidade>")
            return
        end
    
        character = args[1]
        amount = parse(Int, args[2])
    
        server_id = string(m.guild_id)
        server_data = load_server_data(server_id)
    
        if !check_permissions(m.member, character, "saldo", server_data, false)
            reply(c, m, get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
            return
        end
    
        character_found = false
        for (user_id, characters) in server_data["characters"]
            if haskey(characters, character)
                character_data = characters[character]
                character_data["dinheiro"] += amount
    
                if amount > 0
                    reply(c, m, "Adicionado $amount moedas ao saldo de $character. Novo saldo: $(character_data["dinheiro"]) moedas.")
                else
                    reply(c, m, "Removido $(abs(amount)) moedas do saldo de $character. Novo saldo: $(character_data["dinheiro"]) moedas.")
                end
    
                save_server_data(server_id, server_data)
                character_found = true
            break
        end
    end

    if !character_found
        reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

function saldo(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 1
        reply(c, m, "Por favor, forneça o nome do personagem.")
        return
    end

    character = join(args, " ")
    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)

    if !check_permissions(m.member, character, "view", server_data, true)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    user_id = string(m.author.id)
    user_characters = get(server_data["characters"], user_id, Dict())

    if haskey(user_characters, character)
        character_data = user_characters[character]
        money = get(character_data, "dinheiro", 0)
        reply(c, m, "$character tem $money moedas.")
    else
        reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

function pix(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 3
        reply(c, m, "Uso correto: !pix <personagem_origem> <personagem_destino> <quantidade>")
        return
    end

    from_character, to_character = args[1:2]
    amount = parse(Int, args[3])

    if amount <= 0
        reply(c, m, "A quantidade deve ser maior que zero.")
        return
    end

    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)

    user_id = string(m.author.id)
    user_characters = get(server_data["characters"], user_id, Dict())

    if !haskey(user_characters, from_character)
        reply(c, m, "Você não possui um personagem chamado $from_character.")
        return
    end

    if any(char -> char == to_character, keys(user_characters))
        reply(c, m, "Não é possível transferir moedas para um de seus próprios personagens.")
        return
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
        reply(c, m, "O personagem destinatário '$to_character' não foi encontrado ou é de sua propriedade.")
        return
    end

    sender_data = user_characters[from_character]

    if sender_data["dinheiro"] < amount
        reply(c, m, "$from_character não tem moedas suficientes. Saldo disponível: $(sender_data["dinheiro"])")
        return
    end

    sender_data["dinheiro"] -= amount
    recipient_data["dinheiro"] += amount

    save_server_data(server_id, server_data)

    reply(c, m, "Transferência realizada com sucesso!\n$from_character enviou $amount moedas para $to_character.\nNovo saldo de $from_character: $(sender_data["dinheiro"]) moedas.")
end

function limpar_estoque(c::Client, m::Discord.Message)
    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)
    server_data["stock_items"] = Dict()

    if !check_permissions(m.member, nothing, "loja", server_data)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    save_server_data(server_id, server_data)

    reply(c, m, "O estoque foi limpo com sucesso.")
end

function backup(c::Client, m::Discord.Message)
    if !(:administrator in m.member.permissions)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)

    backup_data = JSON3.write(server_data)
    if length(backup_data) <= 2000
        reply(c, m, "```json\n$backup_data\n```")
    else
        open("backup_$server_id.json", "w") do f
            JSON3.write(f, server_data)
        end
        reply(c, m, "O backup é muito grande para ser enviado como mensagem. Um arquivo foi criado no servidor.")
    end
end

function listar_comandos(c::Client, m::Discord.Message)
    comandos = ["criar", "cargos", "estoque", "inserir", "remover", "loja", "up", "marcos", "mochila", "comprar", "dinheiro", "saldo", "pix", "limpar_estoque", "backup", "listar_comandos", "mensagens", "tiers", "trabalhar", "probabilidade_crime", "crime", "rip", "inss", "ajuda"]
    reply(c, m, "Comandos disponíveis: $(join(comandos, ", "))")
end

function mensagens(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 2
        reply(c, m, "Uso correto: !mensagens <tipo> <mensagem>")
        return
    end

    tipo = args[1]
    mensagem = join(args[2:end], " ")

    if !(:administrator in m.member.permissions)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)

    if !haskey(server_data, "messages")
        server_data["messages"] = Dict("trabalho" => String[], "crime" => String[])
    end

    push!(get!(server_data["messages"], tipo, String[]), mensagem)
    save_server_data(server_id, server_data)
    reply(c, m, "Mensagem adicionada ao tipo $tipo com sucesso.")
end

function tiers(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 4
        reply(c, m, "Uso correto: !tiers <tier> <nivel_min> <nivel_max> <recompensa>")
        return
    end

    tier, nivel_min, nivel_max, recompensa = args[1], parse(Int, args[2]), parse(Int, args[3]), parse(Int, args[4])

    if !(:administrator in m.member.permissions)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    server_id = string(m.guild_id)
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
    reply(c, m, "Tier '$tier' definido para níveis $nivel_min-$nivel_max com recompensa de $recompensa moedas.")
end

function trabalhar(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 1
        reply(c, m, "Por favor, forneça o nome do personagem.")
        return
    end

    character = join(args, " ")
    server_id = string(m.guild_id)
    user_id = string(m.author.id)
    server_data = load_server_data(server_id)

    if !check_permissions(m.member, character, "view", server_data, true)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    user_characters = get(server_data["characters"], user_id, Dict())
    if !haskey(user_characters, character)
        reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
        return
    end

    character_data = user_characters[character]

    last_work_time = get(character_data, "last_work_time", nothing)
    now = Dates.now()
    intervalo_trabalhar = get(get(config, "limites", Dict()), "intervalo_trabalhar", 86400)
    if !isnothing(last_work_time)
        delta = now - DateTime(last_work_time)
        if Dates.value(delta) < intervalo_trabalhar * 1000
            reply(c, m, get(config["messages"]["erros"], "acao_frequente", "Você já trabalhou recentemente. Aguarde um pouco para trabalhar novamente."))
            return
        end
    end

    nivel = get(character_data, "nivel", 0)
    tier_name = get_tier(nivel, server_data)
    if isnothing(tier_name)
        reply(c, m, "Nenhum tier definido para o seu nível. Contate um administrador.")
        return
    end

    tier = server_data["tiers"][tier_name]
    recompensa = tier["recompensa"]
    character_data["dinheiro"] += recompensa
    character_data["last_work_time"] = string(now)

    mensagens = get(get(server_data, "messages", Dict()), "trabalho", get(config["messages"], "trabalho", []))
    mensagem = isempty(mensagens) ? "Você trabalhou duro e ganhou sua recompensa!" : rand(mensagens)

    save_server_data(server_id, server_data)
    reply(c, m, "$mensagem\nVocê ganhou $recompensa moedas. Saldo atual: $(character_data["dinheiro"]) moedas.")
end

function probabilidade_crime(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 1
        reply(c, m, "Por favor, forneça a probabilidade de sucesso (0 a 100).")
        return
    end

    probabilidade = parse(Int, args[1])

    server_id = string(m.guild_id)
    server_data = load_server_data(server_id)
    
    if !check_permissions(m.member, nothing, "loja", server_data)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end
    
    if !(0 <= probabilidade <= 100)
        reply(c, m, "Por favor, insira um valor entre 0 e 100.")
        return
    end

    server_data["probabilidade_crime"] = probabilidade
    save_server_data(server_id, server_data)
    reply(c, m, "Probabilidade de sucesso no crime definida para $probabilidade%.")
end

function crime(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 1
        reply(c, m, "Por favor, forneça o nome do personagem.")
        return
    end

    character = join(args, " ")
    server_id = string(m.guild_id)
    user_id = string(m.author.id)
    server_data = load_server_data(server_id)

    if !check_permissions(m.member, character, "view", server_data, true)
        reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        return
    end

    user_characters = get(server_data["characters"], user_id, Dict())
    if !haskey(user_characters, character)
        reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
        return
    end

    character_data = user_characters[character]

    last_crime_time = get(character_data, "last_crime_time", nothing)
    now = Dates.now()
    intervalo_crime = get(get(config, "limites", Dict()), "intervalo_crime", 86400)
    if !isnothing(last_crime_time)
        delta = now - DateTime(last_crime_time)
        if Dates.value(delta) < intervalo_crime * 1000
            reply(c, m, get(config["messages"]["erros"], "acao_frequente", "Você já cometeu um crime recentemente. Aguarde um pouco para tentar novamente."))
            return
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
    reply(c, m, "$mensagem\n$resultado\nSaldo atual: $(character_data["dinheiro"]) moedas.")
end

function rip(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 1
        reply(c, m, "Por favor, forneça o nome do personagem a ser eliminado.")
        return
    end

    character = join(args, " ")
    server_id = string
    (m.guild_id)
    server_data = load_server_data(server_id)

    # Verificar permissões
    if :administrator in m.member.permissions || check_permissions(m.member, character, "marcos", server_data, false)
        # Pode ver todos os personagens
    else
        # Usuário comum só pode ver seus próprios personagens
        if !check_permissions(m.member, character, "view", server_data, true)
            reply(c, m, get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
            return
        end
    end

    # Encontrar o personagem
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
        reply(c, m, "Personagem $character não encontrado.")
        return
    end

    # Confirmação
    reply(c, m, "Tem certeza que deseja eliminar o personagem $character? Responda 'sim' para confirmar.")

    response = readline()
    if lowercase(strip(response)) != "sim"
        reply(c, m, "Eliminação cancelada.")
        return
    end

    # Remover o personagem
    delete!(server_data["characters"][owner_id], character)
    if isempty(server_data["characters"][owner_id])
        delete!(server_data["characters"], owner_id)
    end

    save_server_data(server_id, server_data)
    reply(c, m, "Personagem $character foi eliminado com sucesso.")
end

function inss(c::Client, m::Discord.Message)
    args = split(m.content)[2:end]
    if length(args) < 1
        reply(c, m, "Por favor, forneça o nome do personagem.")
        return
    end

    character = join(args, " ")
    server_id = string(m.guild_id)
    user_id = string(m.author.id)
    server_data = load_server_data(server_id)

    user_characters = get(server_data["characters"], user_id, Dict())
    if !haskey(user_characters, character)
        reply(c, m, get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
        return
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
    reply(c, m, "Personagem $character foi aposentado com sucesso e seus dados foram preservados.")
end

function ajuda(c::Client, m::Discord.Message)
    embed = Discord.Embed(
        title="Ajuda do Bot RPG",
        description="Oi! Eu sou Ostervalt, Contador e Guarda-Livros do Reino de Tremond. Estou um pouco nervoso, mas vou tentar explicar os comandos disponíveis. Por favor, não grite!",
        color=0xFFA500
    )

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
        ("crime", "Arrisque ganhar ou perder dinheiro. Mas crime não compensa e é muito, muito assustador!"),
    ]

    for (nome, descricao) in comandos
        Discord.add_field!(embed, name="!$nome", value=descricao, inline=false)
    end

    Discord.set_footer!(embed, text="Lembre-se, se precisar de mais ajuda, é só chamar! Mas, por favor, não grite. Coelhos têm ouvidos sensíveis!")

    reply(c, m, embed=embed)
end

# Configuração e execução do bot
client = Client(TOKEN; prefix="!")

# Adicionar handlers para cada comando
add_command!(client, :criar, criar)
add_command!(client, :cargos, cargos)
add_command!(client, :estoque, estoque)
add_command!(client, :inserir, inserir)
add_command!(client, :remover, remover)
add_command!(client, :loja, loja)
add_command!(client, :up, up)
add_command!(client, :marcos, marcos)
add_command!(client, :mochila, mochila)
add_command!(client, :comprar, comprar)
add_command!(client, :dinheiro, dinheiro)
add_command!(client, :saldo, saldo)
add_command!(client, :pix, pix)
add_command!(client, :limpar_estoque, limpar_estoque)
add_command!(client, :backup, backup)
add_command!(client, :listar_comandos, listar_comandos)
add_command!(client, :mensagens, mensagens)
add_command!(client, :tiers, tiers)
add_command!(client, :trabalhar, trabalhar)
add_command!(client, :probabilidade_crime, probabilidade_crime)
add_command!(client, :crime, crime)
add_command!(client, :rip, rip)
add_command!(client, :inss, inss)
add_command!(client, :ajuda, ajuda)

# Tratamento de erros global
function on_error(c::Client, event::String, args...)
    @error "Erro no evento $event: $args"
end

add_handler!(client, :on_error, on_error)

# Inicialização do bot
open(client)
wait(client)