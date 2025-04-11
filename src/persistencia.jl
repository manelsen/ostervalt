# Persistência de dados (cache, JSON)
# Este arquivo é incluído diretamente no módulo OstervaltBot.

using JSON3, Dates, Logging
# using .Config: config # Removido, 'config' está no mesmo escopo (OstervaltBot)

# Não precisa de export aqui

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

- `chave`: Chave de busca.
- `cache`: Instância de Cache.

Retorna o valor armazenado ou `nothing` se expirado ou não encontrado.
"""
function obter_cache(chave::String, cache::Cache)
    if haskey(cache.dados, chave) && (now() - cache.ultima_atualizacao).value < cache.tempo_vida * 1000 # Tempo de vida em milissegundos
        return cache.dados[chave]
    end
    return nothing
end

"""
    definir_cache(chave::String, valor::Any, cache::Cache)

Armazena um valor no cache e atualiza o timestamp.

- `chave`: Chave de armazenamento.
- `valor`: Valor a ser armazenado.
- `cache`: Instância de Cache.
"""
function definir_cache(chave::String, valor::Any, cache::Cache)
    cache.dados[chave] = valor
    cache.ultima_atualizacao = now()
end

# Instância global do cache para dados do servidor
const cache_dados_servidor = Cache(Dict(), 300, now()) # Cache de 5 minutos

"""
    carregar_dados_servidor(id_servidor::String) -> Dict

Carrega os dados persistentes de um servidor Discord a partir de arquivo JSON.
Utiliza cache para otimizar leituras frequentes.

- `id_servidor`: ID do servidor Discord.

Retorna um dicionário com todos os dados do servidor, inicializando campos padrão se necessário.
"""
function carregar_dados_servidor(id_servidor::String)
    dados_em_cache = obter_cache(id_servidor, cache_dados_servidor)
    if !isnothing(dados_em_cache)
        @debug "Dados do servidor $id_servidor carregados do cache."
        return dados_em_cache
    end

    @debug "Cache miss para servidor $id_servidor. Lendo do arquivo..."
    data = Dict{String, Any}() # Especificar tipo para clareza
    filepath = "dados_servidor_$(id_servidor).json"
    if isfile(filepath)
        try
            open(filepath, "r") do f
                data = JSON3.read(f, Dict{String, Any}) # Especificar tipo
            end
            @info "Dados carregados de $filepath"
        catch e
            @error "Erro ao ler arquivo de dados $filepath" exception=(e, catch_backtrace())
            # Retorna um dicionário vazio ou com padrões em caso de erro de leitura
            data = Dict{String, Any}()
        end
    else
        @warn "Arquivo de dados $filepath não encontrado. Usando dados padrão."
    end

    # Inicialização de campos padrão para garantir a existência das chaves
    data["personagens"]    = get(data, "personagens",    Dict{String, Any}())
    data["itens_estoque"]   = get(data, "itens_estoque",   Dict{String, Any}())
    data["special_roles"] = get(data, "special_roles", Dict{String, Any}())

    # Garante que as listas de roles existam dentro de special_roles
    for key in ["saldo", "marcos", "loja", "view"] # Adicionado "view"
        data["special_roles"][key] = get(data["special_roles"], key, UInt64[])
    end

    # Outros campos com valores padrão do config ou hardcoded
    # 'config' agora está acessível diretamente no escopo OstervaltBot
    default_messages = get(config, "messages", Dict())
    default_tiers = get(config, "tiers", Dict())
    default_crime_prob = get(get(config, "probabilidades", Dict()), "crime", 50)

    data["itens_loja"]          = get(data, "itens_loja", nothing) # 'nothing' pode não ser ideal, talvez []?
    data["messages"]            = get(data, "messages", default_messages)
    data["tiers"]               = get(data, "tiers", default_tiers)
    data["aposentados"]         = get(data, "aposentados", Dict{String, Any}())
    data["precos"]              = get(data, "precos", Dict{String, Any}())
    data["probabilidade_crime"] = get(data, "probabilidade_crime", default_crime_prob)

    definir_cache(id_servidor, data, cache_dados_servidor)
    return data
end

"""
    salvar_dados_servidor(id_servidor::String, dados::Dict)

Salva os dados do servidor Discord em arquivo JSON e atualiza o cache.

- `id_servidor`: ID do servidor Discord.
- `dados`: Dicionário de dados a serem salvos.
"""
function salvar_dados_servidor(id_servidor::String, dados::Dict)
    filepath = "dados_servidor_$(id_servidor).json"
    try
        open(filepath, "w") do f
            JSON3.write(f, dados)
        end
        definir_cache(id_servidor, deepcopy(dados), cache_dados_servidor) # Salva uma cópia no cache
        @info "Dados do servidor $id_servidor salvos em $filepath e cache atualizado."
    catch e
        @error "Erro ao salvar dados para o servidor $id_servidor em $filepath" exception=(e, catch_backtrace())
    end
end

"""
    atualizar_preco_item(id_servidor::String, nome_item::String, valor::String)

Atualiza o preço de um item na base de dados do servidor.

- `id_servidor`: ID do servidor Discord.
- `nome_item`: Nome do item.
- `valor`: Novo valor do item (string).
"""
function atualizar_preco_item(id_servidor::String, nome_item::String, valor::String)
    dados = carregar_dados_servidor(id_servidor)
    precos = get!(dados, "precos", Dict{String, Any}()) # Garante que a chave "precos" exista
    precos[nome_item] = valor
    salvar_dados_servidor(id_servidor, dados)
    @info "Preço atualizado para '$nome_item': $valor moedas no servidor $id_servidor"
end

"""
    exportar_dados_json(id_servidor::String) -> String

Carrega os dados do servidor e os formata como uma string JSON.

- `id_servidor`: ID do servidor Discord.

Retorna uma string contendo os dados formatados em JSON.
"""
function exportar_dados_json(id_servidor::String)
    @info "Exportando dados para JSON para o servidor $id_servidor"
    dados = carregar_dados_servidor(id_servidor)
    try
        return JSON3.write(dados)
    catch e
        @error "Erro ao converter dados para JSON para o servidor $id_servidor" exception=(e, catch_backtrace())
        return "{ \"erro\": \"Falha ao exportar dados\" }" # Retorna um JSON de erro
    end
end

# Fim do código de persistencia.jl (sem 'end' de módulo)