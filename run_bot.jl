# Ponto de Entrada Principal para o Bot Ostervalt Modularizado
println("Iniciando run_bot.jl...")

# Adiciona o diretório 'src' ao caminho de busca de módulos do Julia
push!(LOAD_PATH, joinpath(@__DIR__, "src"))
println("Diretório 'src' adicionado ao LOAD_PATH.")

try
    # Carrega o módulo principal do bot
    using OstervaltBot
    println("Módulo OstervaltBot carregado com sucesso.")

    # Chama a função principal para iniciar o bot
    println("Chamando OstervaltBot.iniciar_bot()...")
    OstervaltBot.iniciar_bot()
    println("OstervaltBot.iniciar_bot() chamado.")

catch e
    println("\nErro fatal ao carregar ou iniciar OstervaltBot:")
    showerror(stdout, e)
    println()
    Base.show_backtrace(stdout, catch_backtrace())
    println("\nVerifique a definição do módulo em src/OstervaltBot.jl e seus submódulos.")
    exit(1)
end

println("Script run_bot.jl concluído (o bot pode estar rodando em background).")