# Permissoes.jl
# Funções de verificação e gerenciamento de permissões do Ostervalt

# Verifica se o membro possui permissão para executar determinada ação
function verificar_permissoes(membro::Ekztazy.Member, personagem::Union{String, Nothing}, tipo_permissao::String, dados_servidor::Dict, permitir_proprietario::Bool=true)
    id_usuario = string(membro.user.id)
    eh_proprietario = !isnothing(personagem) && haskey(get(dados_servidor["personagens"], id_usuario, Dict()), personagem)
    eh_admin = :administrator in membro.permissoes
    tem_cargo_especial = any(role -> role.id in get(dados_servidor["special_roles"], tipo_permissao, UInt64[]), membro.roles)
    return permitir_proprietario ? (eh_proprietario || eh_admin || tem_cargo_especial) : (eh_admin || tem_cargo_especial)
end