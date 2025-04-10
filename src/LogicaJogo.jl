# LogicaJogo.jl
# Funções centrais da lógica de jogo do Ostervalt

# Calcula o nível de um personagem a partir da quantidade de Marcos
function calcular_nivel(marcos::Float64)
    min(20, floor(Int, marcos) + 1)
end

# Retorna a quantidade de Marcos a ser ganha para o próximo nível, de acordo com a configuração
function marcos_para_ganhar(nivel::Int)
    marcos_por_nivel = get(get(config, "progressao", Dict()), "marcos_por_nivel", Dict())
    if nivel <= 4
        return get(marcos_por_nivel, "1-4", 16)
    elseif nivel <= 12
        return get(marcos_por_nivel, "5-12", 4)
    elseif nivel <= 16
        return get(marcos_por_nivel, "13-16", 2)
    else
        return get(marcos_por_nivel, "17-20", 1)
    end
end

# Formata a quantidade de partes de Marcos em uma string legível
function formatar_marcos(partes_marcos::Int)
    marcos_completos = div(partes_marcos, 16)
    partes_restantes = mod(partes_marcos, 16)

    if partes_restantes == 0
        return "\$marcos_completos Marcos"
    end

    nivel = calcular_nivel(partes_marcos / 16)

    if nivel <= 4
        return "\$marcos_completos Marcos"
    elseif nivel <= 12
        return "\$marcos_completos e \$(div(partes_restantes, 4))/4 Marcos"
    elseif nivel <= 16
        return "\$marcos_completos e \$(div(partes_restantes, 2))/8 Marcos"
    else
        return "\$marcos_completos e \$partes_restantes/16 Marcos"
    end
end

# Obtém o nome do tier correspondente ao nível informado, de acordo com a configuração do servidor
function obter_tier(nivel::Int, dados_servidor::Dict)
    for (nome_tier, dados_tier) in get(dados_servidor, "tiers", Dict())
        if dados_tier["nivel_min"] <= nivel && nivel <= dados_tier["nivel_max"]
            return nome_tier
        end
    end
    return nothing
end