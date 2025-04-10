module ComandosDiscord
export registrar_comandos, handler_comando_saldo, handler_comando_dinheiro

using ..GerenciamentoPersonagens, ..Acoes, ..Economia, ..Configuracoes, ..InventarioLoja, ..LogicaJogo, ..Permissoes, ..PersistenciaDados, ..Cache, ..UtilitariosDiscord

# Handler para /saldo totalmente integrado
function handler_comando_saldo(contexto)
    opcoes = contexto.interaction.data.opcoes
    if isempty(opcoes)
        return reply(contexto.cliente, contexto, content="Por favor, forneça o nome do personagem.")
    end
    personagem = opcoes[1].value
    id_servidor = string(contexto.interaction.id_guilda)
    id_usuario = string(contexto.interaction.membro.user.id)
    dados_servidor = PersistenciaDados.carregar_dados_servidor(id_servidor)
    personagens_usuario = get(dados_servidor["personagens"], id_usuario, Dict())
    if haskey(personagens_usuario, personagem)
        dados_personagem = personagens_usuario[personagem]
        dinheiro = get(dados_personagem, "dinheiro", 0)
        return reply(contexto.cliente, contexto, content="$personagem tem $dinheiro moedas.")
    else
        return reply(contexto.cliente, contexto, content="Personagem não encontrado.")
    end
end

# Outros handlers...

# Registro de comandos Discord
function registrar_comandos(cliente)
    comandos = [
        # Comando /saldo
        Dict("name" => "saldo", "description" => "Verifica o saldo de um personagem", "options" => [
            Dict("name" => "personagem", "description" => "Nome do personagem", "type" => 3, "required" => true)
        ]),
        # Comando /dinheiro
        Dict("name" => "dinheiro", "description" => "Adiciona ou remove dinheiro de um personagem", "options" => [
            Dict("name" => "personagem", "description" => "Nome do personagem", "type" => 3, "required" => true),
            Dict("name" => "quantidade", "description" => "Quantidade de dinheiro", "type" => 4, "required" => true)
        ]),
        # Outros comandos...
    ]
    Ekztazy.bulk_override_guild_application_commands(cliente, UInt64(GUILD), comandos)
end

end # do módulo