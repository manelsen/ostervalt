module Acoes
export adicionar_marcos, trabalhar, pix, dinheiro, saldo, mochila, marcos, up, crime

using ..PersistenciaDados

# Função para adicionar marcos a um personagem (simplificada)
function adicionar_marcos(id_servidor::String, personagem::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagem_encontrado = false
    for (id_usuario, personagens) in dados_servidor["personagens"]
        if haskey(personagens, personagem)
            dados_personagem = personagens[personagem]
            nivel_atual = dados_personagem["nivel"]
            marcos_a_adicionar = marcos_para_ganhar(nivel_atual)
            dados_personagem["marcos"] += marcos_a_adicionar
            novos_marcos = dados_personagem["marcos"]
            novo_nivel = calcular_nivel(novos_marcos / 16)
            if novo_nivel > nivel_atual
                dados_personagem["nivel"] = novo_nivel
            end
            PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
            personagem_encontrado = true
            return "Adicionado $marcos_a_adicionar para $personagem. Total: $(formatar_marcos(novos_marcos)) (Nível $novo_nivel)"
        end
    end
    if !personagem_encontrado
        return "Personagem não encontrado."
    end
end

# Função para comando trabalhar
function trabalhar(id_servidor::String, personagem::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagem_encontrado = false
    for (id_usuario, personagens) in dados_servidor["personagens"]
        if haskey(personagens, personagem)
            dados_p = personagens[personagem]
            ganho = calcular_ganho_trabalho(dados_p["nivel"])
            dados_p["dinheiro"] += ganho
            dados_p["marcos"] += 5  # Ganho fixo de 5 marcos
            PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
            personagem_encontrado = true
            return "✨ $personagem trabalhou e ganhou $ganho moedas e 5 Marcos!"
        end
    end
    return "Personagem não encontrado."
end

# Função auxiliar para calcular ganho do trabalho
function calcular_ganho_trabalho(nivel::Int)
    base = 100
    return Int(base * (1 + nivel/10))
end

# Função para comando pix
function pix(id_servidor::String, id_usuario::String, de_personagem::String, para_personagem::String, quantidade::Int)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    id_usuario_remetente = id_usuario
    id_usuario_destinatario = nothing
    personagens_usuario_remetente = get(dados_servidor["personagens"], id_usuario_remetente, Dict())
    if !haskey(personagens_usuario_remetente, de_personagem)
        return "Você não possui um personagem chamado $de_personagem."
    end
    dados_remetente = personagens_usuario_remetente[de_personagem]
    if dados_remetente["dinheiro"] < quantidade
        return "$de_personagem não tem moedas suficientes. Saldo disponível: $(dados_remetente["dinheiro"])"
    end
    for (id_usuario_encontrado, personagens) in dados_servidor["personagens"]
        if haskey(personagens, para_personagem) && id_usuario_encontrado != id_usuario_remetente
            id_usuario_destinatario = id_usuario_encontrado
            break
        end
    end
    if isnothing(id_usuario_destinatario)
        return "O personagem destinatário '$para_personagem' não foi encontrado ou é de sua propriedade."
    end
    dados_destinatario = dados_servidor["personagens"][id_usuario_destinatario][para_personagem]
    dados_remetente["dinheiro"] -= quantidade
    dados_destinatario["dinheiro"] += quantidade
    PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
    return "Transferência realizada com sucesso!\n$de_personagem enviou $quantidade moedas para $para_personagem.\nNovo saldo de $de_personagem: $(dados_remetente["dinheiro"]) moedas"
end

# Função para comando dinheiro
function dinheiro(id_servidor::String, id_usuario::String, personagem::String, quantidade::Int)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagem_encontrado = false
    for (id_usuario_encontrado, personagens) in dados_servidor["personagens"]
        if haskey(personagens, personagem)
            dados_personagem = personagens[personagem]
            dados_personagem["dinheiro"] += quantidade
            PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
            personagem_encontrado = true
            return "Dinheiro atualizado para $personagem: $(dados_personagem["dinheiro"]) moedas"
        end
    end
    if !personagem_encontrado
        return "Personagem não encontrado."
    end
end

# Função para comando saldo
function saldo(id_servidor::String, id_usuario::String, personagem::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return "Personagem não encontrado."
    end
    dados_personagem = personagens_usuario[personagem]
    dinheiro = get(dados_personagem, "dinheiro", 0)
    return "$personagem tem $dinheiro moedas."
end

# Função para comando mochila
function mochila(id_servidor::String, id_usuario::String, personagem::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return "Personagem não encontrado."
    end
    dados_personagem = personagens_usuario[personagem]
    inventario = get(dados_personagem, "inventario", [])
    if isempty(inventario)
        return "O inventário de $personagem está vazio."
    end
    contagem_itens = Dict{String, Int}()
    for item in inventario
        contagem_itens[item] = get(contagem_itens, item, 0) + 1
    end
    itens_formatados = join(["**$item** (x$count)" for (item, count) in contagem_itens], ", ")
    return "Inventário de $personagem: $itens_formatados"
end

# Função para comando marcos
function marcos(id_servidor::String, id_usuario::String, personagem::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return "Personagem não encontrado."
    end
    dados_personagem = personagens_usuario[personagem]
    marcos = dados_personagem["marcos"]
    nivel = calcular_nivel(marcos / 16)
    return "$personagem tem $(formatar_marcos(marcos)) (Nível $nivel)"
end

# Função para comando up
function up(id_servidor::String, id_usuario::String, personagem::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return "Personagem não encontrado."
    end
    dados_personagem = personagens_usuario[personagem]
    nivel_atual = dados_personagem["nivel"]
    marcos_a_adicionar = marcos_para_ganhar(nivel_atual)
    dados_personagem["marcos"] += marcos_a_adicionar
    novos_marcos = dados_personagem["marcos"]
    novo_nivel = calcular_nivel(novos_marcos / 16)
    if novo_nivel > nivel_atual
        dados_personagem["nivel"] = novo_nivel
    end
    PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
    return "Adicionado $marcos_a_adicionar Marcos para $personagem. Total: $(formatar_marcos(novos_marcos)) (Nível $novo_nivel)"
end

# Função para comando crime
function crime(id_servidor::String, id_usuario::String, personagem::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return "Personagem não encontrado."
    end
    dados_personagem = personagens_usuario[personagem]
    probabilidade = get(dados_servidor, "probabilidade_crime", 50)
    chance = rand(1:100)
    if chance <= probabilidade
        recompensa = rand(100:500)
        dados_personagem["dinheiro"] += recompensa
        PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
        return "Sucesso! Você ganhou $recompensa moedas."
    else
        perda = rand(50:250)
        dados_personagem["dinheiro"] = max(0, dados_personagem["dinheiro"] - perda)
        PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
        return "Você foi pego! Perdeu $perda moedas."
    end
end

end # do módulo
