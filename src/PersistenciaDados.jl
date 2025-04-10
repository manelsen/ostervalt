module PersistenciaDados
export carregar_dados_servidor, salvar_dados_servidor, atualizar_preco_item

using JSON3, Dates
using ..ServicoCache

# Função para carregar dados do servidor
function carregar_dados_servidor(id_servidor::String)
    dados_em_cache = ServicoCache.obter_cache(id_servidor, ServicoCache.cache_dados_servidor)
    if !isnothing(dados_em_cache)
        return dados_em_cache
    end

    dados = Dict()
    arquivo = "dados_servidor_$id_servidor.json"
    if isfile(arquivo)
        open(arquivo, "r") do f
            dados = JSON3.read(f, Dict)
        end
    end

    # Inicialização dos campos padrão
    dados["personagens"]    = get(dados, "personagens",    Dict())
    dados["itens_estoque"]  = get(dados, "itens_estoque",  Dict())
    dados["special_roles"]  = get(dados, "special_roles",  Dict())
    for chave in ["saldo", "marcos", "loja"]
        dados["special_roles"][chave] = get(dados["special_roles"], chave, UInt64[])
    end
    dados["itens_loja"]          = get(dados, "itens_loja", nothing)
    dados["messages"]            = get(dados, "messages", get(Configuracoes.config, "messages", Dict()))
    dados["tiers"]               = get(dados, "tiers", get(Configuracoes.config, "tiers", Dict()))
    dados["aposentados"]         = get(dados, "aposentados", Dict())
    dados["precos"]              = get(dados, "precos", Dict())
    dados["probabilidade_crime"] = get(dados, "probabilidade_crime", get(get(Configuracoes.config, "probabilidades", Dict()), "crime", 50))

    ServicoCache.definir_cache(id_servidor, dados, ServicoCache.cache_dados_servidor)
    return dados
end

# Função para salvar dados do servidor
function salvar_dados_servidor(id_servidor::String, dados::Dict)
    arquivo = "dados_servidor_$id_servidor.json"
    open(arquivo, "w") do f
        JSON3.write(f, dados)
    end
    ServicoCache.definir_cache(id_servidor, dados, ServicoCache.cache_dados_servidor)
    @info "Dados do servidor $id_servidor salvos e cache atualizado."
end

# Função para atualizar preço de item
function atualizar_preco_item(id_servidor::String, nome_item::String, valor::String)
    dados = carregar_dados_servidor(id_servidor)
    dados["precos"] = get(dados, "precos", Dict())
    dados["precos"][nome_item] = valor
    salvar_dados_servidor(id_servidor, dados)
    @info "Preço atualizado para $nome_item: $valor moedas"
end

end # do módulo