using JSON3, Dates

# Estrutura para armazenamento em cache de dados temporários
mutable struct Cache
    dados::Dict{String, Any}
    tempo_vida::Int
    ultima_atualizacao::DateTime
end

# Obtém um valor do cache se ainda estiver válido
function obter_cache(chave::String, cache::Cache)
    if haskey(cache.dados, chave) && (now() - cache.ultima_atualizacao).value < cache.tempo_vida
        return cache.dados[chave]
    end
    return nothing
end

# Armazena um valor no cache e atualiza o timestamp
function definir_cache(chave::String, valor::Any, cache::Cache)
    cache.dados[chave] = valor
    cache.ultima_atualizacao = now()
end

const cache_dados_servidor = Cache(Dict(), 300, now())

# Carrega os dados persistentes de um servidor Discord a partir de arquivo JSON
function carregar_dados_servidor(id_servidor::String)
    dados_em_cache = obter_cache(id_servidor, cache_dados_servidor)
    if !isnothing(dados_em_cache)
        return dados_em_cache
    end

    data = Dict()
    if isfile("dados_servidor_$id_servidor.json")
        open("dados_servidor_$id_servidor.json", "r") do f
            data = JSON3.read(f, Dict)
        end
    end

    # Inicialização de campos padrão
    data["personagens"]    = get(data, "personagens",    Dict())
    data["itens_estoque"]   = get(data, "itens_estoque",   Dict())
    data["special_roles"] = get(data, "special_roles", Dict())
    
    for key in ["saldo", "marcos", "loja"]
        data["special_roles"][key] = get(data["special_roles"], key, UInt64[])
    end
    
    data["itens_loja"]          = get(data, "itens_loja", nothing)
    data["messages"]            = get(data, "messages", get(config, "messages", Dict()))
    data["tiers"]               = get(data, "tiers", get(config, "tiers", Dict()))
    data["aposentados"]         = get(data, "aposentados", Dict())
    data["precos"]              = get(data, "precos", Dict())
    data["probabilidade_crime"] = get(data, "probabilidade_crime", get(get(config, "probabilidades", Dict()), "crime", 50))

    definir_cache(id_servidor, data, cache_dados_servidor)
    return data
end

# Salva os dados do servidor Discord em arquivo JSON e atualiza o cache
function salvar_dados_servidor(id_servidor::String, dados::Dict)
    open("dados_servidor_$id_servidor.json", "w") do f
        JSON3.write(f, dados)
    end
    definir_cache(id_servidor, dados, cache_dados_servidor)
    @info "Dados do servidor $id_servidor salvos e cache atualizado."
end