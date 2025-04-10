module GerenciamentoPersonagens
export criar_personagem, remover_personagem, aposentar_personagem, listar_personagens

using ..PersistenciaDados

# Cria um novo personagem para o usuário
function criar_personagem(id_servidor::String, id_usuario::String, nome::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())

    if haskey(personagens_usuario, nome)
        return "Você já possui um personagem com esse nome."
    end

    novo_personagem = Dict(
        "dinheiro" => 0,
        "nivel" => 1,
        "marcos" => 0,
        "inventario" => [],
        "ultimo_trabalho" => nothing,
        "ultimo_crime" => nothing,
        "estrelas" => 0
    )

    personagens_usuario[nome] = novo_personagem
    dados_servidor["personagens"][id_usuario] = personagens_usuario

    PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)

    return "Personagem $nome criado com sucesso e vinculado à sua conta Discord! Nível inicial: 1"
end

# Remove permanentemente um personagem (função simplificada)
function remover_personagem(id_servidor::String, nome::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    id_proprietario = ""
    personagem_encontrado = false
    for (id_usuario, personagens) in dados_servidor["personagens"]
        if haskey(personagens, nome)
            id_proprietario = id_usuario
            personagem_encontrado = true
            break
        end
    end
    if !personagem_encontrado
        return "Personagem $nome não encontrado."
    end
    delete!(dados_servidor["personagens"][id_proprietario], nome)
    if isempty(dados_servidor["personagens"][id_proprietario])
        delete!(dados_servidor["personagens"], id_proprietario)
    end
    PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
    return "Personagem $nome removido com sucesso."
end

# Aposenta um personagem, movendo para a seção 'aposentados'
function aposentar_personagem(id_servidor::String, id_usuario::String, nome::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, nome)
        return "Personagem não encontrado."
    end
    if !haskey(dados_servidor, "aposentados")
        dados_servidor["aposentados"] = Dict()
    end
    dados_servidor["aposentados"][nome] = personagens_usuario[nome]
    delete!(personagens_usuario, nome)
    if isempty(personagens_usuario)
        delete!(dados_servidor["personagens"], id_usuario)
    else
        dados_servidor["personagens"][id_usuario] = personagens_usuario
    end
    PersistenciaDados.salvar_dados_servidor(id_servidor, dados_servidor)
    return "Personagem $nome foi aposentado com sucesso e seus dados foram preservados."
end

# Lista todos os personagens de um usuário
function listar_personagens(id_servidor::String, id_usuario::String)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if isempty(personagens_usuario)
        return "Você não possui personagens cadastrados."
    end
    return "Seus personagens: $(join(keys(personagens_usuario), ", "))"
end

end # do módulo