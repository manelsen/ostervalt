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

function carregar_configuracao()
    YAML.load_file("config.yaml")
end

const config = carregar_configuracao()

"""
    Cache

Estrutura para armazenamento em cache de dados temporários.

# Campos
- `dados::Dict{String, Any}`: Dados armazenados em cache.
- `tempo_vida::Int`: Tempo de vida do cache em segundos.
- `ultima_atualizacao::DateTime`: Momento da última atualização do cache.
"""
mutable struct Cache
    dados::Dict{String, Any}
    tempo_vida::Int
    ultima_atualizacao::DateTime
end

"""
    obter_cache(chave::String, cache::Cache) -> Any

Obtém um valor do cache se ainda estiver válido.

- `key`: Chave de busca.
- `cache`: Instância de Cache.

Retorna o valor armazenado ou `nothing` se expirado ou não encontrado.
"""
function obter_cache(chave::String, cache::Cache)
    if haskey(cache.data, key) && (now() - cache.last_update).value < cache.ttl
        return cache.data[key]
    end
    return nothing
end

"""
    definir_cache(chave::String, valor::Any, cache::Cache)

Armazena um valor no cache e atualiza o timestamp.

- `key`: Chave de armazenamento.
- `value`: Valor a ser armazenado.
- `cache`: Instância de Cache.
"""
function definir_cache(chave::String, valor::Any, cache::Cache)
    cache.data[key] = value
    cache.last_update = now()
end

const cache_dados_servidor = Cache(Dict(), 300, now())

"""
    carregar_dados_servidor(id_servidor::String) -> Dict

Carrega os dados persistentes de um servidor Discord a partir de arquivo JSON.
Utiliza cache para otimizar leituras frequentes.

- `id_servidor`: ID do servidor Discord.

Retorna um dicionário com todos os dados do servidor.
"""
function carregar_dados_servidor(id_servidor::String)
    dados_em_cache = obter_cache(id_servidor, cache_dados_servidor)
    if !isnothing(cached_dados)
        return dados_em_cache
    end

    data = Dict()
    if isfile("dados_servidor_$id_servidor.json")
        open("dados_servidor_$id_servidor.json", "r") do f
            data = JSON3.read(f, Dict)
        end
    end

    data["personagens"]    = get(dados, "personagens",    Dict())
    data["itens_estoque"]   = get(dados, "itens_estoque",   Dict())
    data["special_roles"] = get(dados, "special_roles", Dict())
    
    for key in ["saldo", "marcos", "loja"]
        data["special_roles"][key] = get(data["special_roles"], key, UInt64[])
    end
    
    data["itens_loja"]          = get(dados, "itens_loja", nothing)
    data["messages"]            = get(dados, "messages", get(config, "messages", Dict()))
    data["tiers"]               = get(dados, "tiers", get(config, "tiers", Dict()))
    data["aposentados"]         = get(dados, "aposentados", Dict())
    data["precos"]              = get(dados, "precos", Dict())
    data["probabilidade_crime"] = get(dados, "probabilidade_crime", get(get(config, "probabilidades", Dict()), "crime", 50))

    definir_cache(id_servidor, data, cache_dados_servidor)
    return data
end

"""
    salvar_dados_servidor(id_servidor::String, dados::Dict)

Salva os dados do servidor Discord em arquivo JSON e atualiza o cache.

- `id_servidor`: ID do servidor Discord.
- `data`: Dicionário de dados a serem salvos.
"""
function salvar_dados_servidor(id_servidor::String, dados::Dict)
    open("dados_servidor_$id_servidor.json", "w") do f
        JSON3.write(f, dados)
    end
    definir_cache(id_servidor, data, cache_dados_servidor)
    @info "Dados do servidor $id_servidor salvos e cache atualizado."
end

"""
    atualizar_preco_item(id_servidor::String, nome_item::String, value::String)

Atualiza o preço de um item na base de dados do servidor.

- `id_servidor`: ID do servidor Discord.
- `nome_item`: Nome do item.
- `value`: Novo valor do item (string).
"""
function atualizar_preco_item(id_servidor::String, nome_item::String, value::String)
    data = carregar_dados_servidor(id_servidor)
    data["precos"] = get(dados, "precos", Dict())
    data["precos"][nome_item] = value
    salvar_dados_servidor(id_servidor, dados)
    @info "Preço atualizado para $nome_item: $value moedas"
end

"""
    calcular_nivel(marcos::Float64) -> Int

Calcula o nível de um personagem a partir da quantidade de Marcos.

- `marcos`: Quantidade de Marcos (pontos de experiência).

Retorna o nível correspondente (máximo 20).
"""
function calcular_nivel(marcos::Float64)
    min(20, floor(Int, marcos) + 1)
end

"""
    marcos_para_ganhar(nivel::Int) -> Int

Retorna a quantidade de Marcos a ser ganha para o próximo nível, de acordo com a configuração.

- `level`: Nível atual do personagem.

Retorna a quantidade de Marcos a ser adicionada.
"""
function marcos_para_ganhar(nivel::Int)
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
    formatar_marcos(partes_marcos::Int) -> String

Formata a quantidade de partes de Marcos em uma string legível, considerando frações e níveis.

- `marcos_parts`: Quantidade de partes de Marcos (1 Marco = 16 partes).

Retorna uma string formatada para exibição ao usuário.
"""
function formatar_marcos(partes_marcos::Int)
    marcos_completos = div(marcos_parts, 16)
    partes_restantes = mod(marcos_parts, 16)

    if partes_restantes == 0
        return "$marcos_completos Marcos"
    end

    level = calcular_nivel(marcos_parts / 16)

    if level <= 4
        return "$marcos_completos Marcos"
    elseif level <= 12
        return "$marcos_completos e $(div(partes_restantes, 4))/4 Marcos"
    elseif level <= 16
        return "$marcos_completos e $(div(partes_restantes, 2))/8 Marcos"
    else
        return "$marcos_completos e $partes_restantes/16 Marcos"
    end
end

"""
    verificar_permissoes(membro::Ekztazy.Member, personagem::Union{String, Nothing}, tipo_permissao::String, dados_servidor::Dict, permitir_proprietario::Bool=true) -> Bool

Verifica se o membro possui permissão para executar determinada ação, considerando dono do personagem, administrador ou cargo especial.

- `membro`: Membro do Discord.
- `personagem`: Nome do personagem (ou `nothing`).
- `permission_type`: Tipo de permissão ("marcos", "saldo", "loja", etc).
- `dados_servidor`: Dados do servidor.
- `allow_owner`: Se `true`, permite que o dono do personagem execute a ação.

Retorna `true` se permitido, `false` caso contrário.
"""
function verificar_permissoes(membro::Ekztazy.Member, personagem::Union{String, Nothing}, tipo_permissao::String, dados_servidor::Dict, permitir_proprietario::Bool=true)
    id_usuario = string(membro.user.id)
    eh_proprietario = !isnothing(personagem) && haskey(get(dados_servidor["personagens"], id_usuario, Dict()), personagem)
    eh_admin = :administrator in membro.permissoes
    tem_cargo_especial = any(role -> role.id in get(dados_servidor["special_roles"], permission_type, UInt64[]), membro.roles)
    return allow_owner ? (eh_proprietario || eh_admin || tem_cargo_especial) : (eh_admin || tem_cargo_especial)
end

"""
    obter_tier(nivel::Int, dados_servidor::Dict) -> Union{String, Nothing}

Obtém o nome do tier correspondente ao nível informado, de acordo com a configuração do servidor.

- `nivel`: Nível do personagem.
- `dados_servidor`: Dados do servidor.

Retorna o nome do tier ou `nothing` se não houver correspondência.
"""
function obter_tier(nivel::Int, dados_servidor::Dict)
    for (nome_tier, tier_dados) in get(dados_servidor, "tiers", Dict())
        if dados_tier["nivel_min"] <= nivel && nivel <= dados_tier["nivel_max"]
            return nome_tier
        end
    end
    return nothing
end

"""
    aguardar_mensagem(contexto) -> Union{String, Nothing}

Aguarda a resposta do usuário no canal do contexto, com timeout de 30 segundos.

- `contexto`: Contexto da interação.

Retorna o conteúdo da mensagem respondida ou `nothing` em caso de timeout.
"""
function aguardar_mensagem(contexto)
    futuro = wait_for(contexto.cliente, :MessageCreate;
                      check=(event_contexto) -> event_contexto.author.id == contexto.interaction.membro.user.id &&
                                           event_contexto.channel_id == contexto.interaction.channel_id,
                      timeout=30)
    if futuro === nothing
        reply(contexto.cliente, contexto, content="Tempo esgotado para responder.")
        return nothing
    else
        return futuro.message.content
    end
end

"""
    handler_comando_criar(contexto)

Handler do comando /criar. Cria um novo personagem para o usuário a partir do nome fornecido.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da criação.
"""
function handler_comando_criar(contexto)
    @info "Comando /criar foi acionado"

    opcoes = contexto.interaction.data.opcoes

    if isnothing(opcoes) || isempty(opcoes)
        return reply(cliente, contexto, content="Por favor, forneça um nome para o personagem.")
    end

    nome = opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)

    resultado = criar_personagem(id_servidor, id_usuario, nome)
    
    reply(cliente, contexto, content=resultado)
    @info "Resultado da criação do personagem: $resultado"
end

"""
    handler_comando_ajuda(contexto)

Handler do comando /ajuda. Exibe a mensagem de ajuda com a lista de comandos disponíveis.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a mensagem de ajuda.
"""
function handler_comando_ajuda(contexto)
    @info "Comando /ajuda foi acionado"
    mensagem_ajuda = gerar_mensagem_ajuda()
    reply(cliente, contexto, content=mensagem_ajuda)
    @info "Resposta de ajuda enviada com sucesso"
end

function obter_descricao_item(dados_servidor::Dict, nome_item::String)
    for (_, raridade_items) in get(dados_servidor, "itens_estoque", Dict())
        if nome_item in get(raridade_items, "Name", [])
            index = findfirst(==(nome_item), raridade_items["Name"])
            return get(raridade_items, "Text", [])[index]
        end
    end
    return "Descrição não disponível."
end

function criar_personagem(server_id::String, user_id::String, nome::String)
    server_data = load_server_data(server_id)

    limite_personagens = get(get(config, "limites", Dict()), "personagens_por_usuario", 2)
    user_characters = get(server_data["characters"], user_id, Dict())

    if length(user_characters) >= limite_personagens
        return "Você já possui $limite_personagens personagens. Não é possível criar mais."
    end

    if haskey(user_characters, nome)
        return "Você já tem um personagem com o nome $nome. Por favor, escolha outro nome."
    end

    new_character = Dict(
        "marcos" => 0,
        "inventory" => [],
        "dinheiro" => 0,
        "nivel" => 1,
        "ultimo_trabalho" => nothing,
        "ultimo_crime" => nothing,
        "estrelas" => 0
    )

    personagens_usuario[nome] = novo_personagem
    dados_servidor["personagens"][id_usuario] = personagens_usuario

    salvar_dados_servidor(id_servidor, dados_servidor)

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

function handler_comando_criar(contexto)
    @info "Comando /criar foi acionado"

    opcoes = contexto.interaction.data.opcoes

    if isnothing(opcoes) || isempty(opcoes)
        return reply(cliente, contexto, content="Por favor, forneça um nome para o personagem.")
    end

    nome = opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)

    resultado = criar_personagem(id_servidor, id_usuario, nome)
    
    reply(cliente, contexto, content=resultado)
    @info "Resultado da criação do personagem: $resultado"
end

function handler_comando_ajuda(contexto)
    @info "Comando /ajuda foi acionado"
    mensagem_ajuda = gerar_mensagem_ajuda()
    reply(cliente, contexto, content=mensagem_ajuda)
    @info "Resposta de ajuda enviada com sucesso"
end

"""
    handler_comando_up(contexto)

Handler do comando /up. Adiciona Marcos ao personagem informado, atualizando o nível se necessário.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação.
"""
function handler_comando_up(contexto)
    @info "Comando /up foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "marcos", dados_servidor, false)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    personagem_encontrado = false
    for (id_usuario, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem)
            dados_personagem = personagems[personagem]
            nivel_atual = dados_personagem["nivel"]
            marcos_a_adicionar = marcos_para_ganhar(nivel_atual)

            dados_personagem["marcos"] += marcos_a_adicionar
            novos_marcos = dados_personagem["marcos"]
            novo_nivel = calcular_nivel(novos_marcos / 16)

            if novo_nivel > nivel_atual
                dados_personagem["nivel"] = novo_nivel
                reply(cliente, contexto, content="$personagem subiu para o nível $novo_nivel!")
            else
                fracao_adicionada = marcos_a_adicionar == 4 ? "1/4 de Marco" :
                                 marcos_a_adicionar == 2 ? "1/8 de Marco" :
                                 marcos_a_adicionar == 1 ? "1/16 de Marco" :
                                 "$marcos_a_adicionar Marcos"

                reply(cliente, contexto, content="Adicionado $fracao_adicionada para $personagem. Total: $(formatar_marcos(novos_marcos)) (Nível $novo_nivel)")
            end

            salvar_dados_servidor(id_servidor, dados_servidor)
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    handler_comando_marcos(contexto)

Handler do comando /marcos. Exibe a quantidade de Marcos e o nível do personagem informado.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a quantidade de Marcos e nível.
"""
function handler_comando_marcos(contexto)
    @info "Comando /marcos foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "marcos", dados_servidor, false)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    personagem_encontrado = false
    for (id_usuario, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem)
            dados_personagem = personagems[personagem]
            marcos = dados_personagem["marcos"]
            level = calcular_nivel(marcos / 16)
            reply(cliente, contexto, content="$personagem tem $(formatar_marcos(marcos)) (Nível $level)")
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    handler_comando_mochila(contexto)

Handler do comando /mochila. Exibe o inventário do personagem informado, ou a descrição de um item específico.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a lista de itens ou descrição detalhada.
"""
function handler_comando_mochila(contexto)
    @info "Comando /mochila foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    item = length(contexto.interaction.data.opcoes) > 1 ? contexto.interaction.data.opcoes[2].value : nothing

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    dados_personagem = get(get(dados_servidor["personagens"], id_usuario, Dict()), personagem, nothing)
    if isnothing(personagem_dados)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    inventory = get(dados_personagem, "inventario", [])
    if isempty(inventory)
        return reply(cliente, contexto, content="O inventário de $personagem está vazio.")
    end

    if !isnothing(item)
        if item in inventory
            contagem_item = count(==(item), inventory)
            descricao_item = obter_descricao_item(dados_servidor, item)
            reply(cliente, contexto, content="**$item** (x$contagem_item)\nDescrição: $descricao_item")
        else
            reply(cliente, contexto, content="O item '$item' não está na mochila de $personagem.")
        end
    else
        contagem_itens = Dict{String, Int}()
        for i in inventory
            contagem_items[i] = get(contagem_items, i, 0) + 1
        end
        
        items_formatted = join(["**$item** (x$count)" for (item, count) in contagem_items], ", ")
        reply(cliente, contexto, content="Inventário de $personagem: $items_formatted")
    end
end

"""
    handler_comando_comprar(contexto)

Handler do comando /comprar. Permite que um personagem compre um item da loja, descontando o valor e atualizando o estoque.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da compra.
"""
function handler_comando_comprar(contexto)
    @info "Comando /comprar foi acionado"

    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /comprar <personagem> <item>")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    item = contexto.interaction.data.opcoes[2].value

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    if isempty(get(dados_servidor, "itens_estoque", Dict()))
        return reply(cliente, contexto, content="A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
    end

    dados_personagem = personagens_usuario[personagem]
    item_found = false
    for (raridade, itens) in dados_servidor["itens_estoque"]
        if item in itens["Name"]
            indice_item = findfirst(==(item), items["Name"])
            if items["Quantity"][indice_item] > 0
                valor_item = parse(Int, items["Value"][indice_item])

                if dados_personagem["dinheiro"] < valor_item
                    return reply(cliente, contexto, content="$personagem não tem dinheiro suficiente para comprar $item. Preço: $valor_item, Dinheiro disponível: $(dados_personagem["dinheiro"])")
                end

                dados_personagem["dinheiro"] -= valor_item
                push!(dados_personagem["inventario"], item)

                items["Quantity"][indice_item] -= 1

                reply(cliente, contexto, content="$personagem comprou $item por $valor_item moedas. Dinheiro restante: $(dados_personagem["dinheiro"])")
                salvar_dados_servidor(id_servidor, dados_servidor)
                item_found = true
            else
                reply(cliente, contexto, content="Desculpe, $item está fora de estoque.")
                item_found = true
            end
            break
        end
    end

    if !item_found
        reply(cliente, contexto, content="Item '$item' não encontrado na loja.")
    end
end

"""
    handler_comando_dinheiro(contexto)

Handler do comando /dinheiro. Adiciona ou remove dinheiro do saldo de um personagem.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o novo saldo ou mensagem de erro.
"""
function handler_comando_dinheiro(contexto)
    @info "Comando /dinheiro foi acionado"

    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /dinheiro <personagem> <quantidade>")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    quantidade = parse(Int, contexto.interaction.data.opcoes[2].value)

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "saldo", dados_servidor, false)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    personagem_encontrado = false
    for (id_usuario, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem)
            dados_personagem = personagems[personagem]
            dados_personagem["dinheiro"] += amount

            if quantidade > 0
                reply(cliente, contexto, content="Adicionado $quantidade moedas ao saldo de $personagem. Novo saldo: $(dados_personagem["dinheiro"]) moedas.")
            else
                reply(cliente, contexto, content="Removido $(abs(quantidade)) moedas do saldo de $personagem. Novo saldo: $(dados_personagem["dinheiro"]) moedas.")
            end

            salvar_dados_servidor(id_servidor, dados_servidor)
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    handler_comando_saldo(contexto)

Handler do comando /saldo. Exibe o saldo de moedas do personagem informado.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o saldo do personagem.
"""
function handler_comando_saldo(contexto)
    @info "Comando /saldo foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    id_usuario = string(contexto.interaction.membro.user.id)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())

    if haskey(personagens_usuario, personagem)
        dados_personagem = personagens_usuario[personagem]
        money = get(dados_personagem, "dinheiro", 0)
        reply(cliente, contexto, content="$personagem tem $money moedas.")
    else
        reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    handler_comando_pix(contexto)

Handler do comando /pix. Transfere moedas de um personagem para outro, validando saldo e restrições.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da transferência.
"""
function handler_comando_pix(contexto)
    @info "Comando /pix foi acionado"

    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /pix <de_personagem> <para_personagem> <quantidade>")
    end

    personagem_origem = contexto.interaction.data.opcoes[1].value
    personagem_destino = contexto.interaction.data.opcoes[2].value
    quantidade = parse(Int, contexto.interaction.data.opcoes[3].value)

    if quantidade <= 0
        return reply(cliente, contexto, content="A quantidade deve ser maior que zero.")
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    id_usuario = string(contexto.interaction.membro.user.id)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())

    if !haskey(personagens_usuario, personagem_origem)
        return reply(cliente, contexto, content="Você não possui um personagem chamado $personagem_origem.")
    end

    if any(char -> char == personagem_destino, keys(personagens_usuario))
        return reply(cliente, contexto, content="Não é possível transferir moedas para um de seus próprios personagens.")
    end

    destinatario_encontrado = false
    dados_destinatario = nothing
    for (id_usuario_recipient, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem_destino) && id_usuario_recipient != id_usuario
            dados_destinatario = personagems[personagem_destino]
            destinatario_encontrado = true
            break
        end
    end

    if !destinatario_encontrado
        return reply(cliente, contexto, content="O personagem destinatário '$personagem_destino' não foi encontrado ou é de sua propriedade.")
    end

    dados_remetente = personagens_usuario[personagem_origem]

    if dados_remetente["dinheiro"] < amount
        return reply(cliente, contexto, content="$personagem_origem não tem moedas suficientes. Saldo disponível: $(dados_remetente["dinheiro"])")
    end

    dados_remetente["dinheiro"] -= amount
    dados_destinatario["dinheiro"] += amount

    salvar_dados_servidor(id_servidor, dados_servidor)

    reply(cliente, contexto, content="Transferência realizada com sucesso!\n$personagem_origem enviou $quantidade moedas para $personagem_destino.\nNovo saldo de $personagem_origem: $(dados_remetente["dinheiro"]) moedas.")
end

"""
    handler_comando_trabalhar(contexto)

Handler do comando /trabalhar. Permite que o personagem trabalhe para ganhar moedas, respeitando limites de tempo e tiers.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a recompensa do trabalho ou mensagem de erro.
"""
"""
    handler_comando_trabalhar(contexto)

Handler do comando /trabalhar. Permite que o personagem trabalhe para ganhar moedas, respeitando limites de tempo e tiers.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a recompensa do trabalho ou mensagem de erro.
"""
function handler_comando_trabalhar(contexto)
    @info "Comando /trabalhar foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    dados_personagem = personagens_usuario[personagem]

    ultimo_trabalho = get(dados_personagem, "ultimo_trabalho", nothing)
    now = Dates.now()
    intervalo_trabalhar = get(get(config, "limites", Dict()), "intervalo_trabalhar", 86400)
    if !isnothing(ultimo_trabalho)
        delta = now - DateTime(ultimo_trabalho)
        if Dates.value(delta) < intervalo_trabalhar * 1000
            return reply(cliente, contexto, content=get(config["messages"]["erros"], "acao_frequente", "Você já trabalhou recentemente. Aguarde um pouco para trabalhar novamente."))
        end
    end

    nivel = get(dados_personagem, "nivel", 0)
    nome_tier = obter_tier(nivel, dados_servidor)
    if isnothing(nome_tier)
        return reply(cliente, contexto, content="Nenhum tier definido para o seu nível. Contate um administrador.")
    end

    tier = dados_servidor["tiers"][nome_tier]
    recompensa = tier["recompensa"]
    dados_personagem["dinheiro"] += recompensa
    dados_personagem["ultimo_trabalho"] = string(now)

    mensagens = get(get(dados_servidor, "messages", Dict()), "trabalho", get(config["messages"], "trabalho", []))
    mensagem = isempty(mensagens) ? "Você trabalhou duro e ganhou sua recompensa!" : rand(mensagens)

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="$mensagem\nVocê ganhou $recompensa moedas. Saldo atual: $(dados_personagem["dinheiro"]) moedas.")
end

"""
    handler_comando_crime(contexto)

Handler do comando /crime. Permite que o personagem tente cometer um crime para ganhar ou perder moedas, respeitando limites e probabilidades.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado do crime.
"""
function handler_comando_crime(contexto)
    @info "Comando /crime foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    dados_personagem = personagens_usuario[personagem]

    ultimo_crime = get(dados_personagem, "ultimo_crime", nothing)
    now = Dates.now()
    intervalo_crime = get(get(config, "limites", Dict()), "intervalo_crime", 86400)
    if !isnothing(ultimo_crime)
        delta = now - DateTime(ultimo_crime)
        if Dates.value(delta) < intervalo_crime * 1000
            return reply(cliente, contexto, content=get(config["messages"]["erros"], "acao_frequente", "Você já cometeu um crime recentemente. Aguarde um pouco para tentar novamente."))
        end
    end

    probabilidade = get(dados_servidor, "probabilidade_crime", get(get(config, "probabilidades", Dict()), "crime", 50))
    chance = rand(1:100)

    mensagens = get(get(dados_servidor, "messages", Dict()), "crime", get(config["messages"], "crime", []))
    mensagem = isempty(mensagens) ? "Você tentou cometer um crime..." : rand(mensagens)

    if chance <= probabilidade
        recompensa = rand(100:500)
        dados_personagem["dinheiro"] += recompensa
        resultado = "Sucesso! Você ganhou $recompensa moedas."
    else
        perda = rand(50:250)
        dados_personagem["dinheiro"] = max(0, dados_personagem["dinheiro"] - perda)
        resultado = "Você foi pego! Perdeu $perda moedas."
    end

    dados_personagem["ultimo_crime"] = string(now)

    # Incrementar o atributo oculto 'estrelas'
    dados_personagem["estrelas"] = get(dados_personagem, "estrelas", 0) + 1

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="$mensagem\n$resultado\nSaldo atual: $(dados_personagem["dinheiro"]) moedas.")
end

"""
    handler_comando_cargos(contexto)

Handler do comando /cargos. Gerencia cargos especiais para permissões de saldo, marcos e loja.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de cargos.
"""
function handler_comando_cargos(contexto)
    @info "Comando /cargos foi acionado"

    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /cargos <tipo> <acao> <cargo>")
    end

    tipo = contexto.interaction.data.opcoes[1].value
    acao = contexto.interaction.data.opcoes[2].value
    nome_cargo = contexto.interaction.data.opcoes[3].value

    user = contexto.interaction.membro
    guild = contexto.interaction.id_guilda |> (t -> get_guild(cliente, t)) |> fetch |> (u -> u.val)
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val)
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal)

    if !has_permission(permissoes, PERM_ADMINISTRATOR)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !(tipo in ["saldo", "marcos", "loja"])
        return reply(cliente, contexto, content="Tipo inválido. Use 'saldo', 'marcos' ou 'loja'.")
    end

    if !(acao in ["add", "remove"])
        return reply(cliente, contexto, content="Ação inválida. Use 'add' ou 'remove'.")
    end

    cargo = findfirst(r -> lowercase(r.name) == lowercase(nome_cargo), guild.roles)
    if isnothing(cargo)
        return reply(cliente, contexto, content="Cargo não encontrado.")
    end

    if !haskey(dados_servidor["special_roles"], tipo)
        dados_servidor["special_roles"][tipo] = UInt64[]
    end

    if acao == "add"
        if !(cargo.id in dados_servidor["special_roles"][tipo])
            push!(dados_servidor["special_roles"][tipo], cargo.id)
            reply(cliente, contexto, content="Cargo $(cargo.name) adicionado às permissões de $tipo.")
        else
            reply(cliente, contexto, content="Cargo $(cargo.name) já está nas permissões de $tipo.")
        end
    elseif acao == "remove"
        if cargo.id in dados_servidor["special_roles"][tipo]
            filter!(id -> id != cargo.id, dados_servidor["special_roles"][tipo])
            reply(cliente, contexto, content="Cargo $(cargo.name) removido das permissões de $tipo.")
        else
            reply(cliente, contexto, content="Cargo $(cargo.name) não estava nas permissões de $tipo.")
        end
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
    @info "Comando cargos concluído. Dados atualizados: $(dados_servidor["special_roles"])"
end

"""
    handler_comando_estoque(contexto)

Handler do comando /estoque. Gerencia o estoque da loja, permitindo abastecimento e definição de preços.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de estoque.
"""
function handler_comando_estoque(contexto)
    @info "Comando /estoque foi acionado"

    if length(contexto.interaction.data.opcoes) < 4
        return reply(cliente, contexto, content="Uso incorreto. Use: /estoque <comum> <incomum> <raro> <muito_raro>")
    end

    comum = contexto.interaction.data.opcoes[1].value
    uncomum = contexto.interaction.data.opcoes[2].value
    raro = contexto.interaction.data.opcoes[3].value
    very_raro = contexto.interaction.data.opcoes[4].value

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)
    
    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    dados_servidor["itens_estoque"] = Dict()

    raridades = Dict(
        "common" => common,
        "uncommon" => uncommon,
        "rare" => rare,
        "very rare" => very_rare
    )

    csv_file = isfile("items_$(id_servidor).csv") ? "items_$(id_servidor).csv" : "items.csv"

    try
        todos_itens = CSV.read(csv_file, DataFrame)
    catch
        return reply(cliente, contexto, content="Erro: O arquivo de itens '$csv_file' não foi encontrado.")
    end

    reply(cliente, contexto, content="Criando novo estoque. Por favor, defina os preços para cada item.")

    for (raridade, count) in raridades
        itens_disponiveis = filter(row -> row.Rarity == raridade, todos_itens)
        contagem_disponivel = nrow(itens_disponiveis)

        if contagem_disponivel < count
            count = contagem_disponivel
        end

        if count > 0
            itens = itens_disponiveis[rand(1:nrow(itens_disponiveis), count), :]
            dados_servidor["itens_estoque"][raridade] = Dict(
                "Name" => items.Name,
                "Value" => String[],
                "Quantity" => fill(1, count),
                "Text" => items.Text
            )

            for name in dados_servidor["itens_estoque"][raridade]["Name"]
                preco_definido = false
                attempts = 0
                while !preco_definido && attempts < 3
                    reply(cliente, contexto, content="Digite o preço para $name (em moedas):")
                    resposta = aguardar_mensagem(contexto)
                    if resposta === nothing
                        break
                    end
                    try
                        preco = parse(Int, resposta)
                        push!(dados_servidor["itens_estoque"][raridade]["Value"], string(price))
                        atualizar_preco_item(id_servidor, name, string(price))
                        reply(cliente, contexto, content="Preço de $name definido como $price moedas e salvo.")
                        preco_definido = true
                    catch
                        reply(cliente, contexto, content="Por favor, digite um número inteiro válido.")
                        attempts += 1
                    end
                end

                if !preco_definido
                    preco_padrao = get(get(config, "precos_padroes", Dict()), "item_padrao", 100)
                    reply(cliente, contexto, content="Falha ao definir preço para $name. Definindo preço padrão de $preco_padrao moedas.")
                    push!(dados_servidor["itens_estoque"][raridade]["Value"], string(preco_padrao))
                    atualizar_preco_item(id_servidor, name, string(preco_padrao))
                end
            end
        end
    end

    salvar_dados_servidor(id_servidor, dados_servidor)

    summary = "Novo estoque criado com:\n"
    for (raridade, itens) in dados_servidor["itens_estoque"]
        summary *= "- $(length(items["Name"])) itens $raridade\n"
    end

    reply(cliente, contexto, content=summary)
    reply(cliente, contexto, content="Estoque atualizado com sucesso e valores salvos!")
end

"""
    handler_comando_loja(contexto)

Handler do comando /loja. Exibe os itens disponíveis na loja para o personagem selecionado.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a lista de itens da loja e saldo do personagem.
"""
function handler_comando_loja(contexto)
    @info "Comando /loja foi acionado"

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if isempty(get(dados_servidor, "itens_estoque", Dict()))
        return reply(cliente, contexto, content="A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if isempty(personagens_usuario)
        return reply(cliente, contexto, content="Você não tem nenhum personagem. Crie um personagem primeiro antes de acessar a loja.")
    end

    reply(cliente, contexto, content="Escolha o personagem para ver a loja:")
    for personagem in keys(personagens_usuario)
        reply(cliente, contexto, content=personagem)
    end

    resposta = aguardar_mensagem(contexto)
    if resposta === nothing
        return
    end
    personagem_selecionado = strip(resposta)

    if !haskey(personagens_usuario, personagem_selecionado)
        return reply(cliente, contexto, content="Personagem inválido selecionado.")
    end

    todos_itens = []
    for (raridade, itens) in dados_servidor["itens_estoque"]
        for (name, valor, quantity, text) in zip(items["Name"], items["Value"], items["Quantity"], items["Text"])
            if quantity > 0
                push!(todos_itens, Dict(
                    "Name" => name,
                    "Value" => value,
                    "Quantity" => quantity,
                    "Text" => text
                ))
            end
        end
    end

    if isempty(todos_itens)
        return reply(cliente, contexto, content="Não há itens disponíveis na loja no momento.")
    end

    for item in todos_itens
        reply(cliente, contexto, content="""
        **$(item["Name"])**
        Preço: $(item["Value"]) moedas
        Quantidade: $(item["Quantity"])
        Descrição: $(item["Text"])
        """)
    end

    reply(cliente, contexto, content="Seu dinheiro: $(personagens_usuario[personagem_selecionado]["dinheiro"]) moedas")
end

"""
    handler_comando_inserir(contexto)

Handler do comando /inserir. Permite inserir um novo item no estoque da loja, definindo raridade, quantidade e valor.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de inserção.
"""
"""
    handler_comando_inserir(contexto)

Handler do comando /inserir. Permite inserir um novo item no estoque da loja, definindo raridade, quantidade e valor.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de inserção.
"""
function handler_comando_inserir(contexto)
    @info "Comando /inserir foi acionado"

    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /inserir <raridade> <item> <quantidade> [valor]")
    end

    raridade = contexto.interaction.data.opcoes[1].value
    item = contexto.interaction.data.opcoes[2].value
    quantidade = parse(Int, contexto.interaction.data.opcoes[3].value)
    valor = length(contexto.interaction.data.opcoes) >= 4 ? contexto.interaction.data.opcoes[4].value : nothing

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)
    
    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    if !haskey(dados_servidor, "itens_estoque") || isempty(dados_servidor["itens_estoque"])
        dados_servidor["itens_estoque"] = Dict()
    end
    
    if !haskey(dados_servidor["itens_estoque"], raridade)
        dados_servidor["itens_estoque"][raridade] = Dict(
            "Name" => String[],
            "Value" => String[],
            "Quantity" => Int[],
            "Text" => String[]
        )
    end

    estoque = dados_servidor["itens_estoque"][raridade]

    if item in estoque["Name"]
        index = findfirst(==(item), stock["Name"])
        stock["Quantity"][index] += quantidade
        if !isnothing(valor)
            stock["Value"][index] = string(valor)
            atualizar_preco_item(id_servidor, item, string(valor))
        end
    else
        push!(stock["Name"], item)
        push!(stock["Quantity"], quantidade)
        if !isnothing(valor)
            push!(stock["Value"], string(valor))
            atualizar_preco_item(id_servidor, item, string(valor))
        else
            preco = get(get(dados_servidor, "precos", Dict()), item, string(get(get(config, "precos_padroes", Dict()), "item_padrao", 100)))
            push!(stock["Value"], price)
        end
        push!(stock["Text"], "Descrição não disponível")
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Item '$item' inserido no estoque com sucesso.")
end

"""
    handler_comando_remover(contexto)

Handler do comando /remover. Permite remover um item do estoque da loja, parcial ou totalmente.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de remoção.
"""
"""
    handler_comando_remover(contexto)

Handler do comando /remover. Permite remover um item do estoque da loja, parcial ou totalmente.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de remoção.
"""
function handler_comando_remover(contexto)
    @info "Comando /remover foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do item a ser removido.")
    end

    item = contexto.interaction.data.opcoes[1].value
    quantidade = length(contexto.interaction.data.opcoes) >= 2 ? parse(Int, contexto.interaction.data.opcoes[2].value) : nothing

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)
    
    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end
    
    item_found = false
    for (raridade, stock) in get(dados_servidor, "itens_estoque", Dict())
        if item in estoque["Name"]
            index = findfirst(==(item), stock["Name"])
            if isnothing(quantidade) || quantidade >= stock["Quantity"][index]
                deleteat!(stock["Name"], index)
                deleteat!(stock["Value"], index)
                deleteat!(stock["Quantity"], index)
                deleteat!(stock["Text"], index)
                reply(cliente, contexto, content="Item '$item' removido completamente do estoque.")
            else
                stock["Quantity"][index] -= quantidade
                reply(cliente, contexto, content="Removido $quantidade de '$item'. Quantidade restante: $(stock["Quantity"][index])")
            end
            item_found = true
            break
        end
    end

    if !item_found
        reply(cliente, contexto, content="Item '$item' não encontrado no estoque.")
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
end

"""
    limpar_handler_comando_estoque(contexto)

Handler do comando /limpar_estoque. Limpa completamente o estoque da loja do servidor.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a limpeza do estoque.
"""
"""
    limpar_handler_comando_estoque(contexto)

Handler do comando /limpar_estoque. Limpa completamente o estoque da loja do servidor.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a limpeza do estoque.
"""
function limpar_handler_comando_estoque(contexto)
    @info "Comando /limpar_estoque foi acionado"

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)
    
    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    dados_servidor["itens_estoque"] = Dict()
    salvar_dados_servidor(id_servidor, dados_servidor)

    reply(cliente, contexto, content="O estoque foi limpo com sucesso.")
end

function backhandler_comando_up(contexto)
    @info "Comando /backup foi acionado"
    usuario    = contexto.interaction.membro
    servidor   = contexto.interaction.id_guilda   |> (t -> get_guild(cliente, t))   |> fetch |> (u -> u.val)
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val)
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal)
    if !has_permission(permissoes, PERM_ADMINISTRATOR)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    dados_backup = contexto.interaction.id_guilda |> string |> carregar_dados_servidor |> JSON3.write
    
    if length(backup_dados) <= 2000
        reply(cliente, contexto, content="```json\n$dados_backup\n```")
    else
        open("backup_$(contexto.interaction.id_guilda).json", "w") do f
            JSON3.write(f, backup_dados)
        end
        reply(cliente, contexto, content="O backup é muito grande para ser enviado como mensagem. Um arquivo foi criado no servidor.")
    end
end

"""
    handler_comando_mensagens(contexto)

Handler do comando /mensagens. Permite adicionar mensagens personalizadas para eventos como trabalho e crime.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a adição da mensagem.
"""
function handler_comando_mensagens(contexto)
    @info "Comando /mensagens foi acionado"

    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /mensagens <tipo> <mensagem>")
    end

    tipo = contexto.interaction.data.opcoes[1].value
    mensagem = contexto.interaction.data.opcoes[2].value

    usuario    = contexto.interaction.membro
    servidor   = contexto.interaction.id_guilda   |> (t -> get_guild(cliente, t))   |> fetch |> (u -> u.val)
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val)
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal)
    if !has_permission(permissoes, PERM_ADMINISTRATOR)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !haskey(dados_servidor, "messages")
        dados_servidor["messages"] = Dict("trabalho" => String[], "crime" => String[])
    end

    push!(get!(dados_servidor["messages"], tipo, String[]), mensagem)
    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Mensagem adicionada ao tipo $tipo com sucesso.")
end

"""
    handler_comando_tiers(contexto)

Handler do comando /tiers. Permite configurar os tiers de níveis, definindo nível mínimo, máximo e recompensa.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a configuração do tier.
"""
function handler_comando_tiers(contexto)
    @info "Comando /tiers foi acionado"

    if length(contexto.interaction.data.opcoes) < 4
        return reply(cliente, contexto, content="Uso incorreto. Use: /tiers <tier> <nivel_min> <nivel_max> <recompensa>")
    end

    tier = contexto.interaction.data.opcoes[1].value
    nivel_min = parse(Int, contexto.interaction.data.opcoes[2].value)
    nivel_max = parse(Int, contexto.interaction.data.opcoes[3].value)
    recompensa = parse(Int, contexto.interaction.data.opcoes[4].value)

    usuario    = contexto.interaction.membro
    servidor   = contexto.interaction.id_guilda   |> (t -> get_guild(cliente, t))   |> fetch |> (u -> u.val)
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val)
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal)
    if !has_permission(permissoes, PERM_ADMINISTRATOR)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !haskey(dados_servidor, "tiers")
        dados_servidor["tiers"] = Dict()
    end

    dados_servidor["tiers"][tier] = Dict(
        "nivel_min" => nivel_min,
        "nivel_max" => nivel_max,
        "recompensa" => recompensa
    )

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Tier '$tier' definido para níveis $nivel_min-$nivel_max com recompensa de $recompensa moedas.")
end

"""
    prob_handler_comando_crime(contexto)

Handler do comando /probabilidade_crime. Define a probabilidade de sucesso ao cometer um crime.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a nova probabilidade.
"""
function prob_handler_comando_crime(contexto)
    @info "Comando /probabilidade_crime foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça a probabilidade de sucesso do crime.")
    end

    probabilidade = parse(Int, contexto.interaction.data.opcoes[1].value)

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)
    
    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
    end
    
    if !(0 <= probabilidade <= 100)
        return reply(cliente, contexto, content="Por favor, insira um valor entre 0 e 100.")
    end

    dados_servidor["probabilidade_crime"] = probabilidade
    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Probabilidade de sucesso no crime definida para $probabilidade%.")
end

"""
    handler_comando_rip(contexto)

Handler do comando /rip. Remove permanentemente um personagem, após confirmação.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a eliminação ou cancelamento.
"""
function handler_comando_rip(contexto)
    @info "Comando /rip foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    usuario    = contexto.interaction.membro
    servidor   = contexto.interaction.id_guilda   |> (t -> get_guild(cliente, t))   |> fetch |> (u -> u.val)
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val)
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal)

    if !has_permission(permissoes, PERM_ADMINISTRATOR) && !verificar_permissoes(contexto.interaction.membro, personagem, "marcos", dados_servidor, false)
        if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true)
            return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando."))
        end
    end

    personagem_encontrado = false
    id_proprietario = ""
    for (id_usuario, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem)
            id_proprietario = id_usuario
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        return reply(cliente, contexto, content="Personagem $personagem não encontrado.")
    end

    reply(cliente, contexto, content="Tem certeza que deseja eliminar o personagem $personagem? Responda 'sim' para confirmar.")

    resposta = aguardar_mensagem(contexto)
    if resposta === nothing || lowercase(strip(resposta)) != "sim"
        return reply(cliente, contexto, content="Eliminação cancelada.")
    end

    delete!(dados_servidor["personagens"][id_proprietario], personagem)
    if isempty(dados_servidor["personagens"][id_proprietario])
        delete!(dados_servidor["personagens"], id_proprietario)
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Personagem $personagem foi eliminado com sucesso.")
end

"""
    handler_comando_inss(contexto)

Handler do comando /inss. Aposenta um personagem, movendo seus dados para a seção 'aposentados'.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a aposentadoria do personagem.
"""
function handler_comando_inss(contexto)
    @info "Comando /inss foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    if !haskey(dados_servidor, "aposentados")
        dados_servidor["aposentados"] = Dict()
    end

    dados_servidor["aposentados"][personagem] = personagens_usuario[personagem]
    delete!(personagens_usuario, personagem)

    if isempty(personagens_usuario)
        delete!(dados_servidor["personagens"], id_usuario)
    else
        dados_servidor["personagens"][id_usuario] = personagens_usuario
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Personagem $personagem foi aposentado com sucesso e seus dados foram preservados.")
end

"""
    registrar_comandos_guild(cliente::Client, id_guilda::UInt64)

Registra todos os comandos de aplicação (slash commands) para uma guild específica.

- `cliente`: Instância do clientee Discord.
- `id_guilda`: ID da guild onde os comandos serão registrados.
"""
function registrar_comandos_guild(cliente::Client, id_guilda::UInt64)
    commands = [
        ApplicationCommand(
            name = "criar",
            description = "Cria um novo personagem",
            application_id = APPLICATION_ID,
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
        Ekztazy.bulk_overwrite_application_commands(cliente, id_guilda, commands)
    catch e
        @error "Erro ao registrar comandos para a guild $id_guilda" exception=(erro, catch_backtrace())
    end
end

"""
    registrar_comandos_globais(cliente::Client)

Registra os comandos de aplicação globais (disponíveis em todas as guilds).

- `cliente`: Instância do clientee Discord.
"""
"""
    registrar_comandos_globais(cliente::Client)

Registra os comandos de aplicação globais (disponíveis em todas as guilds).

- `cliente`: Instância do clientee Discord.
"""
"""
    registrar_comandos_globais(cliente::Client)

Registra os comandos de aplicação globais (disponíveis em todas as guilds).

- `cliente`: Instância do clientee Discord.
"""
"""
    registrar_comandos_globais(cliente::Client)

Registra os comandos de aplicação globais (disponíveis em todas as guilds).

- `cliente`: Instância do clientee Discord.
"""
"""
    registrar_comandos_globais(cliente::Client)

Registra os comandos de aplicação globais (disponíveis em todas as guilds).

- `cliente`: Instância do clientee Discord.
"""
function registrar_comandos_globais(cliente::Client)
    @info "Registrando comandos globalmente"
    commands = [
        ApplicationCommand(
            name = "criar",
            description = "Cria um novo personagem",
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
            opcoes = [
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
        Ekztazy.bulk_overwrite_application_commands(cliente, commands)
        @info "Comandos registrados globalmente com sucesso"
    catch e
        @error "Erro ao registrar comandos globalmente" exception=(erro, catch_backtrace())
    end
end

# Configuração do clientee
cliente = Client(TOKEN, UInt64(APPLICATION_ID), intents(GUILDS, GUILD_MESSAGES), version=9)

# Adicionar handlers para cada comando
"""
    registrar_handlers_comandos()

Registra os handlers para cada comando de aplicação no clientee Discord.
"""
function registrar_handlers_comandos()
    @info "Registrando comandos"
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
    @info "Comandos registrados com sucesso"
end

# Handler para quando o bot entrar em uma nova guild
"""
Handler para o evento `GUILD_CREATE`. Registra os comandos específicos da guild quando o bot entra em um novo servidor.
"""
ao_entrar_guild!(cliente) do contexto
    id_guilda = UInt64(contexto.guild.id)
    @info "Bot entrou na guild: $id_guilda. Registrando comandos..."
    try
        registrar_comandos_guild(cliente, id_guilda)
    catch e
        @error "Erro ao registrar comandos para a nova guild" exception=(erro, catch_backtrace())
    end
end

# Tratamento de erros global
"""
    handler_erro_personalizado(c::Client, erro::Exception, args...)

Handler global de erros. Loga o erro e tenta reconectar em caso de erro de WebSocket.

- `c`: Instância do clientee Discord.
- `e`: Exceção capturada.
- `args...`: Argumentos adicionais do erro.
"""
function handler_erro_personalizado(c::Client, erro::Exception, args...)
    @error "Ocorreu um erro" exception=(erro, catch_backtrace())
    if isa(e, HTTP.WebSockets.WebSocketError)
        @warn "Erro de WebSocket detectado. Tentando reconectar..."
        sleep(5)  # Espera 5 segundos antes de tentar reconectar
        try
            start(c)
        catch erro_reconexao
            @error "Falha ao reconectar" exception=(erro_reconexao, catch_backtrace())
        end
    end
end

# Inicialização do bot
try
    @info "Gerando gestor de erros..."
    add_handler!(cliente, Handler(handler_erro_personalizado, type=:OnError))
    @info "Gestor de erros gerado com sucesso. Inicializando comandos..."
    registrar_handlers_comandos()
    @info "Comandos inicializados com sucesso. Iniciando o bot..."

    start(cliente)
catch e
    @error "Falha ao iniciar o bot" exception=(erro, catch_backtrace())
end