module ServicoCache
export cache_dados_servidor

using Dates
mutable struct CacheContainer
    dados::Dict{String, Any}
    tempo_vida::Int
    ultima_atualizacao::DateTime
end

# Instância global de cache para dados de servidor
cache_dados_servidor = CacheContainer(Dict(), 300, now())

end # do módulo