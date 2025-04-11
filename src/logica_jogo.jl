# Lógica de jogo

# Atualiza o preço de um item na base de dados do servidor
function atualizar_preco_item(id_servidor::String, nome_item::String, valor::String)
    data = carregar_dados_servidor(id_servidor)
    data["precos"] = get(data, "precos", Dict())
    data["precos"][nome_item] = valor
    salvar_dados_servidor(id_servidor, data)
    @info "Preço atualizado para $nome_item: $valor moedas"
end

# Calcula o nível de um personagem a partir da quantidade de Marcos
function calcular_nivel(marcos::Float64)
    min(20, floor(Int, marcos) + 1)
end

# Retorna a quantidade de Marcos a ser ganha para o próximo nível
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
        return "$marcos_completos Marcos"
    end

    nivel = calcular_nivel(partes_marcos / 16)

    if nivel <= 4
        return "$marcos_completos Marcos"
    elseif nivel <= 12
        return "$marcos_completos e $(div(partes_restantes, 4))/4 Marcos"
    elseif nivel <= 16
        return "$marcos_completos e $(div(partes_restantes, 2))/8 Marcos"
    else
        return "$marcos_completos e $partes_restantes/16 Marcos"
    end
end

# Verifica se o membro possui permissão para executar determinada ação
function verificar_permissoes(membro::Ekztazy.Member, personagem::Union{String, Nothing}, tipo_permissao::String, dados_servidor::Dict, permitir_proprietario::Bool=true)
    id_usuario = string(membro.user.id)
    eh_proprietario = !isnothing(personagem) && haskey(get(dados_servidor["personagens"], id_usuario, Dict()), personagem)
    eh_admin = :administrator in membro.permissoes
    tem_cargo_especial = any(role -> role.id in get(dados_servidor["special_roles"], tipo_permissao, UInt64[]), membro.roles)
    return permitir_proprietario ? (eh_proprietario || eh_admin || tem_cargo_especial) : (eh_admin || tem_cargo_especial)
end

# Obtém o nome do tier correspondente ao nível informado
function obter_tier(nivel::Int, dados_servidor::Dict)
    for (nome_tier, tier_dados) in get(dados_servidor, "tiers", Dict())
        if tier_dados["nivel_min"] <= nivel && nivel <= tier_dados["nivel_max"]
            return nome_tier
        end
    end
    return nothing
end