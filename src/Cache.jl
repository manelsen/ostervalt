module Cache
export obter_cache, definir_cache, cache_dados_servidor

using Dates

# Estrutura para armazenamento em cache de dados temporários
mutable struct CacheContainer
    dados::Dict{String, Any}
    tempo_vida::Int
    ultima_atualizacao::DateTime
end

# Função para obter um valor do cache
function obter_cache(chave::String, cache::CacheContainer)
    if haskey(cache.dados, chave) && (now() - cache.ultima_atualizacao).value < cache.tempo_vida
        return cache.dados[chave]
    end
    return nothing
end

# Função para armazenar um valor no cache
function definir_cache(chave::String, valor::Any, cache::CacheContainer)
    cache.dados[chave] = valor
    cache.ultima_atualizacao = now()
end

# Instância global de cache para dados de servidor
cache_dados_servidor = CacheContainer(Dict(), 300, now())

end # do módulo