# InventarioLoja.jl
# Funções para gerenciamento de inventário e loja

# Retorna a descrição de um item do estoque
function obter_descricao_item(dados_servidor::Dict, nome_item::String)
    for (_, raridade_items) in get(dados_servidor, "itens_estoque", Dict())
        if nome_item in get(raridade_items, "Name", [])
            index = findfirst(==(nome_item), raridade_items["Name"])
            return get(raridade_items, "Text", [])[index]
        end
    end
    return "Descrição não disponível."
end

# (Outras funções de inventário e loja podem ser migradas aqui conforme a modularização avança)