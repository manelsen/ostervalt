# -*- coding: utf-8 -*-
import discord
import asyncio
import datetime
import math # Adicionado para calculate_level
from discord.ext import commands
from discord import app_commands, Member

# TODO: Importar corretamente as funções de persistência, utilitários e config
# from ostervalt.infraestrutura.persistencia.armazenamento_servidor import load_server_data, save_server_data
# from ostervalt.nucleo.utilitarios import calculate_level, format_marcos, marcos_to_gain, check_permissions
# from ostervalt.infraestrutura.configuracao.loader import load_config
# from ostervalt.infraestrutura.bot_discord.autocomplete import autocomplete_character, autocomplete_item, autocomplete_character_for_user # Supondo que autocomplete esteja aqui
# config = load_config()

# Placeholder para as funções importadas até que a injeção de dependência seja configurada
def load_server_data(server_id):
    print(f"[Placeholder] Carregando dados para server_id: {server_id}")
    return {
            "characters": {},
            "stock_items": {},
            "aposentados": {},
            "special_roles": {"saldo": [], "marcos": [], "view": []}, # Adicionado view
            "messages": {"trabalho": [], "crime": []},
            "tiers": {},
            "prices": {},
            "probabilidade_crime": 50
        }
def save_server_data(server_id, data):
    print(f"[Placeholder] Salvando dados para server_id: {server_id}")
    pass
def calculate_level(marcos):
    print(f"[Placeholder] Calculando nível para marcos: {marcos}")
    if not isinstance(marcos, (int, float)) or marcos < 0:
         return 1 # Nível padrão se entrada inválida
    # Lógica simplificada do monolito
    level = min(20, math.floor(marcos / 16) + 1 if isinstance(marcos, float) else math.floor(marcos / 16) + 1) # Ajuste para float
    return level

def format_marcos(marcos_parts):
    print(f"[Placeholder] Formatando marcos: {marcos_parts}")
    if not isinstance(marcos_parts, int) or marcos_parts < 0:
         return "0 Marcos"
    # Lógica simplificada do monolito
    full_marcos = marcos_parts // 16
    remaining_parts = marcos_parts % 16
    level = calculate_level(marcos_parts / 16) # Usa a função calculate_level definida aqui

    if remaining_parts == 0:
        return f"{full_marcos} Marcos"
    elif level <= 4:
        return f"{full_marcos} Marcos" # Nível 1-4 não mostra partes
    elif level <= 12:
        return f"{full_marcos} e {remaining_parts // 4}/4 Marcos"
    elif level <= 16:
        return f"{full_marcos} e {remaining_parts // 2}/8 Marcos"
    else:
        return f"{full_marcos} e {remaining_parts}/16 Marcos"

def marcos_to_gain(level):
    print(f"[Placeholder] Calculando ganho de marcos para nível: {level}")
    # Lógica simplificada do monolito (sem config)
    if level <= 4: return 16
    elif level <= 12: return 4
    elif level <= 16: return 2
    else: return 1

def check_permissions(member: Member, character: str, permission_type: str, server_data, allow_owner=True):
    print(f"[Placeholder] Checando permissão '{permission_type}' para {member.id} no personagem '{character}' (allow_owner={allow_owner})")
    # Lógica simplificada (requer dados reais do servidor)
    user_id = str(member.id)
    is_admin = member.guild_permissions.administrator
    # Simula checagem de cargo especial (precisaria dos IDs reais)
    has_special_role = any(role.id in server_data.get("special_roles", {}).get(permission_type, []) for role in member.roles)
    # Simula checagem de dono (precisaria dos dados reais)
    is_owner = character in server_data.get("characters", {}).get(user_id, {})

    if allow_owner:
        return is_owner or is_admin or has_special_role
    else:
        return is_admin or has_special_role

# Placeholder para config
config = {
    "messages": {
        "erros": {
            "permissao": "Você não tem permissão para usar este comando.",
            "dinheiro_permissao": "Você não tem permissão para gerenciar saldo/marcos.",
            "personagem_nao_encontrado": "Personagem não encontrado."
            }
        }
    }

# Placeholder para funções de autocomplete (serão movidas para autocomplete.py)
async def autocomplete_character(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    print(f"[Placeholder Autocomplete] Buscando personagem: {current}")
    # Lógica simplificada: busca nos dados placeholder
    server_data = load_server_data(str(interaction.guild_id))
    user_chars = server_data.get("characters", {}).get(str(interaction.user.id), {})
    return [
        app_commands.Choice(name=name, value=name)
        for name in user_chars if current.lower() in name.lower()
    ][:25]

async def autocomplete_item(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    print(f"[Placeholder Autocomplete] Buscando item: {current}")
     # Lógica simplificada: busca nos dados placeholder
    server_data = load_server_data(str(interaction.guild_id))
    items = []
    for rarity, data in server_data.get("stock_items", {}).items():
        for name, value, quantity in zip(data.get("Name", []), data.get("Value", []), data.get("Quantity", [])):
             if quantity > 0 and current.lower() in name.lower():
                  items.append(app_commands.Choice(name=f"{name} - {value} moedas", value=name))
    return items[:25]


async def autocomplete_character_for_user(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    print(f"[Placeholder Autocomplete] Buscando personagem para outro usuário: {current}")
    user_option = interaction.namespace.user # Pega o usuário do comando /rip
    if not user_option: return []
    target_user_id = str(user_option.id)
    server_data = load_server_data(str(interaction.guild_id))
    user_chars = server_data.get("characters", {}).get(target_user_id, {})
    return [
        app_commands.Choice(name=name, value=name)
        for name in user_chars if current.lower() in name.lower()
    ][:25]


class UtilCog(commands.Cog):
    """Cog para comandos utilitários gerais do bot."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Cog Util carregado.")

    @app_commands.command(name="carteira", description="Mostra quanto dinheiro um personagem tem")
    @app_commands.describe(character="Nome do personagem")
    @app_commands.autocomplete(character=autocomplete_character)
    async def carteira(self, interaction: discord.Interaction, character: str):
        """Mostra quanto dinheiro um personagem tem."""
        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        # Permite que dono ou quem tem permissão de saldo veja
        # A lógica original permitia ao dono ver, mas aqui vamos permitir a quem tem permissão de saldo também
        if not check_permissions(interaction.user, character, "saldo", server_data, allow_owner=True):
            await interaction.response.send_message(config["messages"]["erros"]["dinheiro_permissao"], ephemeral=True)
            return

        # Procurar o personagem em todos os usuários (se tiver permissão) ou só nos do usuário
        character_found = False
        money = 0
        # Verifica se o usuário tem permissão para ver qualquer carteira (admin ou cargo saldo)
        can_view_any = check_permissions(interaction.user, "", "saldo", server_data, allow_owner=False)

        if can_view_any:
             for user_id_str, characters in server_data.get("characters", {}).items():
                  if character in characters:
                       character_data = characters[character]
                       money = character_data.get("dinheiro", 0)
                       character_found = True
                       break
        else: # Usuário normal, só pode ver a própria carteira
             user_id = str(interaction.user.id)
             user_characters = server_data.get("characters", {}).get(user_id, {})
             if character in user_characters:
                  character_data = user_characters[character]
                  money = character_data.get("dinheiro", 0)
                  character_found = True

        if character_found:
            await interaction.response.send_message(f"{character} tem {money} moedas.", ephemeral=True)
        else:
            await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)

    @app_commands.command(name="listar_comandos", description="Lista todos os comandos de slash disponíveis")
    async def listar_comandos_slash(self, interaction: discord.Interaction):
        """Lista todos os comandos de slash disponíveis."""
        all_commands = self.bot.tree.get_commands(guild=interaction.guild) # Pega comandos do servidor ou globais se não estiver em servidor
        command_names = sorted([cmd.name for cmd in all_commands])

        if command_names:
            # Formata a lista para melhor visualização
            formatted_list = [f"`/{name}`" for name in command_names]
            # Paginação simples se a lista for muito longa
            message_content = f"Comandos disponíveis:\n" + "\n".join(formatted_list)
            if len(message_content) > 1900:
                 parts = []
                 current_part = "Comandos disponíveis:\n"
                 for name in formatted_list:
                      if len(current_part) + len(name) + 1 > 1900:
                           parts.append(current_part)
                           current_part = ""
                      current_part += name + "\n"
                 parts.append(current_part)

                 await interaction.response.send_message(parts[0], ephemeral=True)
                 for part in parts[1:]:
                      await interaction.followup.send(part, ephemeral=True)
            else:
                 await interaction.response.send_message(message_content, ephemeral=True)

        else:
            await interaction.response.send_message("Nenhum comando de slash encontrado.", ephemeral=True)


    @app_commands.command(name="marcos", description="Mostra os Marcos e nível de um personagem")
    @app_commands.describe(character="Nome do personagem")
    @app_commands.autocomplete(character=autocomplete_character)
    async def marcos(self, interaction: discord.Interaction, character: str):
        """Mostra os marcos e nível de um personagem."""
        server_id = str(interaction.guild_id)
        user_id = str(interaction.user.id) # ID do usuário que executou
        server_data = load_server_data(server_id)

        # Permite que o dono ou quem tem permissão de 'marcos' veja
        if not check_permissions(interaction.user, character, "marcos", server_data, allow_owner=True):
            await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
            return

        # Procura o personagem APENAS nos dados do usuário que executou o comando
        user_characters = server_data.get("characters", {}).get(user_id, {})
        if character in user_characters:
            character_data = user_characters[character]
            marcos_val = character_data.get("marcos", 0)
            level = calculate_level(marcos_val / 16.0) # Usar float para divisão
            await interaction.response.send_message(f'{character} tem {format_marcos(marcos_val)} (Nível {level})', ephemeral=True)
        else:
            # Tentar encontrar em outros usuários (se for admin/tiver permissão?)
            can_view_any = check_permissions(interaction.user, "", "marcos", server_data, allow_owner=False)
            found_elsewhere = False
            if can_view_any:
                 for other_user_id, other_characters in server_data.get("characters", {}).items():
                      if other_user_id != user_id and character in other_characters:
                           character_data = other_characters[character]
                           marcos_val = character_data.get("marcos", 0)
                           level = calculate_level(marcos_val / 16.0)
                           await interaction.response.send_message(f'{character} (de outro usuário) tem {format_marcos(marcos_val)} (Nível {level})', ephemeral=True)
                           found_elsewhere = True
                           break
            if not found_elsewhere:
                 await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)


    @app_commands.command(name="up", description="Adiciona Marcos a um personagem ou sobe de nível")
    @app_commands.describe(character="Nome do personagem")
    @app_commands.autocomplete(character=autocomplete_character)
    async def up(self, interaction: discord.Interaction, character: str):
        """Adiciona marcos a um personagem ou sobe de nível."""
        server_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        server_data = load_server_data(server_id)

        # Permite que o dono ou quem tem permissão de 'marcos' use o /up
        if not check_permissions(interaction.user, character, "marcos", server_data, allow_owner=True):
            await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
            return

        user_characters = server_data.get("characters", {}).get(user_id, {})
        if character not in user_characters:
             # Se admin/tem permissão, permitir dar up em outros? Por ora, não.
            await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)
            return

        character_data = user_characters[character]
        current_level = character_data.get("nivel", 1) # Default level 1
        marcos_to_add = marcos_to_gain(current_level) # Usar função importada

        current_marcos = character_data.get("marcos", 0)
        character_data["marcos"] = current_marcos + marcos_to_add
        new_marcos = character_data["marcos"]
        new_level = calculate_level(new_marcos / 16.0) # Usar float

        response_message = ""
        if new_level > current_level:
            character_data["nivel"] = new_level
            response_message = f'{character} subiu para o nível {new_level}!'
        else:
            fraction_added = ""
            if marcos_to_add == 16: fraction_added = "1 Marco completo" # Caso nível 1-4
            elif marcos_to_add == 4: fraction_added = "1/4 de Marco"
            elif marcos_to_add == 2: fraction_added = "1/8 de Marco"
            elif marcos_to_add == 1: fraction_added = "1/16 de Marco"
            else: fraction_added = f"{marcos_to_add} partes de Marco ({marcos_to_add}/16)" # Fallback mais claro

            response_message = f'Adicionado {fraction_added} para {character}. Total: {format_marcos(new_marcos)} (Nível {new_level})' # Usar função importada

        save_server_data(server_id, server_data)
        await interaction.response.send_message(response_message, ephemeral=True)


    @app_commands.command(name="mochila", description="Mostra o inventário de um personagem")
    @app_commands.describe(character="Nome do personagem")
    @app_commands.autocomplete(character=autocomplete_character)
    async def mochila(self, interaction: discord.Interaction, character: str):
        """Mostra o inventário de um personagem."""
        server_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        server_data = load_server_data(server_id)

        # Permite que o dono ou quem tem permissão de 'view' veja
        if not check_permissions(interaction.user, character, "view", server_data, allow_owner=True):
            await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
            return

        user_characters = server_data.get("characters", {}).get(user_id, {})
        if character in user_characters:
             character_data = user_characters[character]
             inventory = character_data.get("inventory", []) # Default para lista vazia
             if inventory:
                  # Usar Embed para melhor formatação
                  embed = discord.Embed(title=f"🎒 Mochila de {character}", color=discord.Color.brown())
                  # Contar itens repetidos
                  item_counts = {}
                  for item_name in inventory:
                       item_counts[item_name] = item_counts.get(item_name, 0) + 1
                  # Adicionar ao embed
                  description = "\n".join([f"- {name} (x{count})" for name, count in item_counts.items()])
                  embed.description = description if description else "Vazio"
                  await interaction.response.send_message(embed=embed, ephemeral=True)
             else:
                  await interaction.response.send_message(f'O inventário de {character} está vazio.', ephemeral=True)
        else:
             # Tentar encontrar em outros usuários (se tiver permissão de view)
             can_view_any = check_permissions(interaction.user, "", "view", server_data, allow_owner=False)
             found_elsewhere = False
             if can_view_any:
                  for other_user_id, other_characters in server_data.get("characters", {}).items():
                       if other_user_id != user_id and character in other_characters:
                            character_data = other_characters[character]
                            inventory = character_data.get("inventory", [])
                            embed = discord.Embed(title=f"🎒 Mochila de {character} (Outro Usuário)", color=discord.Color.light_grey())
                            item_counts = {}
                            for item_name in inventory:
                                 item_counts[item_name] = item_counts.get(item_name, 0) + 1
                            description = "\n".join([f"- {name} (x{count})" for name, count in item_counts.items()])
                            embed.description = description if description else "Vazio"
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                            found_elsewhere = True
                            break
             if not found_elsewhere:
                  await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)


    @app_commands.command(name="comprar", description="Compra um item da loja")
    @app_commands.describe(
        character="Nome do personagem",
        item="Nome do item a ser comprado"
    )
    @app_commands.autocomplete(character=autocomplete_character, item=autocomplete_item)
    async def comprar(self, interaction: discord.Interaction, character: str, item: str):
        """Permite que um personagem compre um item da loja."""
        server_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        server_data = load_server_data(server_id)

        # Permite que o dono compre (não precisa de permissão especial de saldo)
        if not check_permissions(interaction.user, character, "saldo", server_data, allow_owner=True):
             # Esta checagem pode ser redundante se autocomplete_character só mostra os do usuário
             # Mas mantém a segurança caso o autocomplete falhe ou seja burlado.
             await interaction.response.send_message(config["messages"]["erros"]["permissao"], ephemeral=True)
             return

        user_characters = server_data.get("characters", {}).get(user_id, {})
        if character not in user_characters:
            await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)
            return

        if "stock_items" not in server_data or not server_data["stock_items"]:
            await interaction.response.send_message("A loja está vazia.", ephemeral=True)
            return

        character_data = user_characters[character]
        item_found_in_stock = False
        item_value = 0
        item_rarity = None
        item_index = -1

        # Procurar item no estoque
        for rarity, items_data in server_data["stock_items"].items():
            try:
                idx = items_data['Name'].index(item)
                if items_data['Quantity'][idx] > 0:
                    item_found_in_stock = True
                    # Validar se 'Value' existe e é número
                    try:
                         item_value = int(items_data['Value'][idx])
                    except (ValueError, IndexError):
                         print(f"Erro: Valor inválido para o item '{item}' na raridade '{rarity}'.")
                         await interaction.response.send_message(f"Erro interno ao obter o preço do item '{item}'. Contate um administrador.", ephemeral=True)
                         return
                    item_rarity = rarity
                    item_index = idx
                    break
                else:
                     # Encontrou mas está fora de estoque
                     await interaction.response.send_message(f"Desculpe, {item} está fora de estoque.", ephemeral=True)
                     return
            except (ValueError, IndexError):
                continue # Item não encontrado nesta raridade

        if not item_found_in_stock:
            await interaction.response.send_message(f"Item '{item}' não encontrado ou fora de estoque na loja.", ephemeral=True)
            return

        current_money = character_data.get("dinheiro", 0)
        if current_money < item_value:
            await interaction.response.send_message(f"{character} não tem dinheiro suficiente para comprar {item}. Preço: {item_value}, Dinheiro disponível: {current_money}", ephemeral=True)
            return

        # Realizar a compra
        character_data["dinheiro"] = current_money - item_value
        if "inventory" not in character_data:
             character_data["inventory"] = []
        character_data["inventory"].append(item)

        # Atualizar estoque
        server_data["stock_items"][item_rarity]['Quantity'][item_index] -= 1
        # Opcional: remover raridade do estoque se ficar vazia?
        # if all(q == 0 for q in server_data["stock_items"][item_rarity]['Quantity']):
        #     del server_data["stock_items"][item_rarity]

        save_server_data(server_id, server_data)
        await interaction.response.send_message(f"{character} comprou {item} por {item_value} moedas. Dinheiro restante: {character_data['dinheiro']}", ephemeral=True)


    @app_commands.command(name="rip", description="[Admin] Elimina definitivamente um personagem")
    @app_commands.describe(
        user="Usuário dono do personagem",
        character="Nome do personagem a ser eliminado"
    )
    @app_commands.autocomplete(character=autocomplete_character_for_user)
    @app_commands.checks.has_permissions(administrator=True)
    async def rip(self, interaction: discord.Interaction, user: Member, character: str):
        """Elimina definitivamente um personagem de um usuário."""
        server_id = str(interaction.guild_id)
        target_user_id = str(user.id)
        server_data = load_server_data(server_id)

        # Usar .get() para evitar KeyError se 'characters' ou target_user_id não existirem
        user_characters = server_data.get("characters", {}).get(target_user_id, {})
        if character not in user_characters:
            await interaction.response.send_message(f"Personagem '{character}' não encontrado para o usuário {user.display_name}.", ephemeral=True)
            return

        # Confirmação com botões
        view = discord.ui.View(timeout=30.0)
        confirm_button = discord.ui.Button(label="Confirmar Eliminação", style=discord.ButtonStyle.danger, custom_id=f"confirm_rip_{interaction.id}")
        cancel_button = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary, custom_id=f"cancel_rip_{interaction.id}")

        async def confirm_callback(interaction_confirm: discord.Interaction):
            # Verificar se é o usuário original que clicou
            if interaction_confirm.user.id != interaction.user.id:
                 await interaction_confirm.response.send_message("Apenas o autor do comando pode confirmar.", ephemeral=True)
                 return

            # Recarregar dados para operação segura
            current_server_data = load_server_data(server_id)
            current_user_chars = current_server_data.get("characters", {}).get(target_user_id, {})

            if character in current_user_chars:
                 del current_user_chars[character]
                 if not current_user_chars: # Remove usuário se não tiver mais personagens
                      if target_user_id in current_server_data.get("characters", {}):
                           del current_server_data["characters"][target_user_id]
                 # else: # Não precisa reatribuir se modificou o dict in-place
                 #      current_server_data["characters"][target_user_id] = current_user_chars

                 save_server_data(server_id, current_server_data)
                 await interaction_confirm.response.edit_message(content=f"Personagem **{character}** de {user.display_name} foi eliminado com sucesso.", view=None)
            else:
                 await interaction_confirm.response.edit_message(content=f"Personagem **{character}** não encontrado (talvez já tenha sido removido?).", view=None)
            view.stop()

        async def cancel_callback(interaction_cancel: discord.Interaction):
             if interaction_cancel.user.id != interaction.user.id:
                 await interaction_cancel.response.send_message("Apenas o autor do comando pode cancelar.", ephemeral=True)
                 return
             await interaction_cancel.response.edit_message(content="Eliminação cancelada.", view=None)
             view.stop()

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        await interaction.response.send_message(f"Tem certeza que deseja eliminar o personagem **{character}** de {user.display_name}? Esta ação é **irreversível**.", view=view, ephemeral=True)

        timeout = await view.wait()
        # Se timeout, editar a mensagem original para indicar que expirou
        if timeout:
             # Precisamos tentar editar a resposta original
             try:
                  await interaction.edit_original_response(content="Tempo de confirmação esgotado. O personagem não foi eliminado.", view=None)
             except discord.NotFound:
                  print("Não foi possível editar a mensagem original de confirmação RIP (provavelmente já foi editada ou deletada).")
             except discord.HTTPException as e:
                  print(f"Erro ao editar mensagem original de confirmação RIP: {e}")


    @app_commands.command(name="inss", description="Aposenta um personagem, preservando seus dados")
    @app_commands.describe(character="Nome do personagem a aposentar")
    @app_commands.autocomplete(character=autocomplete_character)
    async def inss(self, interaction: discord.Interaction, character: str):
        """Aposenta um personagem, movendo seus dados para 'aposentados'."""
        server_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        server_data = load_server_data(server_id)

        user_characters = server_data.get("characters", {}).get(user_id, {})
        if character not in user_characters:
            await interaction.response.send_message(config["messages"]["erros"]["personagem_nao_encontrado"], ephemeral=True)
            return

        if "aposentados" not in server_data:
            server_data["aposentados"] = {}

        # Mover dados do personagem para aposentados
        character_data_to_retire = user_characters.pop(character) # Remove e retorna o valor
        # Adicionar informações extras
        character_data_to_retire['aposentado_em'] = datetime.datetime.now().isoformat()
        character_data_to_retire['user_id'] = user_id # Guarda o ID do dono original
        server_data["aposentados"][character] = character_data_to_retire


        # Remover entrada do usuário se não tiver mais personagens ativos
        if not user_characters:
            if user_id in server_data.get("characters", {}):
                 del server_data["characters"][user_id]
        # else: # Não precisa reatribuir se modificou o dict in-place
        #     server_data["characters"][user_id] = user_characters

        save_server_data(server_id, server_data)
        await interaction.response.send_message(f"Personagem {character} foi aposentado com sucesso e seus dados foram preservados.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # TODO: Injetar dependências (casos de uso, repositórios) se necessário
    await bot.add_cog(UtilCog(bot))