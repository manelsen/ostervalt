from dataclasses import dataclass

@dataclass
class Item:
    """
    Entidade que representa um item disponível na loja ou no inventário.

    Atributos:
        id (int): ID único do item (gerado pelo banco de dados).
        nome (str): Nome do item.
        raridade (str): Raridade do item (comum, incomum, raro, muito raro).
        valor (int): Preço do item em moedas.
        descricao (str): Descrição do item.
    """
    id: int
    nome: str
    raridade: str
    valor: int
    descricao: str

@dataclass
class ItemInventario:
    """
    Entidade que representa um item no inventário de um personagem.

    Atributos:
        id (int): ID único do registro de inventário.
        personagem_id (int): ID do personagem dono do item.
        item_id (int): ID do item.
        quantidade (int): Quantidade possuída.
    """
    id: int
    personagem_id: int
    item_id: int
    quantidade: int