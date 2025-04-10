# Arquivo: src/Ostervalt.jl
module Ostervalt

# Inclui os arquivos que definem os módulos. 
# A ordem importa se houver dependências entre eles no carregamento inicial.
# Coloque PersistenciaDados antes de Configuracoes, por exemplo.
include("PersistenciaDados.jl")
include("Configuracoes.jl") 
include("Cache.jl") 
include("GerenciamentoPersonagens.jl")
include("Acoes.jl")
include("Economia.jl")
include("InventarioLoja.jl")
include("LogicaJogo.jl")
include("Permissoes.jl")
include("UtilitariosDiscord.jl")
include("ComandosDiscord.jl")
include("NucleoOstervalt.jl") 

function iniciar()
    println("Iniciando Ostervalt Bot...")
end

# Se quiser iniciar automaticamente ao carregar o módulo:

# iniciar() 

end # module OstervaltBot