# Lógica de jogo
# Este arquivo é incluído diretamente no módulo OstervaltBot.

using Ekztazy, Dates, Logging
# using .Persistencia: carregar_dados_servidor, salvar_dados_servidor # Removido
# using .Config: config # Removido

# Não precisa de export aqui

# --- Funções Existentes ---

# Nota: A função atualizar_preco_item foi movida para Persistencia.jl

# Calcula o nível de um personagem a partir da quantidade de Marcos
function calcular_nivel(marcos::Float64)
    min(20, floor(Int, marcos) + 1)
end

# Retorna a quantidade de Marcos a ser ganha para o próximo nível
function marcos_para_ganhar(nivel::Int)
    # 'config' está acessível no escopo OstervaltBot
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

    # Chama calcular_nivel diretamente, pois está no mesmo escopo
    nivel = calcular_nivel(partes_marcos / 16.0) # Garante float division

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
    # Acessa dados_servidor diretamente
    personagens_usuario = get(dados_servidor, "personagens", Dict())
    eh_proprietario = !isnothing(personagem) && haskey(get(personagens_usuario, id_usuario, Dict()), personagem)
    # Assume que membro.permissoes e membro.roles estão disponíveis via Ekztazy
    eh_admin = :administrator in membro.permissoes
    roles_especiais = get(dados_servidor, "special_roles", Dict())
    lista_cargos_permissao = get(roles_especiais, tipo_permissao, UInt64[])
    tem_cargo_especial = any(role -> role.id in lista_cargos_permissao, membro.roles)
    return permitir_proprietario ? (eh_proprietario || eh_admin || tem_cargo_especial) : (eh_admin || tem_cargo_especial)
end

# Obtém o nome do tier correspondente ao nível informado
function obter_tier(nivel::Int, dados_servidor::Dict)
    # Acessa dados_servidor diretamente
    tiers = get(dados_servidor, "tiers", Dict())
    for (nome_tier, tier_dados) in tiers
        # Garante que as chaves existem antes de acessá-las
        if haskey(tier_dados, "nivel_min") && haskey(tier_dados, "nivel_max")
            if tier_dados["nivel_min"] <= nivel <= tier_dados["nivel_max"]
                return nome_tier
            end
        else
            @warn "Estrutura inválida para o tier '$nome_tier'. Faltando 'nivel_min' ou 'nivel_max'."
        end
    end
    return nothing
end

# --- Funções Novas Extraídas de ostervalt.jl ---

"""
    obter_descricao_item(dados_servidor::Dict, nome_item::String)

Obtém a descrição de um item a partir dos dados do servidor.

- `dados_servidor`: Dicionário com os dados do servidor.
- `nome_item`: Nome do item a procurar.

Retorna a string da descrição ou "Descrição não disponível.".
"""
function obter_descricao_item(dados_servidor::Dict, nome_item::String)
    itens_estoque = get(dados_servidor, "itens_estoque", Dict())
    for (_, raridade_items) in itens_estoque
        # Verifica se a chave "Name" existe e é um array antes de procurar
        if haskey(raridade_items, "Name") && isa(raridade_items["Name"], AbstractArray) && nome_item in raridade_items["Name"]
            index = findfirst(==(nome_item), raridade_items["Name"])
            # Verifica se a chave "Text" existe e tem o índice correspondente
            if !isnothing(index) && haskey(raridade_items, "Text") && isa(raridade_items["Text"], AbstractArray) && length(raridade_items["Text"]) >= index
                 return raridade_items["Text"][index]
            end
        end
    end
    return "Descrição não disponível."
end

"""
    criar_personagem(id_servidor::String, id_usuario::String, nome::String)

Cria um novo personagem para o usuário, validando limites e duplicidade.

- `id_servidor`: ID do servidor Discord.
- `id_usuario`: ID do usuário Discord.
- `nome`: Nome do personagem a ser criado.

Retorna uma string com o resultado da operação.
"""
function criar_personagem(id_servidor::String, id_usuario::String, nome::String)
    # Chama funções de persistência diretamente, pois estão no mesmo escopo (OstervaltBot)
    dados_servidor = carregar_dados_servidor(id_servidor)

    # 'config' está acessível no escopo OstervaltBot
    limite_personagens = get(get(config, "limites", Dict()), "personagens_por_usuario", 2)
    personagens_usuario = get!(dados_servidor["personagens"], id_usuario, Dict{String, Any}()) # Garante que o usuário exista no dict

    if length(personagens_usuario) >= limite_personagens
        return "Você já possui $limite_personagens personagens. Não é possível criar mais."
    end

    # Verifica se já existe personagem com esse nome para QUALQUER usuário
    for (_, outros_personagens) in dados_servidor["personagens"]
        if haskey(outros_personagens, nome)
             return "Já existe um personagem com o nome '$nome' neste servidor. Por favor, escolha outro nome."
        end
    end

    novo_personagem = Dict(
        "marcos" => 0,
        "inventario" => [],
        "dinheiro" => 0,
        "nivel" => 1,
        "ultimo_trabalho" => nothing,
        "ultimo_crime" => nothing,
        "estrelas" => 0
    )

    personagens_usuario[nome] = novo_personagem

    salvar_dados_servidor(id_servidor, dados_servidor)

    return "Personagem $nome criado com sucesso e vinculado à sua conta Discord! Nível inicial: 1"
end

"""
    gerar_mensagem_ajuda()

Gera a mensagem de ajuda padrão com a lista de comandos.

Retorna uma string formatada.
"""
function gerar_mensagem_ajuda()
    # Esta lista pode vir de 'config' ou ser gerada dinamicamente no futuro
    comandos = [
        ("criar", "Cria um novo personagem."),
        ("up", "Adiciona Marcos (XP) a um personagem (Admin)."),
        ("marcos", "Mostra os Marcos e nível de um personagem (Admin)."),
        ("mochila", "Lista os itens no inventário do seu personagem."),
        ("comprar", "Compra um item da loja."),
        ("dinheiro", "Adiciona/remove dinheiro de um personagem (Admin)."),
        ("saldo", "Mostra o saldo do seu personagem."),
        ("pix", "Transfere moedas entre personagens."),
        ("trabalhar", "Seu personagem trabalha para ganhar dinheiro."),
        ("crime", "Tenta um crime para ganhar/perder dinheiro."),
        ("cargos", "Gerencia cargos com permissões especiais (Admin)."),
        ("estoque", "Reabastece a loja com itens de um CSV (Admin)."),
        ("loja", "Mostra os itens disponíveis na loja."),
        ("inserir", "Insere um item no estoque (Admin)."),
        ("remover", "Remove um item do estoque (Admin)."),
        ("limpar_estoque", "Limpa todo o estoque da loja (Admin)."),
        ("backup", "Cria um backup dos dados do servidor (Admin)."),
        ("mensagens", "Adiciona mensagens personalizadas para eventos (Admin)."),
        ("tiers", "Configura os tiers de nível e recompensa (Admin)."),
        ("probabilidade_crime", "Define a chance de sucesso em crimes (Admin)."),
        ("rip", "Remove permanentemente um personagem (Admin ou Dono)."),
        ("inss", "Aposenta um personagem (Dono)."),
        ("ajuda", "Mostra esta mensagem de ajuda.")
    ]

    mensagem = "**Comandos do Ostervalt Bot:**\n\n"
    for (nome, descricao) in sort(comandos, by = x -> x[1]) # Ordena alfabeticamente
        mensagem *= "`/$(nome)` - $(descricao)\n"
    end
    mensagem *= "\nUse os comandos com responsabilidade!"
    return mensagem
end

"""
    aguardar_mensagem(contexto)

Aguarda a resposta do usuário no canal do contexto, com timeout de 30 segundos.

- `contexto`: Contexto da interação.

Retorna o conteúdo da mensagem respondida ou `nothing` em caso de timeout.
"""
function aguardar_mensagem(contexto)
    # 'cliente' está acessível no escopo OstervaltBot
    futuro = wait_for(cliente, :MessageCreate;
                      check=(event_contexto) -> event_contexto.author.id == contexto.interaction.membro.user.id &&
                                           event_contexto.channel_id == contexto.interaction.channel_id,
                      timeout=30)
    if futuro === nothing
        try
            # 'reply' está acessível no escopo OstervaltBot (vem de Ekztazy)
            reply(cliente, contexto, content="Tempo esgotado para responder.")
        catch e
            @warn "Não foi possível enviar mensagem de timeout: $e"
        end
        return nothing
    else
        return futuro.message.content
    end
end

# Fim do código de logica_jogo.jl (sem 'end' de módulo)