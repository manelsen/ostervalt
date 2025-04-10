# Economia.jl
# Funções relacionadas à economia do jogo (saldo, transferência, etc.)

# (Funções de saldo, adicionar/remover dinheiro, transferência entre personagens, etc. podem ser migradas aqui)

# Exemplo: função para transferir moedas entre personagens
function transferir_moedas(id_servidor::String, id_usuario_origem::String, personagem_origem::String, personagem_destino::String, quantidade::Int)
    dados_servidor = carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario_origem, Dict())

    if !haskey(personagens_usuario, personagem_origem)
        return "Você não possui um personagem chamado $personagem_origem."
    end

    # Impede transferência para si mesmo
    if personagem_destino in keys(personagens_usuario)
        return "Não é possível transferir moedas para um de seus próprios personagens."
    end

    # Busca destinatário
    destinatario_encontrado = false
    dados_destinatario = nothing
    for (id_usuario_recipient, personagens) in dados_servidor["personagens"]
        if haskey(personagens, personagem_destino) && id_usuario_recipient != id_usuario_origem
            dados_destinatario = personagens[personagem_destino]
            destinatario_encontrado = true
            break
        end
    end
    if !destinatario_encontrado
        return "O personagem destinatário '$personagem_destino' não foi encontrado ou é de sua propriedade."
    end

    dados_remetente = personagens_usuario[personagem_origem]
    if dados_remetente["dinheiro"] < quantidade
        return "$personagem_origem não tem moedas suficientes. Saldo disponível: $(dados_remetente["dinheiro"])"
    end

    dados_remetente["dinheiro"] -= quantidade
    dados_destinatario["dinheiro"] += quantidade

    salvar_dados_servidor(id_servidor, dados_servidor)
    return "Transferência realizada com sucesso! $personagem_origem enviou $quantidade moedas para $personagem_destino."
end
