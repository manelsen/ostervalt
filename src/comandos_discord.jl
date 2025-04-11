# Handlers dos comandos Discord
# Este arquivo é incluído diretamente no módulo OstervaltBot.

using Ekztazy, Dates, Random, Logging, CSV, DataFrames, JSON3 # Bibliotecas externas necessárias pelos handlers

# Imports relativos/absolutos removidos, pois as funções/constantes estarão no mesmo escopo (OstervaltBot)
# Não precisa de export aqui

# === Handlers Extraídos de ostervalt.jl ===

"""
    handler_comando_criar(contexto)

Handler do comando `/criar`. Cria um novo personagem para o usuário que invocou o comando.
"""
function handler_comando_criar(contexto)
    @info "Comando /criar foi acionado por $(contexto.interaction.membro.user.username)"
    opcoes = contexto.interaction.data.opcoes

    if isnothing(opcoes) || isempty(opcoes)
        return reply(cliente, contexto, content="Por favor, forneça um nome para o personagem.")
    end

    nome = opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)

    # Chama a lógica de criação (agora no mesmo escopo OstervaltBot)
    resultado = criar_personagem(id_servidor, id_usuario, nome)

    reply(cliente, contexto, content=resultado)
    @info "Resultado da criação do personagem para $id_usuario: $resultado"
end

"""
    handler_comando_ajuda(contexto)

Handler do comando `/ajuda`. Exibe uma mensagem de ajuda formatada.
"""
function handler_comando_ajuda(contexto)
    @info "Comando /ajuda foi acionado por $(contexto.interaction.membro.user.username)"
    mensagem_ajuda = gerar_mensagem_ajuda() # Função no mesmo escopo
    reply(cliente, contexto, content=mensagem_ajuda)
    @info "Mensagem de ajuda enviada."
end

"""
    handler_comando_up(contexto)

Handler do comando `/up`. Adiciona Marcos (XP) a um personagem especificado.
"""
function handler_comando_up(contexto)
    @info "Comando /up foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Função no mesmo escopo

    # Verifica permissão (não permite dono, apenas admin ou cargo especial "marcos")
    if !verificar_permissoes(contexto.interaction.membro, personagem, "marcos", dados_servidor, false) # Função no mesmo escopo
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict()) # 'config' no mesmo escopo
        return reply(cliente, contexto, content=get(msg_erro, "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    personagem_encontrado = false
    for (id_usuario_dono, personagens_dono) in dados_servidor["personagens"]
        if haskey(personagens_dono, personagem)
            dados_personagem = personagens_dono[personagem]
            nivel_atual = dados_personagem["nivel"]
            marcos_a_adicionar = marcos_para_ganhar(nivel_atual) # Função no mesmo escopo

            dados_personagem["marcos"] += marcos_a_adicionar
            novos_marcos = dados_personagem["marcos"]
            novo_nivel = calcular_nivel(novos_marcos / 16.0) # Função no mesmo escopo

            if novo_nivel > nivel_atual
                dados_personagem["nivel"] = novo_nivel
                reply(cliente, contexto, content="$personagem subiu para o nível $novo_nivel!")
            else
                fracao_adicionada = marcos_a_adicionar == 16 ? "1 Marco" :
                                 marcos_a_adicionar == 4 ? "1/4 de Marco" :
                                 marcos_a_adicionar == 2 ? "1/8 de Marco" :
                                 marcos_a_adicionar == 1 ? "1/16 de Marco" :
                                 "$marcos_a_adicionar partes de Marco"

                reply(cliente, contexto, content="Adicionado $fracao_adicionada para $personagem. Total: $(formatar_marcos(novos_marcos)) (Nível $novo_nivel)") # Função no mesmo escopo
            end

            salvar_dados_servidor(id_servidor, dados_servidor) # Função no mesmo escopo
            personagem_encontrado = true
            @info "Marcos adicionados para $personagem por $(contexto.interaction.membro.user.username). Novo nível: $novo_nivel"
            break
        end
    end

    if !personagem_encontrado
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    handler_comando_marcos(contexto)

Handler do comando `/marcos`. Exibe os Marcos e o nível de um personagem.
"""
function handler_comando_marcos(contexto)
    @info "Comando /marcos foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "marcos", dados_servidor, false)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    personagem_encontrado = false
    for (id_usuario_dono, personagens_dono) in dados_servidor["personagens"]
        if haskey(personagens_dono, personagem)
            dados_personagem = personagens_dono[personagem]
            marcos = dados_personagem["marcos"]
            level = calcular_nivel(marcos / 16.0)
            reply(cliente, contexto, content="$personagem tem $(formatar_marcos(marcos)) (Nível $level)")
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    handler_comando_mochila(contexto)

Handler do comando `/mochila`. Exibe o inventário de um personagem ou a descrição de um item específico.
"""
function handler_comando_mochila(contexto)
    @info "Comando /mochila foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    item = length(contexto.interaction.data.opcoes) > 1 ? contexto.interaction.data.opcoes[2].value : nothing

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario_invocador = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    id_usuario_dono = nothing
    dados_personagem = nothing
    personagem_encontrado = false
    for (id_dono, personagens_dono) in dados_servidor["personagens"]
        if haskey(personagens_dono, personagem)
            id_usuario_dono = id_dono
            dados_personagem = personagens_dono[personagem]
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true)
         msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você não tem permissão para ver esta mochila."))
    end

    inventory = get(dados_personagem, "inventario", [])
    if isempty(inventory)
        return reply(cliente, contexto, content="O inventário de $personagem está vazio.")
    end

    if !isnothing(item)
        if item in inventory
            contagem_item = count(==(item), inventory)
            descricao_item = obter_descricao_item(dados_servidor, item) # Função no mesmo escopo
            reply(cliente, contexto, content="**$item** (x$contagem_item)\nDescrição: $descricao_item")
        else
            reply(cliente, contexto, content="O item '$item' não está na mochila de $personagem.")
        end
    else
        contagem_itens = Dict{String, Int}()
        for i in inventory
            contagem_itens[i] = get(contagem_itens, i, 0) + 1
        end

        items_formatted = isempty(contagem_itens) ? "vazio" : join(["**$item_nome** (x$count)" for (item_nome, count) in contagem_itens], ", ")
        reply(cliente, contexto, content="Inventário de $personagem: $items_formatted")
    end
end

"""
    handler_comando_comprar(contexto)

Handler do comando `/comprar`. Permite que um personagem compre um item da loja.
"""
function handler_comando_comprar(contexto)
    @info "Comando /comprar foi acionado por $(contexto.interaction.membro.user.username)"
    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /comprar <personagem> <item>")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    item_comprar = contexto.interaction.data.opcoes[2].value

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Você não possui um personagem com este nome."))
    end

    itens_estoque = get(dados_servidor, "itens_estoque", Dict())
    if isempty(itens_estoque)
        return reply(cliente, contexto, content="A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.")
    end

    dados_personagem = personagens_usuario[personagem]
    item_encontrado_loja = false
    compra_realizada = false

    for (raridade, itens_raridade) in itens_estoque
        nomes_itens = get(itens_raridade, "Name", [])
        if item_comprar in nomes_itens
            item_encontrado_loja = true
            indice_item = findfirst(==(item_comprar), nomes_itens)

            if !isnothing(indice_item) && itens_raridade["Quantity"][indice_item] > 0
                valor_item_str = itens_raridade["Value"][indice_item]
                valor_item = tryparse(Int, valor_item_str)

                if isnothing(valor_item)
                     @error "Valor inválido para o item '$item_comprar' na loja: $valor_item_str"
                     reply(cliente, contexto, content="Erro interno ao processar o preço do item. Contate um administrador.")
                     break
                end

                if dados_personagem["dinheiro"] < valor_item
                    reply(cliente, contexto, content="$personagem não tem dinheiro suficiente para comprar $item_comprar. Preço: $valor_item, Dinheiro disponível: $(dados_personagem["dinheiro"])")
                else
                    dados_personagem["dinheiro"] -= valor_item
                    push!(dados_personagem["inventario"], item_comprar)
                    itens_raridade["Quantity"][indice_item] -= 1

                    reply(cliente, contexto, content="$personagem comprou $item_comprar por $valor_item moedas. Dinheiro restante: $(dados_personagem["dinheiro"])")
                    salvar_dados_servidor(id_servidor, dados_servidor)
                    compra_realizada = true
                    @info "$personagem (User: $id_usuario) comprou $item_comprar."
                end
            else
                reply(cliente, contexto, content="Desculpe, $item_comprar está fora de estoque.")
            end
            break
        end
    end

    if !item_encontrado_loja
        reply(cliente, contexto, content="Item '$item_comprar' não encontrado na loja.")
    end
end


"""
    handler_comando_dinheiro(contexto)

Handler do comando `/dinheiro`. Adiciona ou remove dinheiro do saldo de um personagem.
"""
function handler_comando_dinheiro(contexto)
    @info "Comando /dinheiro foi acionado por $(contexto.interaction.membro.user.username)"
    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /dinheiro <personagem> <quantidade>")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    quantidade_str = contexto.interaction.data.opcoes[2].value
    quantidade = tryparse(Int, quantidade_str)

    if isnothing(quantidade)
        return reply(cliente, contexto, content="Quantidade inválida. Por favor, forneça um número inteiro.")
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, personagem, "saldo", dados_servidor, false)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "dinheiro_permissao", "Você não tem permissão para usar este comando."))
    end

    personagem_encontrado = false
    for (id_usuario_dono, personagens_dono) in dados_servidor["personagens"]
        if haskey(personagens_dono, personagem)
            dados_personagem = personagens_dono[personagem]
            saldo_anterior = dados_personagem["dinheiro"]
            dados_personagem["dinheiro"] = max(0, saldo_anterior + quantidade)

            if quantidade > 0
                reply(cliente, contexto, content="Adicionado $quantidade moedas ao saldo de $personagem. Novo saldo: $(dados_personagem["dinheiro"]) moedas.")
            elseif quantidade < 0
                 dinheiro_removido = min(saldo_anterior, abs(quantidade))
                 reply(cliente, contexto, content="Removido $dinheiro_removido moedas do saldo de $personagem. Novo saldo: $(dados_personagem["dinheiro"]) moedas.")
            else
                 reply(cliente, contexto, content="Nenhuma alteração no saldo de $personagem. Saldo atual: $(dados_personagem["dinheiro"]) moedas.")
            end

            salvar_dados_servidor(id_servidor, dados_servidor)
            personagem_encontrado = true
            @info "Saldo de $personagem alterado em $quantidade por $(contexto.interaction.membro.user.username). Novo saldo: $(dados_personagem["dinheiro"])"
            break
        end
    end

    if !personagem_encontrado
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Personagem não encontrado."))
    end
end

"""
    handler_comando_saldo(contexto)

Handler do comando `/saldo`. Exibe o saldo de moedas de um personagem.
"""
function handler_comando_saldo(contexto)
    @info "Comando /saldo foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    personagem_encontrado = false
    dados_personagem = nothing
    for (id_usuario_dono, personagens_dono) in dados_servidor["personagens"]
        if haskey(personagens_dono, personagem)
            dados_personagem = personagens_dono[personagem]
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você não tem permissão para ver este saldo."))
    end

    money = get(dados_personagem, "dinheiro", 0)
    reply(cliente, contexto, content="$personagem tem $money moedas.")
end

"""
    handler_comando_pix(contexto)

Handler do comando `/pix`. Transfere moedas entre dois personagens.
"""
function handler_comando_pix(contexto)
    @info "Comando /pix foi acionado por $(contexto.interaction.membro.user.username)"
    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /pix <de_personagem> <para_personagem> <quantidade>")
    end

    personagem_origem = contexto.interaction.data.opcoes[1].value
    personagem_destino = contexto.interaction.data.opcoes[2].value
    quantidade_str = contexto.interaction.data.opcoes[3].value
    quantidade = tryparse(Int, quantidade_str)

    if isnothing(quantidade) || quantidade <= 0
        return reply(cliente, contexto, content="A quantidade deve ser um número inteiro maior que zero.")
    end

    if personagem_origem == personagem_destino
        return reply(cliente, contexto, content="Personagem de origem e destino não podem ser os mesmos.")
    end

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario_remetente = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    personagens_remetente = get(dados_servidor["personagens"], id_usuario_remetente, Dict())
    if !haskey(personagens_remetente, personagem_origem)
        return reply(cliente, contexto, content="Você não possui um personagem chamado '$personagem_origem'.")
    end
    dados_remetente = personagens_remetente[personagem_origem]

    destinatario_encontrado = false
    id_usuario_destinatario = nothing
    dados_destinatario = nothing
    for (id_dono, personagens_dono) in dados_servidor["personagens"]
        if haskey(personagens_dono, personagem_destino)
            if id_dono == id_usuario_remetente
                 return reply(cliente, contexto, content="Não é possível transferir moedas para um de seus próprios personagens.")
            end
            id_usuario_destinatario = id_dono
            dados_destinatario = personagens_dono[personagem_destino]
            destinatario_encontrado = true
            break
        end
    end

    if !destinatario_encontrado
        return reply(cliente, contexto, content="O personagem destinatário '$personagem_destino' não foi encontrado.")
    end

    if dados_remetente["dinheiro"] < quantidade
        return reply(cliente, contexto, content="$personagem_origem não tem moedas suficientes. Saldo disponível: $(dados_remetente["dinheiro"])")
    end

    dados_remetente["dinheiro"] -= quantidade
    dados_destinatario["dinheiro"] += quantidade

    salvar_dados_servidor(id_servidor, dados_servidor)

    reply(cliente, contexto, content="Transferência realizada com sucesso!\n$personagem_origem enviou $quantidade moedas para $personagem_destino.\nNovo saldo de $personagem_origem: $(dados_remetente["dinheiro"]) moedas.")
    @info "Pix de $quantidade moedas de $personagem_origem (User: $id_usuario_remetente) para $personagem_destino (User: $id_usuario_destinatario)."
end

"""
    handler_comando_trabalhar(contexto)

Handler do comando `/trabalhar`. Permite que um personagem trabalhe para ganhar moedas.
"""
function handler_comando_trabalhar(contexto)
    @info "Comando /trabalhar foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Você não possui um personagem com este nome."))
    end
    dados_personagem = personagens_usuario[personagem]

    ultimo_trabalho_str = get(dados_personagem, "ultimo_trabalho", nothing)
    now_time = Dates.now()
    intervalo_trabalhar_s = get(get(config, "limites", Dict()), "intervalo_trabalhar", 86400)
    if !isnothing(ultimo_trabalho_str)
        ultimo_trabalho_dt = tryparse(DateTime, ultimo_trabalho_str)
        if !isnothing(ultimo_trabalho_dt)
            tempo_passado_ms = Dates.value(now_time - ultimo_trabalho_dt)
            if tempo_passado_ms < intervalo_trabalhar_s * 1000
                tempo_restante_s = ceil(Int, (intervalo_trabalhar_s * 1000 - tempo_passado_ms) / 1000)
                msg_cooldown = get(get(config, "messages", Dict()), "erros", Dict())
                return reply(cliente, contexto, content=get(msg_cooldown, "acao_frequente", "Você já trabalhou recentemente. Aguarde $tempo_restante_s segundos."))
            end
        else
             @warn "Timestamp inválido para ultimo_trabalho do personagem $personagem: $ultimo_trabalho_str"
        end
    end

    nivel = get(dados_personagem, "nivel", 1)
    nome_tier = obter_tier(nivel, dados_servidor)
    recompensa = 0
    if !isnothing(nome_tier) && haskey(dados_servidor["tiers"], nome_tier)
        tier_info = dados_servidor["tiers"][nome_tier]
        recompensa = get(tier_info, "recompensa", 0)
    else
         recompensa = get(get(config, "recompensas_padrao", Dict()), "trabalho", 50)
         @warn "Tier '$nome_tier' não encontrado ou sem recompensa definida para nível $nivel. Usando recompensa padrão: $recompensa"
    end

    if recompensa <= 0
         @warn "Recompensa de trabalho calculada como $recompensa para $personagem (Nível $nivel, Tier: $nome_tier). Verifique a configuração."
         return reply(cliente, contexto, content="Ocorreu um problema ao calcular sua recompensa. Contate um administrador.")
    end

    dados_personagem["dinheiro"] += recompensa
    dados_personagem["ultimo_trabalho"] = string(now_time)

    mensagens_trabalho = get(get(dados_servidor, "messages", Dict()), "trabalho", get(config["messages"], "trabalho", ["Você trabalhou duro e ganhou sua recompensa!"]))
    mensagem = rand(mensagens_trabalho)

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="$mensagem\nVocê ganhou $recompensa moedas. Saldo atual: $(dados_personagem["dinheiro"]) moedas.")
    @info "$personagem (User: $id_usuario) trabalhou e ganhou $recompensa moedas."
end

"""
    handler_comando_crime(contexto)

Handler do comando `/crime`. Permite que um personagem tente cometer um crime.
"""
function handler_comando_crime(contexto)
    @info "Comando /crime foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Você não possui um personagem com este nome."))
    end
    dados_personagem = personagens_usuario[personagem]

    ultimo_crime_str = get(dados_personagem, "ultimo_crime", nothing)
    now_time = Dates.now()
    intervalo_crime_s = get(get(config, "limites", Dict()), "intervalo_crime", 86400)
    if !isnothing(ultimo_crime_str)
         ultimo_crime_dt = tryparse(DateTime, ultimo_crime_str)
         if !isnothing(ultimo_crime_dt)
            tempo_passado_ms = Dates.value(now_time - ultimo_crime_dt)
            if tempo_passado_ms < intervalo_crime_s * 1000
                tempo_restante_s = ceil(Int, (intervalo_crime_s * 1000 - tempo_passado_ms) / 1000)
                msg_cooldown = get(get(config, "messages", Dict()), "erros", Dict())
                return reply(cliente, contexto, content=get(msg_cooldown, "acao_frequente", "Você já cometeu um crime recentemente. Aguarde $tempo_restante_s segundos."))
            end
        else
            @warn "Timestamp inválido para ultimo_crime do personagem $personagem: $ultimo_crime_str"
        end
    end

    probabilidade_sucesso = get(dados_servidor, "probabilidade_crime", get(get(config, "probabilidades", Dict()), "crime", 50))
    chance = rand(1:100)

    mensagens_crime = get(get(dados_servidor, "messages", Dict()), "crime", get(config["messages"], "crime", ["Você tentou cometer um crime..."]))
    mensagem = rand(mensagens_crime)

    resultado_str = ""
    ganho_perda = 0

    if chance <= probabilidade_sucesso
        recompensa_min = get(get(config, "recompensas_crime", Dict()), "min", 100)
        recompensa_max = get(get(config, "recompensas_crime", Dict()), "max", 500)
        ganho_perda = rand(recompensa_min:recompensa_max)
        dados_personagem["dinheiro"] += ganho_perda
        resultado_str = "Sucesso! Você ganhou $ganho_perda moedas."
    else
        perda_min = get(get(config, "perdas_crime", Dict()), "min", 50)
        perda_max = get(get(config, "perdas_crime", Dict()), "max", 250)
        perda = rand(perda_min:perda_max)
        saldo_anterior = dados_personagem["dinheiro"]
        dados_personagem["dinheiro"] = max(0, saldo_anterior - perda)
        ganho_perda = -(min(saldo_anterior, perda))
        resultado_str = "Você foi pego! Perdeu $(abs(ganho_perda)) moedas."
    end

    dados_personagem["ultimo_crime"] = string(now_time)
    dados_personagem["estrelas"] = get(dados_personagem, "estrelas", 0) + 1

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="$mensagem\n$resultado_str\nSaldo atual: $(dados_personagem["dinheiro"]) moedas.")
    @info "$personagem (User: $id_usuario) tentou um crime. Resultado: $resultado_str (Prob: $probabilidade_sucesso%, Rolou: $chance). Saldo: $(dados_personagem["dinheiro"])"
end

"""
    handler_comando_cargos(contexto)

Handler do comando `/cargos`. Gerencia cargos especiais para permissões.
"""
function handler_comando_cargos(contexto)
    @info "Comando /cargos foi acionado por $(contexto.interaction.membro.user.username)"
    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /cargos <tipo> <acao> <cargo>")
    end

    tipo = contexto.interaction.data.opcoes[1].value
    acao = contexto.interaction.data.opcoes[2].value
    nome_cargo = contexto.interaction.data.opcoes[3].value

    usuario = contexto.interaction.membro
    guild_future = get_guild(cliente, contexto.interaction.id_guilda)
    guild = fetch(guild_future).val
    if isnothing(guild)
         @error "Não foi possível obter informações da Guild $(contexto.interaction.id_guilda)"
         return reply(cliente, contexto, content="Erro ao obter informações do servidor.")
    end
    permissoes = Ekztazy.permissions(usuario, guild)

    if !has_permission(permissoes, Ekztazy.PERM_ADMINISTRATOR)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você precisa ser administrador para usar este comando."))
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    tipos_validos = ["saldo", "marcos", "loja", "view"]
    if !(tipo in tipos_validos)
        return reply(cliente, contexto, content="Tipo inválido. Use: $(join(tipos_validos, ", "))")
    end
    if !(acao in ["add", "remove"])
        return reply(cliente, contexto, content="Ação inválida. Use 'add' ou 'remove'.")
    end

    cargo_encontrado = nothing
    for role in guild.roles
        if lowercase(role.name) == lowercase(nome_cargo)
            cargo_encontrado = role
            break
        end
    end

    if isnothing(cargo_encontrado)
        return reply(cliente, contexto, content="Cargo '$nome_cargo' não encontrado neste servidor.")
    end
    id_cargo = cargo_encontrado.id

    special_roles = get!(dados_servidor, "special_roles", Dict{String, Any}())
    lista_cargos = get!(special_roles, tipo, UInt64[])

    if acao == "add"
        if !(id_cargo in lista_cargos)
            push!(lista_cargos, id_cargo)
            reply(cliente, contexto, content="Cargo '$(cargo_encontrado.name)' adicionado às permissões de '$tipo'.")
            @info "Cargo $(cargo_encontrado.name) ($id_cargo) adicionado a '$tipo' por $(usuario.user.username)"
        else
            reply(cliente, contexto, content="Cargo '$(cargo_encontrado.name)' já possui permissão para '$tipo'.")
        end
    elseif acao == "remove"
        if id_cargo in lista_cargos
            filter!(id -> id != id_cargo, lista_cargos)
            reply(cliente, contexto, content="Cargo '$(cargo_encontrado.name)' removido das permissões de '$tipo'.")
             @info "Cargo $(cargo_encontrado.name) ($id_cargo) removido de '$tipo' por $(usuario.user.username)"
        else
            reply(cliente, contexto, content="Cargo '$(cargo_encontrado.name)' não possuía permissão para '$tipo'.")
        end
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
end


"""
    handler_comando_estoque(contexto)

Handler do comando `/estoque`. Reabastece a loja com itens aleatórios de um CSV.
"""
function handler_comando_estoque(contexto)
    @info "Comando /estoque foi acionado por $(contexto.interaction.membro.user.username)"
    if length(contexto.interaction.data.opcoes) < 4
        return reply(cliente, contexto, content="Uso incorreto. Use: /estoque <comum> <incomum> <raro> <muito_raro>")
    end

    quantidades_raridade = Dict{String, Int}()
    nomes_raridade = ["comum", "incomum", "raro", "muito_raro"]
    raridades_map = Dict("comum" => "common", "incomum" => "uncommon", "raro" => "rare", "muito_raro" => "very rare")

    for (i, nome_pt) in enumerate(nomes_raridade)
        valor_str = contexto.interaction.data.opcoes[i].value
        qnt = tryparse(Int, valor_str)
        if isnothing(qnt) || qnt < 0
            return reply(cliente, contexto, content="Quantidade inválida para '$nome_pt'. Use números inteiros não negativos.")
        end
        quantidades_raridade[raridades_map[nome_pt]] = qnt
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor, false)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você não tem permissão para gerenciar o estoque."))
    end

    dados_servidor["itens_estoque"] = Dict{String, Any}()

    csv_file = isfile("items_$(id_servidor).csv") ? "items_$(id_servidor).csv" : "items.csv"
    todos_itens_df = nothing
    try
        todos_itens_df = CSV.read(csv_file, DataFrame)
        colunas_necessarias = ["Name", "Rarity", "Text"]
        if !all(col -> col in names(todos_itens_df), colunas_necessarias)
             @error "Arquivo CSV '$csv_file' não contém as colunas necessárias: Name, Rarity, Text."
             return reply(cliente, contexto, content="Erro: Formato inválido do arquivo de itens '$csv_file'. Faltam colunas.")
        end
    catch e
        @error "Erro ao ler o arquivo CSV '$csv_file'" exception=(e, catch_backtrace())
        return reply(cliente, contexto, content="Erro: Não foi possível ler o arquivo de itens '$csv_file'. Verifique se ele existe e tem permissões corretas.")
    end

    reply(cliente, contexto, content="Criando novo estoque a partir de '$csv_file'. Por favor, defina os preços para cada item selecionado.")

    for (raridade_en, count_desejado) in quantidades_raridade
        if count_desejado == 0 continue end

        itens_disponiveis_raridade = filter(row -> lowercase(row.Rarity) == raridade_en, todos_itens_df)
        contagem_disponivel = nrow(itens_disponiveis_raridade)

        if contagem_disponivel == 0
            @warn "Nenhum item encontrado para a raridade '$raridade_en' no arquivo '$csv_file'."
            continue
        end

        count_real = min(count_desejado, contagem_disponivel)

        indices_selecionados = rand(1:contagem_disponivel, count_real)
        itens_selecionados_df = itens_disponiveis_raridade[indices_selecionados, :]

        dados_servidor["itens_estoque"][raridade_en] = Dict(
            "Name" => String.(itens_selecionados_df.Name),
            "Value" => String[],
            "Quantity" => fill(1, count_real),
            "Text" => String.(itens_selecionados_df.Text)
        )

        reply(cliente, contexto, content="--- Definindo preços para itens de raridade: $raridade_en ---")
        for nome_item in dados_servidor["itens_estoque"][raridade_en]["Name"]
            preco_definido = false
            attempts = 0
            preco_final_str = ""
            while !preco_definido && attempts < 3
                reply(cliente, contexto, content="Digite o preço para **$nome_item**: (Apenas números)")
                resposta = aguardar_mensagem(contexto)
                if resposta === nothing
                    reply(cliente, contexto, content="Tempo esgotado para definir o preço de $nome_item.")
                    break
                end

                preco_int = tryparse(Int, strip(resposta))
                if !isnothing(preco_int) && preco_int >= 0
                    preco_final_str = string(preco_int)
                    push!(dados_servidor["itens_estoque"][raridade_en]["Value"], preco_final_str)
                    atualizar_preco_item(id_servidor, nome_item, preco_final_str)
                    reply(cliente, contexto, content="Preço de '$nome_item' definido como $preco_final_str moedas.")
                    preco_definido = true
                else
                    reply(cliente, contexto, content="Preço inválido. Por favor, digite um número inteiro não negativo.")
                    attempts += 1
                end
            end

            if !preco_definido
                preco_padrao = get(get(config, "precos_padroes", Dict()), raridade_en, 100)
                preco_final_str = string(preco_padrao)
                push!(dados_servidor["itens_estoque"][raridade_en]["Value"], preco_final_str)
                atualizar_preco_item(id_servidor, nome_item, preco_final_str)
                reply(cliente, contexto, content="Falha ao definir preço para '$nome_item'. Usando preço padrão de $preco_final_str moedas.")
            end
        end
    end

    salvar_dados_servidor(id_servidor, dados_servidor)

    summary = "--- Resumo do Novo Estoque ---\n"
    if isempty(dados_servidor["itens_estoque"])
        summary *= "Nenhum item foi adicionado ao estoque."
    else
        for (raridade, itens) in dados_servidor["itens_estoque"]
            num_itens = length(get(itens, "Name", []))
            if num_itens > 0
                summary *= "- **$raridade**: $num_itens itens\n"
            end
        end
    end

    reply(cliente, contexto, content=summary)
    reply(cliente, contexto, content="Estoque atualizado e preços salvos!")
    @info "Estoque reabastecido para servidor $id_servidor por $(contexto.interaction.membro.user.username)."
end

"""
    handler_comando_loja(contexto)

Handler do comando `/loja`. Exibe os itens disponíveis na loja.
"""
function handler_comando_loja(contexto)
    @info "Comando /loja foi acionado por $(contexto.interaction.membro.user.username)"
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    itens_estoque = get(dados_servidor, "itens_estoque", Dict())
    if isempty(itens_estoque) || all(isempty(get(d, "Name", [])) for d in values(itens_estoque))
        return reply(cliente, contexto, content="A loja está vazia no momento.")
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if isempty(personagens_usuario)
        return reply(cliente, contexto, content="Você não tem nenhum personagem para visitar a loja. Use `/criar` primeiro.")
    end

    nomes_personagens = collect(keys(personagens_usuario))
    msg_selecao = "Escolha o personagem para ver a loja:\n" * join("- " .* nomes_personagens, "\n")
    reply(cliente, contexto, content=msg_selecao)

    resposta = aguardar_mensagem(contexto)
    if resposta === nothing
        return
    end
    personagem_selecionado = strip(resposta)

    if !haskey(personagens_usuario, personagem_selecionado)
        return reply(cliente, contexto, content="Personagem inválido selecionado.")
    end
    dados_personagem_selecionado = personagens_usuario[personagem_selecionado]

    itens_para_exibir = []
    for (raridade, itens_raridade) in itens_estoque
        nomes = get(itens_raridade, "Name", [])
        valores = get(itens_raridade, "Value", [])
        quantidades = get(itens_raridade, "Quantity", [])
        textos = get(itens_raridade, "Text", [])

        min_len = min(length(nomes), length(valores), length(quantidades), length(textos))

        for i in 1:min_len
            if quantidades[i] > 0
                push!(itens_para_exibir, Dict(
                    "Name" => nomes[i],
                    "Value" => valores[i],
                    "Quantity" => quantidades[i],
                    "Text" => textos[i],
                    "Rarity" => raridade
                ))
            end
        end
    end

    if isempty(itens_para_exibir)
        return reply(cliente, contexto, content="Não há itens disponíveis na loja no momento.")
    end

    reply(cliente, contexto, content="--- Itens Disponíveis na Loja ---")
    for item in itens_para_exibir
        reply(cliente, contexto, content="""
        **$(item["Name"])** [$(item["Rarity"])]
        Preço: $(item["Value"]) moedas
        Quantidade: $(item["Quantity"])
        Descrição: $(item["Text"])
        """)
    end

    saldo_personagem = get(dados_personagem_selecionado, "dinheiro", 0)
    reply(cliente, contexto, content="--- Saldo de $personagem_selecionado: $saldo_personagem moedas ---")
end

"""
    handler_comando_inserir(contexto)

Handler do comando `/inserir`. Adiciona um item específico ao estoque da loja.
"""
function handler_comando_inserir(contexto)
    @info "Comando /inserir foi acionado por $(contexto.interaction.membro.user.username)"
    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /inserir <raridade> <item> <quantidade> [valor]")
    end

    raridade = lowercase(contexto.interaction.data.opcoes[1].value)
    item_nome = contexto.interaction.data.opcoes[2].value
    quantidade_str = contexto.interaction.data.opcoes[3].value
    valor_str = length(contexto.interaction.data.opcoes) >= 4 ? contexto.interaction.data.opcoes[4].value : nothing

    quantidade = tryparse(Int, quantidade_str)
    if isnothing(quantidade) || quantidade <= 0
        return reply(cliente, contexto, content="Quantidade inválida. Deve ser um número inteiro positivo.")
    end

    valor_int = nothing
    if !isnothing(valor_str)
        valor_int = tryparse(Int, valor_str)
        if isnothing(valor_int) || valor_int < 0
            return reply(cliente, contexto, content="Valor inválido. Deve ser um número inteiro não negativo.")
        end
    end

    raridades_validas = ["common", "uncommon", "rare", "very rare"]
    if !(raridade in raridades_validas)
         return reply(cliente, contexto, content="Raridade inválida. Use: $(join(raridades_validas, ", "))")
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor, false)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você não tem permissão para gerenciar o estoque."))
    end

    itens_estoque = get!(dados_servidor, "itens_estoque", Dict{String, Any}())
    estoque_raridade = get!(itens_estoque, raridade, Dict(
        "Name" => String[], "Value" => String[], "Quantity" => Int[], "Text" => String[]
    ))

    indice_existente = findfirst(==(item_nome), estoque_raridade["Name"])

    if !isnothing(indice_existente)
        estoque_raridade["Quantity"][indice_existente] += quantidade
        if !isnothing(valor_int)
            valor_final_str = string(valor_int)
            estoque_raridade["Value"][indice_existente] = valor_final_str
            atualizar_preco_item(id_servidor, item_nome, valor_final_str)
            @info "Valor do item existente '$item_nome' atualizado para $valor_final_str."
        end
        @info "Quantidade do item existente '$item_nome' incrementada em $quantidade."
    else
        push!(estoque_raridade["Name"], item_nome)
        push!(estoque_raridade["Quantity"], quantidade)
        push!(estoque_raridade["Text"], "Descrição a ser definida.")

        valor_final_str = ""
        if !isnothing(valor_int)
            valor_final_str = string(valor_int)
        else
            preco_global = get(get(dados_servidor, "precos", Dict()), item_nome, nothing)
            if !isnothing(preco_global)
                valor_final_str = string(preco_global)
            else
                preco_padrao = get(get(config, "precos_padroes", Dict()), raridade, 100)
                valor_final_str = string(preco_padrao)
                @warn "Preço não fornecido nem encontrado globalmente para '$item_nome'. Usando padrão $valor_final_str."
            end
        end
        push!(estoque_raridade["Value"], valor_final_str)
        atualizar_preco_item(id_servidor, item_nome, valor_final_str)
        @info "Novo item '$item_nome' adicionado com quantidade $quantidade e valor $valor_final_str."
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Item '$item_nome' (x$quantidade) inserido/atualizado no estoque ($raridade) com sucesso.")
end

"""
    handler_comando_remover(contexto)

Handler do comando `/remover`. Remove um item do estoque da loja.
"""
function handler_comando_remover(contexto)
    @info "Comando /remover foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do item a ser removido.")
    end

    item_nome = contexto.interaction.data.opcoes[1].value
    quantidade_str = length(contexto.interaction.data.opcoes) >= 2 ? contexto.interaction.data.opcoes[2].value : nothing
    quantidade_remover = nothing
    if !isnothing(quantidade_str)
        quantidade_remover = tryparse(Int, quantidade_str)
        if isnothing(quantidade_remover) || quantidade_remover <= 0
            return reply(cliente, contexto, content="Quantidade inválida. Deve ser um número inteiro positivo.")
        end
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor, false)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você não tem permissão para gerenciar o estoque."))
    end

    item_encontrado = false
    remocao_realizada = false
    for (raridade, estoque_raridade) in get(dados_servidor, "itens_estoque", Dict())
        nomes = get(estoque_raridade, "Name", [])
        indice_item = findfirst(==(item_nome), nomes)

        if !isnothing(indice_item)
            item_encontrado = true
            quantidade_atual = estoque_raridade["Quantity"][indice_item]

            if isnothing(quantidade_remover) || quantidade_remover >= quantidade_atual
                deleteat!(estoque_raridade["Name"], indice_item)
                deleteat!(estoque_raridade["Value"], indice_item)
                deleteat!(estoque_raridade["Quantity"], indice_item)
                deleteat!(estoque_raridade["Text"], indice_item)
                reply(cliente, contexto, content="Item '$item_nome' removido completamente do estoque ($raridade).")
                remocao_realizada = true
                @info "Item '$item_nome' removido completamente ($raridade) por $(contexto.interaction.membro.user.username)."
            else
                estoque_raridade["Quantity"][indice_item] -= quantidade_remover
                reply(cliente, contexto, content="Removido $quantidade_remover de '$item_nome' ($raridade). Quantidade restante: $(estoque_raridade["Quantity"][indice_item])")
                remocao_realizada = true
                 @info "Removido $quantidade_remover de '$item_nome' ($raridade) por $(contexto.interaction.membro.user.username). Restante: $(estoque_raridade["Quantity"][indice_item])"
            end
            break
        end
    end

    if !item_encontrado
        reply(cliente, contexto, content="Item '$item_nome' não encontrado no estoque.")
    elseif remocao_realizada
        salvar_dados_servidor(id_servidor, dados_servidor)
    end
end

"""
    limpar_handler_comando_estoque(contexto)

Handler do comando `/limpar_estoque`. Remove todos os itens do estoque da loja.
"""
function limpar_handler_comando_estoque(contexto)
    @info "Comando /limpar_estoque foi acionado por $(contexto.interaction.membro.user.username)"
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor, false)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você não tem permissão para limpar o estoque."))
    end

    dados_servidor["itens_estoque"] = Dict{String, Any}()
    salvar_dados_servidor(id_servidor, dados_servidor)

    reply(cliente, contexto, content="O estoque da loja foi limpo com sucesso.")
    @info "Estoque limpo para servidor $id_servidor por $(contexto.interaction.membro.user.username)."
end

"""
    backhandler_comando_up(contexto)

Handler do comando `/backup`. Cria e envia um backup dos dados do servidor em formato JSON.
"""
function backhandler_comando_up(contexto) # Renomear para handler_comando_backup seria mais claro
    @info "Comando /backup foi acionado por $(contexto.interaction.membro.user.username)"
    usuario = contexto.interaction.membro

    guild_future = get_guild(cliente, contexto.interaction.id_guilda)
    guild = fetch(guild_future).val
     if isnothing(guild)
         @error "Não foi possível obter informações da Guild $(contexto.interaction.id_guilda) para backup"
         return reply(cliente, contexto, content="Erro ao obter informações do servidor para backup.")
    end
    permissoes = Ekztazy.permissions(usuario, guild)
    if !has_permission(permissoes, Ekztazy.PERM_ADMINISTRATOR)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você precisa ser administrador para usar este comando."))
    end

    id_servidor = string(contexto.interaction.id_guilda)

    dados_backup_json = exportar_dados_json(id_servidor) # Função no mesmo escopo

    if length(dados_backup_json) <= 1990
        reply(cliente, contexto, content="```json\n$(dados_backup_json)\n```")
        @info "Backup enviado como mensagem para servidor $id_servidor."
    else
        backup_filename = "backup_$(id_servidor).json"
        try
            open(backup_filename, "w") do f
                write(f, dados_backup_json)
            end
            reply(cliente, contexto, content="O backup dos dados é muito grande para ser enviado como mensagem. Foi salvo no arquivo `$backup_filename` no diretório do bot.")
            @info "Backup salvo no arquivo $backup_filename para servidor $id_servidor."
        catch e
            @error "Erro ao salvar arquivo de backup $backup_filename" exception=(e, catch_backtrace())
            reply(cliente, contexto, content="Erro ao salvar o arquivo de backup no servidor.")
        end
    end
end

"""
    handler_comando_mensagens(contexto)

Handler do comando `/mensagens`. Adiciona mensagens personalizadas para eventos.
"""
function handler_comando_mensagens(contexto)
    @info "Comando /mensagens foi acionado por $(contexto.interaction.membro.user.username)"
    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /mensagens <tipo> <mensagem>")
    end

    tipo = contexto.interaction.data.opcoes[1].value
    mensagem = contexto.interaction.data.opcoes[2].value

    usuario = contexto.interaction.membro
    guild_future = get_guild(cliente, contexto.interaction.id_guilda)
    guild = fetch(guild_future).val
     if isnothing(guild)
         @error "Não foi possível obter informações da Guild $(contexto.interaction.id_guilda) para /mensagens"
         return reply(cliente, contexto, content="Erro ao obter informações do servidor.")
    end
    permissoes = Ekztazy.permissions(usuario, guild)
    if !has_permission(permissoes, Ekztazy.PERM_ADMINISTRATOR)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você precisa ser administrador para usar este comando."))
    end

    tipos_validos = ["trabalho", "crime"]
    if !(tipo in tipos_validos)
         return reply(cliente, contexto, content="Tipo de mensagem inválido. Tipos válidos: $(join(tipos_validos, ", "))")
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    mensagens_servidor = get!(dados_servidor, "messages", Dict{String, Any}())
    lista_mensagens = get!(mensagens_servidor, tipo, String[])
    push!(lista_mensagens, mensagem)

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Mensagem adicionada para o evento '$tipo' com sucesso.")
    @info "Mensagem para '$tipo' adicionada no servidor $id_servidor por $(usuario.user.username)."
end

"""
    handler_comando_tiers(contexto)

Handler do comando `/tiers`. Configura os tiers de nível (min, max, recompensa).
"""
function handler_comando_tiers(contexto)
    @info "Comando /tiers foi acionado por $(contexto.interaction.membro.user.username)"
    if length(contexto.interaction.data.opcoes) < 4
        return reply(cliente, contexto, content="Uso incorreto. Use: /tiers <tier> <nivel_min> <nivel_max> <recompensa>")
    end

    tier_nome = contexto.interaction.data.opcoes[1].value
    nivel_min_str = contexto.interaction.data.opcoes[2].value
    nivel_max_str = contexto.interaction.data.opcoes[3].value
    recompensa_str = contexto.interaction.data.opcoes[4].value

    nivel_min = tryparse(Int, nivel_min_str)
    nivel_max = tryparse(Int, nivel_max_str)
    recompensa = tryparse(Int, recompensa_str)

    if isnothing(nivel_min) || nivel_min < 1
        return reply(cliente, contexto, content="Nível mínimo inválido. Deve ser um número inteiro maior ou igual a 1.")
    end
    if isnothing(nivel_max) || nivel_max < nivel_min
        return reply(cliente, contexto, content="Nível máximo inválido. Deve ser um número inteiro maior ou igual ao nível mínimo.")
    end
     if isnothing(recompensa) || recompensa < 0
        return reply(cliente, contexto, content="Recompensa inválida. Deve ser um número inteiro não negativo.")
    end

    usuario = contexto.interaction.membro
    guild_future = get_guild(cliente, contexto.interaction.id_guilda)
    guild = fetch(guild_future).val
     if isnothing(guild)
         @error "Não foi possível obter informações da Guild $(contexto.interaction.id_guilda) para /tiers"
         return reply(cliente, contexto, content="Erro ao obter informações do servidor.")
    end
    permissoes = Ekztazy.permissions(usuario, guild)
    if !has_permission(permissoes, Ekztazy.PERM_ADMINISTRATOR)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você precisa ser administrador para usar este comando."))
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    tiers_servidor = get!(dados_servidor, "tiers", Dict{String, Any}())
    tiers_servidor[tier_nome] = Dict(
        "nivel_min" => nivel_min,
        "nivel_max" => nivel_max,
        "recompensa" => recompensa
    )

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Tier '$tier_nome' definido para níveis $nivel_min-$nivel_max com recompensa de $recompensa moedas.")
    @info "Tier '$tier_nome' configurado no servidor $id_servidor por $(usuario.user.username)."
end

"""
    prob_handler_comando_crime(contexto)

Handler do comando `/probabilidade_crime`. Define a probabilidade de sucesso em crimes.
"""
function prob_handler_comando_crime(contexto)
    @info "Comando /probabilidade_crime foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça a probabilidade de sucesso do crime (0-100).")
    end

    probabilidade_str = contexto.interaction.data.opcoes[1].value
    probabilidade = tryparse(Int, probabilidade_str)

    if isnothing(probabilidade) || !(0 <= probabilidade <= 100)
        return reply(cliente, contexto, content="Probabilidade inválida. Por favor, insira um número inteiro entre 0 e 100.")
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor)

    usuario = contexto.interaction.membro
    guild_future = get_guild(cliente, contexto.interaction.id_guilda)
    guild = fetch(guild_future).val
     if isnothing(guild)
         @error "Não foi possível obter informações da Guild $(contexto.interaction.id_guilda) para /probabilidade_crime"
         return reply(cliente, contexto, content="Erro ao obter informações do servidor.")
    end
    permissoes = Ekztazy.permissions(usuario, guild)
    if !has_permission(permissoes, Ekztazy.PERM_ADMINISTRATOR)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você precisa ser administrador para usar este comando."))
    end

    dados_servidor["probabilidade_crime"] = probabilidade
    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Probabilidade de sucesso no crime definida para $probabilidade%.")
    @info "Probabilidade de crime definida como $probabilidade% no servidor $id_servidor por $(usuario.user.username)."
end

"""
    handler_comando_rip(contexto)

Handler do comando `/rip`. Remove permanentemente um personagem.
"""
function handler_comando_rip(contexto)
    @info "Comando /rip foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem a ser removido.")
    end

    personagem_nome = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario_invocador = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    id_usuario_dono = nothing
    personagem_encontrado = false
    for (id_dono, personagens_dono) in dados_servidor["personagens"]
        if haskey(personagens_dono, personagem_nome)
            id_usuario_dono = id_dono
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Personagem não encontrado."))
    end

    eh_dono = id_usuario_invocador == id_usuario_dono
    eh_admin = false
    guild_future = get_guild(cliente, contexto.interaction.id_guilda)
    guild = fetch(guild_future).val
    if !isnothing(guild)
        permissoes = Ekztazy.permissions(contexto.interaction.membro, guild)
        eh_admin = has_permission(permissoes, Ekztazy.PERM_ADMINISTRATOR)
    else
        @error "Não foi possível obter informações da Guild $(contexto.interaction.id_guilda) para /rip"
    end

    if !(eh_dono || eh_admin)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "permissao", "Você não tem permissão para remover este personagem."))
    end

    reply(cliente, contexto, content="**ALERTA:** Tem certeza que deseja eliminar permanentemente o personagem **$personagem_nome**? Esta ação não pode ser desfeita. Responda `sim` para confirmar.")

    resposta = aguardar_mensagem(contexto)
    if resposta === nothing || lowercase(strip(resposta)) != "sim"
        return reply(cliente, contexto, content="Eliminação cancelada.")
    end

    delete!(dados_servidor["personagens"][id_usuario_dono], personagem_nome)
    if isempty(dados_servidor["personagens"][id_usuario_dono])
        delete!(dados_servidor["personagens"], id_usuario_dono)
        @info "Usuário $id_usuario_dono não possui mais personagens após remoção de $personagem_nome."
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Personagem '$personagem_nome' foi eliminado com sucesso.")
    @info "Personagem '$personagem_nome' (Dono: $id_usuario_dono) eliminado por $(contexto.interaction.membro.user.username)."
end

"""
    handler_comando_inss(contexto)

Handler do comando `/inss`. Aposenta um personagem, movendo seus dados para uma seção separada.
"""
function handler_comando_inss(contexto)
    @info "Comando /inss foi acionado por $(contexto.interaction.membro.user.username)"
    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem a ser aposentado.")
    end

    personagem_nome = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor)

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem_nome)
        msg_erro = get(get(config, "messages", Dict()), "erros", Dict())
        return reply(cliente, contexto, content=get(msg_erro, "personagem_nao_encontrado", "Você não possui um personagem com este nome."))
    end
    dados_personagem = personagens_usuario[personagem_nome]

    aposentados = get!(dados_servidor, "aposentados", Dict{String, Any}())

    aposentados[personagem_nome] = dados_personagem
    delete!(personagens_usuario, personagem_nome)

    if isempty(personagens_usuario)
        delete!(dados_servidor["personagens"], id_usuario)
    end

    salvar_dados_servidor(id_servidor, dados_servidor)
    reply(cliente, contexto, content="Personagem '$personagem_nome' foi aposentado com sucesso. Seus dados foram arquivados.")
    @info "Personagem '$personagem_nome' (User: $id_usuario) aposentado no servidor $id_servidor."
end

# Fim do código de comandos_discord.jl (sem 'end' de módulo)
