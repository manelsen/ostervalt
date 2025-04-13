import json
# TODO: Importar config corretamente
# from ostervalt.infraestrutura.configuracao.loader import load_config
# config = load_config()
config = {} # Placeholder

def load_server_data(server_id):
    """
    Carrega os dados do servidor a partir de um arquivo JSON.

    Args:
        server_id (str): ID do servidor Discord.

    Returns:
        dict: Dicionário com os dados do servidor.
    """
    try:
        with open(f'server_data_{server_id}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "characters": {},
            "stock_items": {},
            "shop_items": None,
            "special_roles": config.get("cargos_especiais", {"saldo": [], "marcos": []}),
            "messages": config.get("messages", {}),
            "tiers": config.get("tiers", {}),
            "aposentados": {},
            "prices": {},
            "probabilidade_crime": config.get("probabilidades", {}).get("crime", 50)
        }

def save_server_data(server_id, data):
    """
    Salva os dados do servidor em um arquivo JSON.

    Args:
        server_id (str): ID do servidor Discord.
        data (dict): Dados a serem salvos.
    """
    with open(f'server_data_{server_id}.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Dados do servidor {server_id} salvos com sucesso.")

def update_item_price(server_id, item_name, value):
    """
    Atualiza o preço de um item nos dados do servidor.

    Args:
        server_id (str): ID do servidor Discord.
        item_name (str): Nome do item.
        value (str): Valor do item.
    """
    server_data = load_server_data(server_id)
    if "prices" not in server_data:
        server_data["prices"] = {}
    server_data["prices"][item_name] = value
    save_server_data(server_id, server_data)
    print(f"Preço atualizado para {item_name}: {value} moedas")
