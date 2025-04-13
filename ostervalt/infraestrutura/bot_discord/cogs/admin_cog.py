# -*- coding: utf-8 -*-
import discord
import os
import json
import polars as pl
import asyncio
import yaml
import datetime # Adicionado para backup filename
from discord.ext import commands
from discord import app_commands, Member, Role

# TODO: Importar corretamente as funções de persistência e config
# from ostervalt.infraestrutura.persistencia.armazenamento_servidor import load_server_data, save_server_data, update_item_price
# from ostervalt.infraestrutura.configuracao.loader import load_config # Supondo que load_config esteja aqui
# config = load_config()

# Placeholder para as funções importadas até que a injeção de dependência seja configurada
# Estas funções precisam ser substituídas pela lógica real ou injeção de dependência
def load_server_data(server_id):
    print(f"[Placeholder] Carregando dados para server_id: {server_id}")
    # Simula a estrutura básica esperada
    return {
            "characters": {},
            "stock_items": {},
            "shop_items": None,
            "special_roles": {"saldo": [], "marcos": []},
            "messages": {"trabalho": [], "crime": []},
            "tiers": {},
            "aposentados": {},
            "prices": {},
            "probabilidade_crime": 50
        }
def save_server_data(server_id, data):
    print(f"[Placeholder] Salvando dados para server_id: {server_id}")
    pass
def update_item_price(server_id, item_name, value):
    print(f"[Placeholder] Atualizando preço para item: {item_name} no server_id: {server_id}")
    pass
# Placeholder para config
config = {
    "messages": {
        "erros": {
            "permissao": "Você não tem permissão para usar este comando."
            }
        },
    "precos_padroes": {
        "item_padrao": 100
        }
    }


class AdminCog(commands.Cog):
    """Cog para comandos administrativos e de configuração."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Cog Admin carregado.")

    # Comandos de prefixo (movidos para Cog)
    @commands.command(name="sync_commands")
    @commands.is_owner()
    async def sync_commands_prefix(self, ctx):
        """Sincroniza os comandos de slash com o Discord."""
        guild = ctx.guild
        if guild:
            self.bot.tree.clear_commands(guild=guild)
            synced = await self.bot.tree.sync(guild=guild)
            await ctx.send(f"Sincronizados {len(synced)} comandos para este servidor.")
        else:
             synced = await self.bot.tree.sync()
             await ctx.send(f"Sincronizados {len(synced)} comandos globais.")


    @commands.command(name="list_commands")
    @commands.is_owner()
    async def list_commands_prefix(self, ctx):
        """Lista todos os comandos disponíveis no servidor."""
        guild = ctx.guild
        if guild:
            guild_commands = await self.bot.tree.fetch_commands(guild=guild)
            await ctx.send(f"Comandos do servidor: {', '.join(cmd.name for cmd in guild_commands)}")
        else:
             global_commands = await self.bot.tree.fetch_commands()
             await ctx.send(f"Comandos globais: {', '.join(cmd.name for cmd in global_commands)}")


    # Comandos de aplicação (slash commands)
    @app_commands.command(name="cargos", description="Define cargos com permissões especiais")
    @app_commands.describe(
        tipo="Tipo de permissão (saldo ou marcos)",
        acao="Adicionar ou remover cargo",
        cargo="Cargo a ser adicionado ou removido"
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Saldo", value="saldo"),
            app_commands.Choice(name="Marcos", value="marcos")
        ],
        acao=[
            app_commands.Choice(name="Adicionar", value="add"),
            app_commands.Choice(name="Remover", value="remove")
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def cargos(self, interaction: discord.Interaction, tipo: str, acao: str, cargo: Role):
        """Gerencia os cargos com permissões especiais."""
        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id) # Usar função importada

        if "special_roles" not in server_data: # Garantir que a chave existe
             server_data["special_roles"] = {"saldo": [], "marcos": []}
        if tipo not in server_data["special_roles"]: # Garantir que o tipo existe
             server_data["special_roles"][tipo] = []

        if acao == "add":
            if cargo.id not in server_data["special_roles"][tipo]:
                server_data["special_roles"][tipo].append(cargo.id)
                await interaction.response.send_message(f"Cargo {cargo.name} adicionado às permissões de {tipo}.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Cargo {cargo.name} já está nas permissões de {tipo}.", ephemeral=True)
        elif acao == "remove":
            if cargo.id in server_data["special_roles"][tipo]:
                server_data["special_roles"][tipo].remove(cargo.id)
                await interaction.response.send_message(f"Cargo {cargo.name} removido das permissões de {tipo}.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Cargo {cargo.name} não estava nas permissões de {tipo}.", ephemeral=True)

        save_server_data(server_id, server_data) # Usar função importada

    @app_commands.command(name="estoque", description="Gera um novo estoque para a loja")
    @app_commands.describe(
        common="Número de itens comuns",
        uncommon="Número de itens incomuns",
        rare="Número de itens raros",
        very_rare="Número de itens muito raros"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def estoque(self, interaction: discord.Interaction, common: int, uncommon: int, rare: int, very_rare: int):
        """Gera um novo estoque de itens para a loja."""
        await interaction.response.defer(ephemeral=True) # Deferir a resposta
        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)
        server_data["stock_items"] = {}

        rarities = {
            'common': common,
            'uncommon': uncommon,
            'rare': rare,
            'very rare': very_rare
        }

        # TODO: Usar repositório de itens em vez de CSV direto
        csv_file = f"items_{server_id}.csv" if os.path.exists(f"items_{server_id}.csv") else "items.csv"

        try:
            all_items = pl.read_csv(csv_file, infer_schema_length=10000, null_values=["undefined"])
        except FileNotFoundError:
            await interaction.followup.send(f"Erro: O arquivo de itens '{csv_file}' não foi encontrado.", ephemeral=True)
            return
        except Exception as e: # Captura outros erros de leitura do Polars/CSV
             await interaction.followup.send(f"Erro ao ler o arquivo de itens '{csv_file}': {e}", ephemeral=True)
             return


        await interaction.followup.send("Criando novo estoque. Por favor, defina os preços para cada item.", ephemeral=True)

        for rarity, count in rarities.items():
            # Filtrar itens da raridade correta
            try:
                available_items = all_items.filter(pl.col("Rarity").str.to_lowercase() == rarity.lower())
            except pl.ColumnNotFoundError:
                 await interaction.followup.send(f"Erro: Coluna 'Rarity' não encontrada no arquivo CSV '{csv_file}'. Verifique o cabeçalho.", ephemeral=True)
                 return
            except Exception as e:
                 await interaction.followup.send(f"Erro ao filtrar itens por raridade '{rarity}': {e}", ephemeral=True)
                 continue # Pula para a próxima raridade

            available_count = len(available_items)

            if available_count == 0:
                 print(f"Nenhum item encontrado para a raridade: {rarity}")
                 continue # Pula se não houver itens dessa raridade

            if available_count < count:
                print(f"Aviso: Solicitados {count} itens {rarity}, mas apenas {available_count} disponíveis.")
                count = available_count

            if count > 0:
                try:
                    items = available_items.sample(count, with_replacement=False, shuffle=True) # Adicionado shuffle
                except Exception as e:
                     await interaction.followup.send(f"Erro ao selecionar amostra de itens {rarity}: {e}", ephemeral=True)
                     continue

                # Verificar se as colunas existem antes de acessá-las
                required_cols = ['Name', 'Text']
                missing_cols = [col for col in required_cols if col not in items.columns]
                if missing_cols:
                     await interaction.followup.send(f"Erro: Colunas ausentes no CSV para raridade {rarity}: {', '.join(missing_cols)}", ephemeral=True)
                     continue


                server_data["stock_items"][rarity] = {
                    'Name': items['Name'].to_list(),
                    'Value': [],
                    'Quantity': [1] * count,
                    'Text': items['Text'].fill_null("Descrição não disponível").to_list() # Tratar nulos
                }

                await interaction.followup.send(f"Definindo preços para itens {rarity}:", ephemeral=True)
                for name in server_data["stock_items"][rarity]['Name']:
                    price_set = False
                    attempts = 0
                    while not price_set and attempts < 3:
                        await interaction.followup.send(f"Digite o preço para {name} (em moedas):", ephemeral=True)
                        try:
                            # Usar self.bot.wait_for
                            price_message = await self.bot.wait_for(
                                'message',
                                check=lambda m: m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit(),
                                timeout=60.0
                            )
                            price = int(price_message.content)
                            if price < 0:
                                 await interaction.followup.send("O preço não pode ser negativo. Tente novamente.", ephemeral=True)
                                 attempts += 1
                                 continue

                            server_data["stock_items"][rarity]['Value'].append(str(price))
                            update_item_price(server_id, name, str(price)) # Usar função importada
                            await interaction.followup.send(f"Preço de {name} definido como {price} moedas e salvo.", ephemeral=True)
                            price_set = True
                        except asyncio.TimeoutError:
                            await interaction.followup.send(f"Tempo esgotado para {name}. Tentativa {attempts + 1} de 3.", ephemeral=True)
                            attempts += 1
                        except Exception as e: # Captura outros erros inesperados
                             await interaction.followup.send(f"Erro inesperado ao processar preço para {name}: {e}", ephemeral=True)
                             attempts += 1 # Considera como tentativa falha


                    if not price_set:
                        preco_padrao = config.get("precos_padroes", {}).get("item_padrao", 100)
                        await interaction.followup.send(f"Falha ao definir preço para {name}. Definindo preço padrão de {preco_padrao} moedas.", ephemeral=True)
                        server_data["stock_items"][rarity]['Value'].append(str(preco_padrao))
                        update_item_price(server_id, name, str(preco_padrao)) # Usar função importada

        save_server_data(server_id, server_data) # Usar função importada

        summary = "Novo estoque criado com:\n"
        for rarity, items_data in server_data.get("stock_items", {}).items():
            item_count = len(items_data.get('Name', []))
            if item_count > 0:
                 summary += f"- {item_count} itens {rarity}\n"

        if not server_data.get("stock_items"):
             summary = "Nenhum item adicionado ao estoque."


        await interaction.followup.send(summary, ephemeral=True)
        await interaction.followup.send("Estoque atualizado com sucesso e valores salvos!", ephemeral=True)

    @app_commands.command(name="inserir", description="Insere um item no estoque da loja")
    @app_commands.describe(
        raridade="Raridade do item",
        item="Nome do item a ser inserido",
        quantidade="Quantidade do item",
        valor="Valor do item (opcional)"
    )
    @app_commands.choices(
        raridade=[
            app_commands.Choice(name="Comum", value="common"),
            app_commands.Choice(name="Incomum", value="uncommon"),
            app_commands.Choice(name="Raro", value="rare"),
            app_commands.Choice(name="Muito Raro", value="very rare")
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def inserir(self, interaction: discord.Interaction, raridade: str, item: str, quantidade: int, valor: int = None):
        """Insere um item no estoque da loja."""
        if quantidade <= 0:
             await interaction.response.send_message("A quantidade deve ser positiva.", ephemeral=True)
             return
        if valor is not None and valor < 0:
             await interaction.response.send_message("O valor não pode ser negativo.", ephemeral=True)
             return

        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        if "stock_items" not in server_data:
            server_data["stock_items"] = {}

        if raridade not in server_data["stock_items"]:
            server_data["stock_items"][raridade] = {
                'Name': [],
                'Value': [],
                'Quantity': [],
                'Text': []
            }

        stock = server_data["stock_items"][raridade]

        try:
            index = stock['Name'].index(item)
            stock['Quantity'][index] += quantidade
            if valor is not None:
                stock['Value'][index] = str(valor)
                update_item_price(server_id, item, str(valor))
        except ValueError: # Item não existe, adiciona novo
            stock['Name'].append(item)
            stock['Quantity'].append(quantidade)
            item_value = str(valor) if valor is not None else server_data.get("prices", {}).get(item, str(config.get("precos_padroes", {}).get("item_padrao", 100)))
            stock['Value'].append(item_value)
            if valor is not None:
                 update_item_price(server_id, item, str(valor))
            # TODO: Buscar descrição real do item se possível
            stock['Text'].append("Descrição não disponível")

        save_server_data(server_id, server_data)
        await interaction.response.send_message(f"Item '{item}' (Quantidade: {quantidade}) inserido/atualizado no estoque com sucesso.", ephemeral=True)

    @app_commands.command(name="remover", description="Remove um item do estoque da loja")
    @app_commands.describe(
        item="Nome do item a ser removido",
        quantidade="Quantidade a ser removida (padrão: todos)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def remover(self, interaction: discord.Interaction, item: str, quantidade: int = None):
        """Remove um item do estoque da loja."""
        if quantidade is not None and quantidade <= 0:
             await interaction.response.send_message("A quantidade a remover deve ser positiva.", ephemeral=True)
             return

        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        item_found = False
        rarity_found = None
        index_found = None

        for rarity, stock in server_data.get("stock_items", {}).items():
            try:
                index = stock['Name'].index(item)
                item_found = True
                rarity_found = rarity
                index_found = index
                break
            except ValueError:
                continue

        if not item_found:
            await interaction.response.send_message(f"Item '{item}' não encontrado no estoque.", ephemeral=True)
            return

        stock_to_update = server_data["stock_items"][rarity_found]
        current_quantity = stock_to_update['Quantity'][index_found]

        if quantidade is None or quantidade >= current_quantity:
            # Remover completamente
            stock_to_update['Name'].pop(index_found)
            stock_to_update['Value'].pop(index_found)
            stock_to_update['Quantity'].pop(index_found)
            stock_to_update['Text'].pop(index_found)
            # Limpar raridade se vazia
            if not stock_to_update['Name']:
                 del server_data["stock_items"][rarity_found]
            await interaction.response.send_message(f"Item '{item}' removido completamente do estoque.", ephemeral=True)
        else:
            # Remover quantidade parcial
            stock_to_update['Quantity'][index_found] -= quantidade
            await interaction.response.send_message(f"Removido {quantidade} de '{item}'. Quantidade restante: {stock_to_update['Quantity'][index_found]}", ephemeral=True)

        save_server_data(server_id, server_data)

    @app_commands.command(name="dinheiro", description="[Admin] Define a quantidade de dinheiro de um personagem")
    @app_commands.describe(
        character="Nome do personagem",
        amount="Quantidade de dinheiro"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def dinheiro(self, interaction: discord.Interaction, character: str, amount: int):
        """Define a quantidade de dinheiro de um personagem."""
        if amount < 0:
             await interaction.response.send_message("A quantidade de dinheiro não pode ser negativa.", ephemeral=True)
             return

        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        character_found = False
        for user_id_str, characters in server_data.get("characters", {}).items():
            if character in characters:
                characters[character]["dinheiro"] = amount
                await interaction.response.send_message(f"Dinheiro de {character} definido como {amount} moedas.", ephemeral=True)
                save_server_data(server_id, server_data)
                character_found = True
                break

        if not character_found:
            await interaction.response.send_message(f"Personagem '{character}' não encontrado.", ephemeral=True)


    @app_commands.command(name="saldo", description="[Admin] Adiciona ou remove dinheiro do saldo de um personagem")
    @app_commands.describe(
        character="Nome do personagem",
        amount="Quantidade de dinheiro (use números negativos para remover)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def saldo(self, interaction: discord.Interaction, character: str, amount: int):
        """Adiciona ou remove dinheiro do saldo de um personagem."""
        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        character_found = False
        for user_id_str, characters in server_data.get("characters", {}).items():
            if character in characters:
                character_data = characters[character]
                # Garantir que dinheiro existe e é int
                if "dinheiro" not in character_data or not isinstance(character_data["dinheiro"], int):
                     character_data["dinheiro"] = 0
                character_data["dinheiro"] += amount
                # Evitar saldo negativo? Depende da regra do jogo.
                # character_data["dinheiro"] = max(0, character_data["dinheiro"])

                novo_saldo = character_data['dinheiro']

                if amount > 0:
                    await interaction.response.send_message(f"Adicionado {amount} moedas ao saldo de {character}. Novo saldo: {novo_saldo} moedas.", ephemeral=True)
                elif amount < 0:
                    await interaction.response.send_message(f"Removido {abs(amount)} moedas do saldo de {character}. Novo saldo: {novo_saldo} moedas.", ephemeral=True)
                else:
                     await interaction.response.send_message(f"Nenhuma alteração no saldo de {character}. Saldo atual: {novo_saldo} moedas.", ephemeral=True)


                save_server_data(server_id, server_data)
                character_found = True
                break

        if not character_found:
            await interaction.response.send_message(f"Personagem '{character}' não encontrado.", ephemeral=True)

    @app_commands.command(name="limpar_estoque", description="[Admin] Limpa o estoque atual da loja")
    @app_commands.checks.has_permissions(administrator=True)
    async def limpar_estoque(self, interaction: discord.Interaction):
        """Limpa o estoque atual da loja."""
        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)
        server_data["stock_items"] = {}
        save_server_data(server_id, server_data)
        await interaction.response.send_message("O estoque foi limpo com sucesso.", ephemeral=True)

    @app_commands.command(name="backup", description="[Admin] Mostra/Envia um backup dos dados do servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(self, interaction: discord.Interaction):
        """Mostra um backup de todos os dados do servidor ou envia como arquivo."""
        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        try:
            backup_data = json.dumps(server_data, indent=2, ensure_ascii=False) # ensure_ascii=False para caracteres especiais
        except Exception as e:
             await interaction.response.send_message(f"Erro ao serializar dados para backup: {e}", ephemeral=True)
             return

        if len(backup_data) <= 1900: # Limite do Discord é 2000, dar margem
            await interaction.response.send_message(f"```json\n{backup_data}\n```", ephemeral=True)
        else:
            try:
                # Salvar em arquivo temporário
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                backup_filename = f"backup_{server_id}_{timestamp}.json"
                with open(backup_filename, "w", encoding='utf-8') as f:
                    f.write(backup_data)

                # Enviar o arquivo
                await interaction.response.send_message("O backup é muito grande para ser enviado como mensagem. Enviando como arquivo...", file=discord.File(backup_filename), ephemeral=True)

                # Limpar o arquivo após envio
                os.remove(backup_filename)
            except Exception as e:
                await interaction.followup.send(f"Erro ao gerar ou enviar arquivo de backup: {e}", ephemeral=True) # Usar followup se a resposta inicial já foi enviada


    @app_commands.command(name="mensagens", description="[Admin] Adiciona uma mensagem para trabalho ou crime")
    @app_commands.describe(
        tipo="Tipo de mensagem (trabalho ou crime)",
        mensagem="A mensagem a ser adicionada"
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Trabalho", value="trabalho"),
            app_commands.Choice(name="Crime", value="crime")
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def mensagens(self, interaction: discord.Interaction, tipo: str, mensagem: str):
        """Adiciona uma mensagem personalizada para trabalho ou crime."""
        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        if "messages" not in server_data:
            server_data["messages"] = {"trabalho": [], "crime": []}
        if tipo not in server_data["messages"]:
             server_data["messages"][tipo] = []

        server_data["messages"][tipo].append(mensagem)
        save_server_data(server_id, server_data)
        await interaction.response.send_message(f"Mensagem adicionada ao tipo {tipo} com sucesso.", ephemeral=True)

    @app_commands.command(name="tiers", description="[Admin] Define faixas de níveis para diferentes tiers")
    @app_commands.describe(
        tier="Nome do tier",
        nivel_min="Nível mínimo",
        nivel_max="Nível máximo",
        recompensa="Recompensa em dinheiro"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def tiers(self, interaction: discord.Interaction, tier: str, nivel_min: int, nivel_max: int, recompensa: int):
        """Define faixas de níveis e recompensas para tiers."""
        if nivel_min <= 0 or nivel_max <= 0 or nivel_min > nivel_max:
             await interaction.response.send_message("Erro: Níveis mínimo e máximo devem ser positivos e mínimo <= máximo.", ephemeral=True)
             return
        if recompensa < 0:
             await interaction.response.send_message("Erro: Recompensa não pode ser negativa.", ephemeral=True)
             return

        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        if "tiers" not in server_data:
            server_data["tiers"] = {}

        # TODO: Validar sobreposição de tiers?

        server_data["tiers"][tier] = {
            "nivel_min": nivel_min,
            "nivel_max": nivel_max,
            "recompensa": recompensa
        }

        save_server_data(server_id, server_data)
        await interaction.response.send_message(f"Tier '{tier}' definido para níveis {nivel_min}-{nivel_max} com recompensa de {recompensa} moedas.", ephemeral=True)

    @app_commands.command(name="probabilidade_crime", description="[Admin] Define a probabilidade de sucesso para o comando /crime")
    @app_commands.describe(probabilidade="Probabilidade de sucesso (0 a 100)")
    @app_commands.checks.has_permissions(administrator=True)
    async def probabilidade_crime(self, interaction: discord.Interaction, probabilidade: int):
        """Define a probabilidade de sucesso para o comando /crime."""
        if not (0 <= probabilidade <= 100):
            await interaction.response.send_message("Por favor, insira um valor entre 0 e 100.", ephemeral=True)
            return

        server_id = str(interaction.guild_id)
        server_data = load_server_data(server_id)

        server_data["probabilidade_crime"] = probabilidade
        save_server_data(server_id, server_data)
        await interaction.response.send_message(f"Probabilidade de sucesso no crime definida para {probabilidade}%.", ephemeral=True)

    # Tratamento de erro específico para comandos de admin neste Cog
    # @AdminCog.error # Decorador de erro para o Cog
    # async def on_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
    #      if isinstance(error, app_commands.MissingPermissions):
    #           await interaction.response.send_message("🚫 Você não tem permissão de administrador para usar este comando.", ephemeral=True)
    #      else:
    #           # Logar o erro para depuração
    #           print(f"Erro inesperado no AdminCog: {error}")
    #           await interaction.response.send_message("❌ Ocorreu um erro inesperado ao executar este comando.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # TODO: Injetar dependências (casos de uso, repositórios) se necessário
    # Exemplo: await bot.add_cog(AdminCog(bot, caso_uso_admin1, repo_config))
    await bot.add_cog(AdminCog(bot))