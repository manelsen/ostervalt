module ComandosDiscord

using Ekztazy, Dates, Random, Logging # Assumindo dependências básicas, podem precisar de ajuste

# Funções auxiliares (precisarão ser importadas de outros módulos futuramente)
# Exemplo: using ..LogicaJogo: calcular_nivel, formatar_marcos, marcos_para_ganhar
# Exemplo: using ..Persistencia: carregar_dados_servidor, salvar_dados_servidor, atualizar_preco_item
# Exemplo: using ..Utils: verificar_permissoes, obter_tier, aguardar_mensagem, obter_descricao_item
# Exemplo: using ..Personagens: criar_personagem
# Exemplo: using ..Config: config # Ou passar config como argumento

export handler_comando_criar, handler_comando_ajuda, handler_comando_up, handler_comando_marcos,
       handler_comando_mochila, handler_comando_comprar, handler_comando_dinheiro, handler_comando_saldo,
       handler_comando_pix, handler_comando_trabalhar, handler_comando_crime, handler_comando_cargos,
       handler_comando_estoque, handler_comando_loja, handler_comando_inserir, handler_comando_remover,
       limpar_handler_comando_estoque, backhandler_comando_up, handler_comando_mensagens,
       handler_comando_tiers, prob_handler_comando_crime, handler_comando_rip, handler_comando_inss

# === Handlers Extraídos de ostervalt.jl ===

"""
    handler_comando_criar(contexto)

Handler do comando /criar. Cria um novo personagem para o usuário a partir do nome fornecido.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da criação.
"""
function handler_comando_criar(contexto)
    @info "Comando /criar foi acionado"

    opcoes = contexto.interaction.data.opcoes

    if isnothing(opcoes) || isempty(opcoes)
        return reply(cliente, contexto, content="Por favor, forneça um nome para o personagem.") # Assumindo 'cliente' global ou importado
    end

    nome = opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)

    resultado = criar_personagem(id_servidor, id_usuario, nome) # Dependência externa

    reply(cliente, contexto, content=resultado) # Assumindo 'cliente' global ou importado
    @info "Resultado da criação do personagem: $resultado"
end

"""
    handler_comando_ajuda(contexto)

Handler do comando /ajuda. Exibe a mensagem de ajuda com a lista de comandos disponíveis.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a mensagem de ajuda.
"""
function handler_comando_ajuda(contexto)
    @info "Comando /ajuda foi acionado"
    mensagem_ajuda = gerar_mensagem_ajuda() # Dependência externa
    reply(cliente, contexto, content=mensagem_ajuda) # Assumindo 'cliente' global ou importado
    @info "Resposta de ajuda enviada com sucesso"
end

"""
    handler_comando_up(contexto)

Handler do comando /up. Adiciona Marcos ao personagem informado, atualizando o nível se necessário.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação.
"""
function handler_comando_up(contexto)
    @info "Comando /up foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, personagem, "marcos", dados_servidor, false) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config)
    end

    personagem_encontrado = false
    for (id_usuario, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem)
            dados_personagem = personagems[personagem]
            nivel_atual = dados_personagem["nivel"]
            marcos_a_adicionar = marcos_para_ganhar(nivel_atual) # Dependência externa

            dados_personagem["marcos"] += marcos_a_adicionar
            novos_marcos = dados_personagem["marcos"]
            novo_nivel = calcular_nivel(novos_marcos / 16) # Dependência externa

            if novo_nivel > nivel_atual
                dados_personagem["nivel"] = novo_nivel
                reply(cliente, contexto, content="$personagem subiu para o nível $novo_nivel!") # Assumindo 'cliente'
            else
                fracao_adicionada = marcos_a_adicionar == 4 ? "1/4 de Marco" :
                                 marcos_a_adicionar == 2 ? "1/8 de Marco" :
                                 marcos_a_adicionar == 1 ? "1/16 de Marco" :
                                 "$marcos_a_adicionar Marcos"

                reply(cliente, contexto, content="Adicionado $fracao_adicionada para $personagem. Total: $(formatar_marcos(novos_marcos)) (Nível $novo_nivel)") # Dependência externa (formatar_marcos), Assumindo 'cliente'
            end

            salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end
end

"""
    handler_comando_marcos(contexto)

Handler do comando /marcos. Exibe a quantidade de Marcos e o nível do personagem informado.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a quantidade de Marcos e nível.
"""
function handler_comando_marcos(contexto)
    @info "Comando /marcos foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, personagem, "marcos", dados_servidor, false) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    personagem_encontrado = false
    for (id_usuario, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem)
            dados_personagem = personagems[personagem]
            marcos = dados_personagem["marcos"]
            level = calcular_nivel(marcos / 16) # Dependência externa
            reply(cliente, contexto, content="$personagem tem $(formatar_marcos(marcos)) (Nível $level)") # Dependência externa (formatar_marcos), Assumindo 'cliente'
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end
end

"""
    handler_comando_mochila(contexto)

Handler do comando /mochila. Exibe o inventário do personagem informado, ou a descrição de um item específico.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a lista de itens ou descrição detalhada.
"""
function handler_comando_mochila(contexto)
    @info "Comando /mochila foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    item = length(contexto.interaction.data.opcoes) > 1 ? contexto.interaction.data.opcoes[2].value : nothing

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    dados_personagem = get(get(dados_servidor["personagens"], id_usuario, Dict()), personagem, nothing)
    if isnothing(dados_personagem) # Corrigido: personagem_dados -> dados_personagem
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end

    inventory = get(dados_personagem, "inventario", [])
    if isempty(inventory)
        return reply(cliente, contexto, content="O inventário de $personagem está vazio.") # Assumindo 'cliente'
    end

    if !isnothing(item)
        if item in inventory
            contagem_item = count(==(item), inventory)
            descricao_item = obter_descricao_item(dados_servidor, item) # Dependência externa
            reply(cliente, contexto, content="**$item** (x$contagem_item)\nDescrição: $descricao_item") # Assumindo 'cliente'
        else
            reply(cliente, contexto, content="O item '$item' não está na mochila de $personagem.") # Assumindo 'cliente'
        end
    else
        contagem_itens = Dict{String, Int}()
        for i in inventory
            contagem_itens[i] = get(contagem_itens, i, 0) + 1
        end

        items_formatted = join(["**$item** (x$count)" for (item, count) in contagem_itens], ", ")
        reply(cliente, contexto, content="Inventário de $personagem: $items_formatted") # Assumindo 'cliente'
    end
end

"""
    handler_comando_comprar(contexto)

Handler do comando /comprar. Permite que um personagem compre um item da loja, descontando o valor e atualizando o estoque.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da compra.
"""
function handler_comando_comprar(contexto)
    @info "Comando /comprar foi acionado"

    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /comprar <personagem> <item>") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    item = contexto.interaction.data.opcoes[2].value

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end

    if isempty(get(dados_servidor, "itens_estoque", Dict()))
        return reply(cliente, contexto, content="A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.") # Assumindo 'cliente'
    end

    dados_personagem = personagens_usuario[personagem]
    item_found = false
    for (raridade, itens) in dados_servidor["itens_estoque"] # Corrigido: items -> itens
        if item in itens["Name"]
            indice_item = findfirst(==(item), itens["Name"]) # Corrigido: items -> itens
            if itens["Quantity"][indice_item] > 0 # Corrigido: items -> itens
                valor_item = parse(Int, itens["Value"][indice_item]) # Corrigido: items -> itens

                if dados_personagem["dinheiro"] < valor_item
                    return reply(cliente, contexto, content="$personagem não tem dinheiro suficiente para comprar $item. Preço: $valor_item, Dinheiro disponível: $(dados_personagem["dinheiro"])") # Assumindo 'cliente'
                end

                dados_personagem["dinheiro"] -= valor_item
                push!(dados_personagem["inventario"], item)

                itens["Quantity"][indice_item] -= 1 # Corrigido: items -> itens

                reply(cliente, contexto, content="$personagem comprou $item por $valor_item moedas. Dinheiro restante: $(dados_personagem["dinheiro"])") # Assumindo 'cliente'
                salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
                item_found = true
            else
                reply(cliente, contexto, content="Desculpe, $item está fora de estoque.") # Assumindo 'cliente'
                item_found = true
            end
            break
        end
    end

    if !item_found
        reply(cliente, contexto, content="Item '$item' não encontrado na loja.") # Assumindo 'cliente'
    end
end

"""
    handler_comando_dinheiro(contexto)

Handler do comando /dinheiro. Adiciona ou remove dinheiro do saldo de um personagem.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o novo saldo ou mensagem de erro.
"""
function handler_comando_dinheiro(contexto)
    @info "Comando /dinheiro foi acionado"

    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /dinheiro <personagem> <quantidade>") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    quantidade = parse(Int, contexto.interaction.data.opcoes[2].value)

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, personagem, "saldo", dados_servidor, false) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "dinheiro_permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    personagem_encontrado = false
    for (id_usuario, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem)
            dados_personagem = personagems[personagem]
            dados_personagem["dinheiro"] += quantidade # Corrigido: amount -> quantidade

            if quantidade > 0
                reply(cliente, contexto, content="Adicionado $quantidade moedas ao saldo de $personagem. Novo saldo: $(dados_personagem["dinheiro"]) moedas.") # Assumindo 'cliente'
            else
                reply(cliente, contexto, content="Removido $(abs(quantidade)) moedas do saldo de $personagem. Novo saldo: $(dados_personagem["dinheiro"]) moedas.") # Assumindo 'cliente'
            end

            salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end
end

"""
    handler_comando_saldo(contexto)

Handler do comando /saldo. Exibe o saldo de moedas do personagem informado.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o saldo do personagem.
"""
function handler_comando_saldo(contexto)
    @info "Comando /saldo foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    id_usuario = string(contexto.interaction.membro.user.id)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())

    if haskey(personagens_usuario, personagem)
        dados_personagem = personagens_usuario[personagem]
        money = get(dados_personagem, "dinheiro", 0)
        reply(cliente, contexto, content="$personagem tem $money moedas.") # Assumindo 'cliente'
    else
        reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end
end

"""
    handler_comando_pix(contexto)

Handler do comando /pix. Transfere moedas de um personagem para outro, validando saldo e restrições.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da transferência.
"""
function handler_comando_pix(contexto)
    @info "Comando /pix foi acionado"

    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /pix <de_personagem> <para_personagem> <quantidade>") # Assumindo 'cliente'
    end

    personagem_origem = contexto.interaction.data.opcoes[1].value
    personagem_destino = contexto.interaction.data.opcoes[2].value
    quantidade = parse(Int, contexto.interaction.data.opcoes[3].value)

    if quantidade <= 0
        return reply(cliente, contexto, content="A quantidade deve ser maior que zero.") # Assumindo 'cliente'
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    id_usuario = string(contexto.interaction.membro.user.id)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())

    if !haskey(personagens_usuario, personagem_origem)
        return reply(cliente, contexto, content="Você não possui um personagem chamado $personagem_origem.") # Assumindo 'cliente'
    end

    if any(char -> char == personagem_destino, keys(personagens_usuario))
        return reply(cliente, contexto, content="Não é possível transferir moedas para um de seus próprios personagens.") # Assumindo 'cliente'
    end

    destinatario_encontrado = false
    dados_destinatario = nothing
    for (id_usuario_recipient, personagems) in dados_servidor["personagens"]
        if haskey(personagems, personagem_destino) && id_usuario_recipient != id_usuario
            dados_destinatario = personagems[personagem_destino]
            destinatario_encontrado = true
            break
        end
    end

    if !destinatario_encontrado
        return reply(cliente, contexto, content="O personagem destinatário '$personagem_destino' não foi encontrado ou é de sua propriedade.") # Assumindo 'cliente'
    end

    dados_remetente = personagens_usuario[personagem_origem]

    if dados_remetente["dinheiro"] < quantidade # Corrigido: amount -> quantidade
        return reply(cliente, contexto, content="$personagem_origem não tem moedas suficientes. Saldo disponível: $(dados_remetente["dinheiro"])") # Assumindo 'cliente'
    end

    dados_remetente["dinheiro"] -= quantidade # Corrigido: amount -> quantidade
    dados_destinatario["dinheiro"] += quantidade # Corrigido: amount -> quantidade

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa

    reply(cliente, contexto, content="Transferência realizada com sucesso!\n$personagem_origem enviou $quantidade moedas para $personagem_destino.\nNovo saldo de $personagem_origem: $(dados_remetente["dinheiro"]) moedas.") # Assumindo 'cliente'
end

"""
    handler_comando_trabalhar(contexto)

Handler do comando /trabalhar. Permite que o personagem trabalhe para ganhar moedas, respeitando limites de tempo e tiers.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a recompensa do trabalho ou mensagem de erro.
"""
function handler_comando_trabalhar(contexto)
    @info "Comando /trabalhar foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end

    dados_personagem = personagens_usuario[personagem]

    ultimo_trabalho = get(dados_personagem, "ultimo_trabalho", nothing)
    now_time = Dates.now() # Corrigido: now -> now_time para evitar conflito com Dates.now
    intervalo_trabalhar = get(get(config, "limites", Dict()), "intervalo_trabalhar", 86400) # Dependência externa (config)
    if !isnothing(ultimo_trabalho)
        delta = now_time - DateTime(ultimo_trabalho)
        if Dates.value(delta) < intervalo_trabalhar * 1000
            return reply(cliente, contexto, content=get(config["messages"]["erros"], "acao_frequente", "Você já trabalhou recentemente. Aguarde um pouco para trabalhar novamente.")) # Dependência externa (config), Assumindo 'cliente'
        end
    end

    nivel = get(dados_personagem, "nivel", 0)
    nome_tier = obter_tier(nivel, dados_servidor) # Dependência externa
    if isnothing(nome_tier)
        return reply(cliente, contexto, content="Nenhum tier definido para o seu nível. Contate um administrador.") # Assumindo 'cliente'
    end

    tier = dados_servidor["tiers"][nome_tier]
    recompensa = tier["recompensa"]
    dados_personagem["dinheiro"] += recompensa
    dados_personagem["ultimo_trabalho"] = string(now_time)

    mensagens = get(get(dados_servidor, "messages", Dict()), "trabalho", get(config["messages"], "trabalho", [])) # Dependência externa (config)
    mensagem = isempty(mensagens) ? "Você trabalhou duro e ganhou sua recompensa!" : rand(mensagens)

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    reply(cliente, contexto, content="$mensagem\nVocê ganhou $recompensa moedas. Saldo atual: $(dados_personagem["dinheiro"]) moedas.") # Assumindo 'cliente'
end

"""
    handler_comando_crime(contexto)

Handler do comando /crime. Permite que o personagem tente cometer um crime para ganhar ou perder moedas, respeitando limites e probabilidades.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado do crime.
"""
function handler_comando_crime(contexto)
    @info "Comando /crime foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end

    dados_personagem = personagens_usuario[personagem]

    ultimo_crime = get(dados_personagem, "ultimo_crime", nothing)
    now_time = Dates.now() # Corrigido: now -> now_time
    intervalo_crime = get(get(config, "limites", Dict()), "intervalo_crime", 86400) # Dependência externa (config)
    if !isnothing(ultimo_crime)
        delta = now_time - DateTime(ultimo_crime)
        if Dates.value(delta) < intervalo_crime * 1000
            return reply(cliente, contexto, content=get(config["messages"]["erros"], "acao_frequente", "Você já cometeu um crime recentemente. Aguarde um pouco para tentar novamente.")) # Dependência externa (config), Assumindo 'cliente'
        end
    end

    probabilidade = get(dados_servidor, "probabilidade_crime", get(get(config, "probabilidades", Dict()), "crime", 50)) # Dependência externa (config)
    chance = rand(1:100)

    mensagens = get(get(dados_servidor, "messages", Dict()), "crime", get(config["messages"], "crime", [])) # Dependência externa (config)
    mensagem = isempty(mensagens) ? "Você tentou cometer um crime..." : rand(mensagens)

    if chance <= probabilidade
        recompensa = rand(100:500)
        dados_personagem["dinheiro"] += recompensa
        resultado = "Sucesso! Você ganhou $recompensa moedas."
    else
        perda = rand(50:250)
        dados_personagem["dinheiro"] = max(0, dados_personagem["dinheiro"] - perda)
        resultado = "Você foi pego! Perdeu $perda moedas."
    end

    dados_personagem["ultimo_crime"] = string(now_time)

    # Incrementar o atributo oculto 'estrelas'
    dados_personagem["estrelas"] = get(dados_personagem, "estrelas", 0) + 1

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    reply(cliente, contexto, content="$mensagem\n$resultado\nSaldo atual: $(dados_personagem["dinheiro"]) moedas.") # Assumindo 'cliente'
end

"""
    handler_comando_cargos(contexto)

Handler do comando /cargos. Gerencia cargos especiais para permissões de saldo, marcos e loja.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de cargos.
"""
function handler_comando_cargos(contexto)
    @info "Comando /cargos foi acionado"

    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /cargos <tipo> <acao> <cargo>") # Assumindo 'cliente'
    end

    tipo = contexto.interaction.data.opcoes[1].value
    acao = contexto.interaction.data.opcoes[2].value
    nome_cargo = contexto.interaction.data.opcoes[3].value

    usuario = contexto.interaction.membro # Corrigido: user -> usuario
    servidor = contexto.interaction.id_guilda |> (t -> get_guild(cliente, t)) |> fetch |> (u -> u.val) # Assumindo 'cliente'
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val) # Assumindo 'cliente'
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal) # Dependência externa (Ekztazy)

    if !has_permission(permissoes, PERM_ADMINISTRATOR) # Dependência externa (Ekztazy)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !(tipo in ["saldo", "marcos", "loja"])
        return reply(cliente, contexto, content="Tipo inválido. Use 'saldo', 'marcos' ou 'loja'.") # Assumindo 'cliente'
    end

    if !(acao in ["add", "remove"])
        return reply(cliente, contexto, content="Ação inválida. Use 'add' ou 'remove'.") # Assumindo 'cliente'
    end

    cargo = findfirst(r -> lowercase(r.name) == lowercase(nome_cargo), servidor.roles) # Corrigido: guild -> servidor
    if isnothing(cargo)
        return reply(cliente, contexto, content="Cargo não encontrado.") # Assumindo 'cliente'
    end

    if !haskey(dados_servidor["special_roles"], tipo)
        dados_servidor["special_roles"][tipo] = UInt64[]
    end

    if acao == "add"
        if !(cargo.id in dados_servidor["special_roles"][tipo])
            push!(dados_servidor["special_roles"][tipo], cargo.id)
            reply(cliente, contexto, content="Cargo $(cargo.name) adicionado às permissões de $tipo.") # Assumindo 'cliente'
        else
            reply(cliente, contexto, content="Cargo $(cargo.name) já está nas permissões de $tipo.") # Assumindo 'cliente'
        end
    elseif acao == "remove"
        if cargo.id in dados_servidor["special_roles"][tipo]
            filter!(id -> id != cargo.id, dados_servidor["special_roles"][tipo])
            reply(cliente, contexto, content="Cargo $(cargo.name) removido das permissões de $tipo.") # Assumindo 'cliente'
        else
            reply(cliente, contexto, content="Cargo $(cargo.name) não estava nas permissões de $tipo.") # Assumindo 'cliente'
        end
    end

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    @info "Comando cargos concluído. Dados atualizados: $(dados_servidor["special_roles"])"
end

"""
    handler_comando_estoque(contexto)

Handler do comando /estoque. Gerencia o estoque da loja, permitindo abastecimento e definição de preços.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de estoque.
"""
function handler_comando_estoque(contexto)
    @info "Comando /estoque foi acionado"

    if length(contexto.interaction.data.opcoes) < 4
        return reply(cliente, contexto, content="Uso incorreto. Use: /estoque <comum> <incomum> <raro> <muito_raro>") # Assumindo 'cliente'
    end

    comum = contexto.interaction.data.opcoes[1].value
    uncomum = contexto.interaction.data.opcoes[2].value # Corrigido: uncommon -> uncomum
    raro = contexto.interaction.data.opcoes[3].value
    very_raro = contexto.interaction.data.opcoes[4].value

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    dados_servidor["itens_estoque"] = Dict()

    raridades = Dict(
        "common" => comum, # Corrigido: common -> comum
        "uncommon" => uncomum,
        "rare" => raro,
        "very rare" => very_raro
    )

    csv_file = isfile("items_$(id_servidor).csv") ? "items_$(id_servidor).csv" : "items.csv"

    try
        todos_itens = CSV.read(csv_file, DataFrame) # Dependência externa (CSV, DataFrame)
    catch
        return reply(cliente, contexto, content="Erro: O arquivo de itens '$csv_file' não foi encontrado.") # Assumindo 'cliente'
    end

    reply(cliente, contexto, content="Criando novo estoque. Por favor, defina os preços para cada item.") # Assumindo 'cliente'

    for (raridade, count) in raridades
        itens_disponiveis = filter(row -> row.Rarity == raridade, todos_itens)
        contagem_disponivel = nrow(itens_disponiveis) # Dependência externa (DataFrame)

        if contagem_disponivel < count
            count = contagem_disponivel
        end

        if count > 0
            itens = itens_disponiveis[rand(1:nrow(itens_disponiveis), count), :] # Dependência externa (DataFrame)
            dados_servidor["itens_estoque"][raridade] = Dict(
                "Name" => itens.Name, # Corrigido: items -> itens
                "Value" => String[],
                "Quantity" => fill(1, count),
                "Text" => itens.Text # Corrigido: items -> itens
            )

            for name in dados_servidor["itens_estoque"][raridade]["Name"]
                preco_definido = false
                attempts = 0
                while !preco_definido && attempts < 3
                    reply(cliente, contexto, content="Digite o preço para $name (em moedas):") # Assumindo 'cliente'
                    resposta = aguardar_mensagem(contexto) # Dependência externa
                    if resposta === nothing
                        break
                    end
                    try
                        preco = parse(Int, resposta)
                        push!(dados_servidor["itens_estoque"][raridade]["Value"], string(preco)) # Corrigido: price -> preco
                        atualizar_preco_item(id_servidor, name, string(preco)) # Dependência externa, Corrigido: price -> preco
                        reply(cliente, contexto, content="Preço de $name definido como $preco moedas e salvo.") # Assumindo 'cliente', Corrigido: price -> preco
                        preco_definido = true
                    catch
                        reply(cliente, contexto, content="Por favor, digite um número inteiro válido.") # Assumindo 'cliente'
                        attempts += 1
                    end
                end

                if !preco_definido
                    preco_padrao = get(get(config, "precos_padroes", Dict()), "item_padrao", 100) # Dependência externa (config)
                    reply(cliente, contexto, content="Falha ao definir preço para $name. Definindo preço padrão de $preco_padrao moedas.") # Assumindo 'cliente'
                    push!(dados_servidor["itens_estoque"][raridade]["Value"], string(preco_padrao))
                    atualizar_preco_item(id_servidor, name, string(preco_padrao)) # Dependência externa
                end
            end
        end
    end

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa

    summary = "Novo estoque criado com:\n"
    for (raridade, itens) in dados_servidor["itens_estoque"]
        summary *= "- $(length(itens["Name"])) itens $raridade\n"
    end

    reply(cliente, contexto, content=summary) # Assumindo 'cliente'
    reply(cliente, contexto, content="Estoque atualizado com sucesso e valores salvos!") # Assumindo 'cliente'
end

"""
    handler_comando_loja(contexto)

Handler do comando /loja. Exibe os itens disponíveis na loja para o personagem selecionado.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com a lista de itens da loja e saldo do personagem.
"""
function handler_comando_loja(contexto)
    @info "Comando /loja foi acionado"

    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if isempty(get(dados_servidor, "itens_estoque", Dict()))
        return reply(cliente, contexto, content="A loja está vazia. Um administrador precisa usar o comando /estoque para abastecê-la.") # Assumindo 'cliente'
    end

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if isempty(personagens_usuario)
        return reply(cliente, contexto, content="Você não tem nenhum personagem. Crie um personagem primeiro antes de acessar a loja.") # Assumindo 'cliente'
    end

    reply(cliente, contexto, content="Escolha o personagem para ver a loja:") # Assumindo 'cliente'
    for personagem in keys(personagens_usuario)
        reply(cliente, contexto, content=personagem) # Assumindo 'cliente'
    end

    resposta = aguardar_mensagem(contexto) # Dependência externa
    if resposta === nothing
        return
    end
    personagem_selecionado = strip(resposta)

    if !haskey(personagens_usuario, personagem_selecionado)
        return reply(cliente, contexto, content="Personagem inválido selecionado.") # Assumindo 'cliente'
    end

    todos_itens = []
    for (raridade, itens) in dados_servidor["itens_estoque"] # Corrigido: items -> itens
        for (name, valor, quantity, text) in zip(itens["Name"], itens["Value"], itens["Quantity"], itens["Text"]) # Corrigido: items -> itens
            if quantity > 0
                push!(todos_itens, Dict(
                    "Name" => name,
                    "Value" => valor, # Corrigido: value -> valor
                    "Quantity" => quantity,
                    "Text" => text
                ))
            end
        end
    end

    if isempty(todos_itens)
        return reply(cliente, contexto, content="Não há itens disponíveis na loja no momento.") # Assumindo 'cliente'
    end

    for item in todos_itens
        reply(cliente, contexto, content="""
        **$(item["Name"])**
        Preço: $(item["Value"]) moedas
        Quantidade: $(item["Quantity"])
        Descrição: $(item["Text"])
        """) # Assumindo 'cliente'
    end

    reply(cliente, contexto, content="Seu dinheiro: $(personagens_usuario[personagem_selecionado]["dinheiro"]) moedas") # Assumindo 'cliente'
end

"""
    handler_comando_inserir(contexto)

Handler do comando /inserir. Permite inserir um novo item no estoque da loja, definindo raridade, quantidade e valor.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de inserção.
"""
function handler_comando_inserir(contexto)
    @info "Comando /inserir foi acionado"

    if length(contexto.interaction.data.opcoes) < 3
        return reply(cliente, contexto, content="Uso incorreto. Use: /inserir <raridade> <item> <quantidade> [valor]") # Assumindo 'cliente'
    end

    raridade = contexto.interaction.data.opcoes[1].value
    item = contexto.interaction.data.opcoes[2].value
    quantidade = parse(Int, contexto.interaction.data.opcoes[3].value)
    valor = length(contexto.interaction.data.opcoes) >= 4 ? contexto.interaction.data.opcoes[4].value : nothing

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    if !haskey(dados_servidor, "itens_estoque") || isempty(dados_servidor["itens_estoque"])
        dados_servidor["itens_estoque"] = Dict()
    end

    if !haskey(dados_servidor["itens_estoque"], raridade)
        dados_servidor["itens_estoque"][raridade] = Dict(
            "Name" => String[],
            "Value" => String[],
            "Quantity" => Int[],
            "Text" => String[]
        )
    end

    estoque = dados_servidor["itens_estoque"][raridade] # Corrigido: stock -> estoque

    if item in estoque["Name"]
        index = findfirst(==(item), estoque["Name"]) # Corrigido: stock -> estoque
        estoque["Quantity"][index] += quantidade # Corrigido: stock -> estoque
        if !isnothing(valor)
            estoque["Value"][index] = string(valor) # Corrigido: stock -> estoque
            atualizar_preco_item(id_servidor, item, string(valor)) # Dependência externa
        end
    else
        push!(estoque["Name"], item) # Corrigido: stock -> estoque
        push!(estoque["Quantity"], quantidade) # Corrigido: stock -> estoque
        if !isnothing(valor)
            push!(estoque["Value"], string(valor)) # Corrigido: stock -> estoque
            atualizar_preco_item(id_servidor, item, string(valor)) # Dependência externa
        else
            preco = get(get(dados_servidor, "precos", Dict()), item, string(get(get(config, "precos_padroes", Dict()), "item_padrao", 100))) # Dependência externa (config), Corrigido: price -> preco
            push!(estoque["Value"], preco) # Corrigido: stock -> estoque, price -> preco
        end
        push!(estoque["Text"], "Descrição não disponível") # Corrigido: stock -> estoque
    end

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    reply(cliente, contexto, content="Item '$item' inserido no estoque com sucesso.") # Assumindo 'cliente'
end

"""
    handler_comando_remover(contexto)

Handler do comando /remover. Permite remover um item do estoque da loja, parcial ou totalmente.

- `contexto`: Contexto da interação Discord.

Responde ao usuário com o resultado da operação de remoção.
"""
function handler_comando_remover(contexto)
    @info "Comando /remover foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do item a ser removido.") # Assumindo 'cliente'
    end

    item = contexto.interaction.data.opcoes[1].value
    quantidade = length(contexto.interaction.data.opcoes) >= 2 ? parse(Int, contexto.interaction.data.opcoes[2].value) : nothing

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    item_found = false
    for (raridade, stock) in get(dados_servidor, "itens_estoque", Dict())
        if item in stock["Name"] # Corrigido: estoque -> stock
            index = findfirst(==(item), stock["Name"])
            if isnothing(quantidade) || quantidade >= stock["Quantity"][index]
                deleteat!(stock["Name"], index)
                deleteat!(stock["Value"], index)
                deleteat!(stock["Quantity"], index)
                deleteat!(stock["Text"], index)
                reply(cliente, contexto, content="Item '$item' removido completamente do estoque.") # Assumindo 'cliente'
            else
                stock["Quantity"][index] -= quantidade
                reply(cliente, contexto, content="Removido $quantidade de '$item'. Quantidade restante: $(stock["Quantity"][index])") # Assumindo 'cliente'
            end
            item_found = true
            break
        end
    end

    if !item_found
        reply(cliente, contexto, content="Item '$item' não encontrado no estoque.") # Assumindo 'cliente'
    end

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
end

"""
    limpar_handler_comando_estoque(contexto)

Handler do comando /limpar_estoque. Limpa completamente o estoque da loja do servidor.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a limpeza do estoque.
"""
function limpar_handler_comando_estoque(contexto)
    @info "Comando /limpar_estoque foi acionado"

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor) # Dependência externa
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    dados_servidor["itens_estoque"] = Dict()
    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa

    reply(cliente, contexto, content="O estoque foi limpo com sucesso.") # Assumindo 'cliente'
end

""" Handler para o comando /backup (anteriormente backhandler_comando_up) """
function backhandler_comando_up(contexto)
    @info "Comando /backup foi acionado"
    usuario    = contexto.interaction.membro
    servidor   = contexto.interaction.id_guilda   |> (t -> get_guild(cliente, t))   |> fetch |> (u -> u.val) # Assumindo 'cliente'
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val) # Assumindo 'cliente'
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal) # Dependência externa (Ekztazy)
    if !has_permission(permissoes, PERM_ADMINISTRATOR) # Dependência externa (Ekztazy)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    dados_backup = contexto.interaction.id_guilda |> string |> carregar_dados_servidor |> JSON3.write # Dependência externa (carregar_dados_servidor, JSON3)

    if length(dados_backup) <= 2000 # Corrigido: backup_dados -> dados_backup
        reply(cliente, contexto, content="```json\n$dados_backup\n```") # Assumindo 'cliente'
    else
        open("backup_$(contexto.interaction.id_guilda).json", "w") do f
            JSON3.write(f, dados_backup) # Dependência externa (JSON3), Corrigido: backup_dados -> dados_backup
        end
        reply(cliente, contexto, content="O backup é muito grande para ser enviado como mensagem. Um arquivo foi criado no servidor.") # Assumindo 'cliente'
    end
end

"""
    handler_comando_mensagens(contexto)

Handler do comando /mensagens. Permite adicionar mensagens personalizadas para eventos como trabalho e crime.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a adição da mensagem.
"""
function handler_comando_mensagens(contexto)
    @info "Comando /mensagens foi acionado"

    if length(contexto.interaction.data.opcoes) < 2
        return reply(cliente, contexto, content="Uso incorreto. Use: /mensagens <tipo> <mensagem>") # Assumindo 'cliente'
    end

    tipo = contexto.interaction.data.opcoes[1].value
    mensagem = contexto.interaction.data.opcoes[2].value

    usuario    = contexto.interaction.membro
    servidor   = contexto.interaction.id_guilda   |> (t -> get_guild(cliente, t))   |> fetch |> (u -> u.val) # Assumindo 'cliente'
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val) # Assumindo 'cliente'
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal) # Dependência externa (Ekztazy)
    if !has_permission(permissoes, PERM_ADMINISTRATOR) # Dependência externa (Ekztazy)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !haskey(dados_servidor, "messages")
        dados_servidor["messages"] = Dict("trabalho" => String[], "crime" => String[])
    end

    push!(get!(dados_servidor["messages"], tipo, String[]), mensagem)
    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    reply(cliente, contexto, content="Mensagem adicionada ao tipo $tipo com sucesso.") # Assumindo 'cliente'
end

"""
    handler_comando_tiers(contexto)

Handler do comando /tiers. Permite configurar os tiers de níveis, definindo nível mínimo, máximo e recompensa.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a configuração do tier.
"""
function handler_comando_tiers(contexto)
    @info "Comando /tiers foi acionado"

    if length(contexto.interaction.data.opcoes) < 4
        return reply(cliente, contexto, content="Uso incorreto. Use: /tiers <tier> <nivel_min> <nivel_max> <recompensa>") # Assumindo 'cliente'
    end

    tier = contexto.interaction.data.opcoes[1].value
    nivel_min = parse(Int, contexto.interaction.data.opcoes[2].value)
    nivel_max = parse(Int, contexto.interaction.data.opcoes[3].value)
    recompensa = parse(Int, contexto.interaction.data.opcoes[4].value)

    usuario    = contexto.interaction.membro
    servidor   = contexto.interaction.id_guilda   |> (t -> get_guild(cliente, t))   |> fetch |> (u -> u.val) # Assumindo 'cliente'
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val) # Assumindo 'cliente'
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal) # Dependência externa (Ekztazy)
    if !has_permission(permissoes, PERM_ADMINISTRATOR) # Dependência externa (Ekztazy)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !haskey(dados_servidor, "tiers")
        dados_servidor["tiers"] = Dict()
    end

    dados_servidor["tiers"][tier] = Dict(
        "nivel_min" => nivel_min,
        "nivel_max" => nivel_max,
        "recompensa" => recompensa
    )

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    reply(cliente, contexto, content="Tier '$tier' definido para níveis $nivel_min-$nivel_max com recompensa de $recompensa moedas.") # Assumindo 'cliente'
end

"""
    prob_handler_comando_crime(contexto)

Handler do comando /probabilidade_crime. Define a probabilidade de sucesso ao cometer um crime.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a nova probabilidade.
"""
function prob_handler_comando_crime(contexto)
    @info "Comando /probabilidade_crime foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça a probabilidade de sucesso do crime.") # Assumindo 'cliente'
    end

    probabilidade = parse(Int, contexto.interaction.data.opcoes[1].value)

    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    if !verificar_permissoes(contexto.interaction.membro, nothing, "loja", dados_servidor) # Dependência externa (permissão "loja" parece estranha aqui, talvez devesse ser outra?)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    if !(0 <= probabilidade <= 100)
        return reply(cliente, contexto, content="Por favor, insira um valor entre 0 e 100.") # Assumindo 'cliente'
    end

    dados_servidor["probabilidade_crime"] = probabilidade
    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    reply(cliente, contexto, content="Probabilidade de sucesso no crime definida para $probabilidade%.") # Assumindo 'cliente'
end

"""
    handler_comando_rip(contexto)

Handler do comando /rip. Remove permanentemente um personagem, após confirmação.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a eliminação ou cancelamento.
"""
function handler_comando_rip(contexto)
    @info "Comando /rip foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    usuario    = contexto.interaction.membro
    servidor   = contexto.interaction.id_guilda   |> (t -> get_guild(cliente, t))   |> fetch |> (u -> u.val) # Assumindo 'cliente'
    canal = contexto.interaction.channel_id |> (r -> get_channel(cliente, r)) |> fetch |> (s -> s.val) # Assumindo 'cliente'
    permissoes = Ekztazy.permissions_in(usuario, servidor, canal) # Dependência externa (Ekztazy)

    # Permite admin OU dono do personagem (verificado por verificar_permissoes com allow_owner=true)
    if !has_permission(permissoes, PERM_ADMINISTRATOR) && !verificar_permissoes(contexto.interaction.membro, personagem, "view", dados_servidor, true) # Dependência externa (Ekztazy, verificar_permissoes)
         return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para usar este comando.")) # Dependência externa (config), Assumindo 'cliente'
    end

    personagem_encontrado = false
    id_proprietario = ""
    for (id_usuario_loop, personagems) in dados_servidor["personagens"] # Corrigido: id_usuario -> id_usuario_loop para evitar sombreamento
        if haskey(personagems, personagem)
            id_proprietario = id_usuario_loop
            personagem_encontrado = true
            break
        end
    end

    if !personagem_encontrado
        return reply(cliente, contexto, content="Personagem $personagem não encontrado.") # Assumindo 'cliente'
    end

    # Verifica se quem chamou é o proprietário ou admin
    if !(string(contexto.interaction.membro.user.id) == id_proprietario || has_permission(permissoes, PERM_ADMINISTRATOR))
         return reply(cliente, contexto, content=get(config["messages"]["erros"], "permissao", "Você não tem permissão para remover este personagem.")) # Dependência externa (config), Assumindo 'cliente'
    end

    reply(cliente, contexto, content="Tem certeza que deseja eliminar o personagem $personagem? Responda 'sim' para confirmar.") # Assumindo 'cliente'

    resposta = aguardar_mensagem(contexto) # Dependência externa
    if resposta === nothing || lowercase(strip(resposta)) != "sim"
        return reply(cliente, contexto, content="Eliminação cancelada.") # Assumindo 'cliente'
    end

    delete!(dados_servidor["personagens"][id_proprietario], personagem)
    if isempty(dados_servidor["personagens"][id_proprietario])
        delete!(dados_servidor["personagens"], id_proprietario)
    end

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    reply(cliente, contexto, content="Personagem $personagem foi eliminado com sucesso.") # Assumindo 'cliente'
end

"""
    handler_comando_inss(contexto)

Handler do comando /inss. Aposenta um personagem, movendo seus dados para a seção 'aposentados'.

- `contexto`: Contexto da interação Discord.

Responde ao usuário confirmando a aposentadoria do personagem.
"""
function handler_comando_inss(contexto)
    @info "Comando /inss foi acionado"

    if isempty(contexto.interaction.data.opcoes)
        return reply(cliente, contexto, content="Por favor, forneça o nome do personagem.") # Assumindo 'cliente'
    end

    personagem = contexto.interaction.data.opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = carregar_dados_servidor(id_servidor) # Dependência externa

    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if !haskey(personagens_usuario, personagem)
        return reply(cliente, contexto, content=get(config["messages"]["erros"], "personagem_nao_encontrado", "Personagem não encontrado.")) # Dependência externa (config), Assumindo 'cliente'
    end

    if !haskey(dados_servidor, "aposentados")
        dados_servidor["aposentados"] = Dict()
    end

    dados_servidor["aposentados"][personagem] = personagens_usuario[personagem]
    delete!(personagens_usuario, personagem)

    if isempty(personagens_usuario)
        delete!(dados_servidor["personagens"], id_usuario)
    else
        dados_servidor["personagens"][id_usuario] = personagens_usuario
    end

    salvar_dados_servidor(id_servidor, dados_servidor) # Dependência externa
    reply(cliente, contexto, content="Personagem $personagem foi aposentado com sucesso e seus dados foram preservados.") # Assumindo 'cliente'
end

end # fim do module ComandosDiscord
