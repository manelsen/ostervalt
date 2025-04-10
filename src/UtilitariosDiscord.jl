# UtilitariosDiscord.jl
# Funções utilitárias específicas do Discord

# Aguarda a resposta do usuário no canal do contexto, com timeout de 30 segundos
function aguardar_mensagem(contexto)
    futuro = wait_for(contexto.cliente, :MessageCreate;
                      check=(event_contexto) -> event_contexto.author.id == contexto.interaction.membro.user.id &&
                                               event_contexto.channel_id == contexto.interaction.channel_id,
                      timeout=30)
    if futuro === nothing
        reply(contexto.cliente, contexto, content="Tempo esgotado para responder.")
        return nothing
    else
        return futuro.message.content
    end
end