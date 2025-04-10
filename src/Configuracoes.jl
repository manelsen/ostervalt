module Configuracoes
export definir_probabilidade_crime, configurar_tier

using ..PersistenciaDados

# Função para definir a probabilidade de sucesso no crime
function definir_probabilidade_crime(id_servidor::String, probabilidade::Int)
    if !(0 <= probabilidade <= 100)
        return "Por favor, insira um valor entre 0 e 100."
    end
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    dados_servidor["probabilidade_crime"] = probabilidade
    PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
    return "Probabilidade de sucesso no crime definida para $probabilidade%."
end

# Função para configurar tiers de níveis
function configurar_tier(id_servidor::String, nome_tier::String, nivel_min::Int, nivel_max::Int, recompensa::Int)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    if !haskey(dados_servidor, "tiers")
        dados_servidor["tiers"] = Dict()
    end
    dados_servidor["tiers"][nome_tier] = Dict(
        "nivel_min" => nivel_min,
        "nivel_max" => nivel_max,
        "recompensa" => recompensa
    )
    PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
    return "Tier '$nome_tier' definido para níveis $nivel_min-$nivel_max com recompensa de $recompensa moedas."
end

end # do módulo