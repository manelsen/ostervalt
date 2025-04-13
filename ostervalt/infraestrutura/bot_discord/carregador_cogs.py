# -*- coding: utf-8 -*-
import os
import importlib
from discord.ext import commands

async def carregar_cogs(bot: commands.Bot, container):
    """
    Descobre e carrega dinamicamente todas as extensões (Cogs)
    da pasta 'cogs'.

    Args:
        bot: A instância do bot Discord.
        container: O container de injeção de dependência (ou similar)
                   que contém as instâncias dos casos de uso.
    """
    cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
    print(f"Procurando Cogs em: {cogs_dir}")

    # Mapeamento de Cogs para suas dependências (casos de uso)
    # Isso será usado para injetar as dependências corretas ao adicionar o Cog
    # Os nomes das chaves devem corresponder aos nomes das classes Cog
    # Os valores são tuplas dos nomes dos serviços no container
    dependencias_cogs = {
        'PersonagemCog': (
            'criar_personagem_uc',
            'obter_personagem_uc',
            'listar_personagens_uc',
        ),
        'EconomiaCog': (
            'realizar_trabalho_uc',
            'cometer_crime_uc',
        ),
        'InventarioCog': (
            'listar_inventario_uc',
            'adicionar_item_inventario_uc', # Nome do serviço no container
            'remover_item_inventario_uc',   # Nome do serviço no container
        ),
        'ItemCog': (
            'obter_item_uc',
            'listar_itens_uc',
        ),
        'AdminCog': (), # Sem dependências de UC por enquanto
        'UtilCog': (),  # Sem dependências de UC por enquanto
        # Adicione outros Cogs e suas dependências aqui
    }

    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            module_name = filename[:-3] # Remove '.py'
            module_path = f'ostervalt.infraestrutura.bot_discord.cogs.{module_name}'
            try:
                # Importa o módulo do Cog
                cog_module = importlib.import_module(module_path)
                print(f"Módulo {module_path} importado.")

                # Encontra a classe Cog dentro do módulo (assumindo nome padrão _Cog)
                cog_class_name = None
                for name, obj in cog_module.__dict__.items():
                    if isinstance(obj, type) and issubclass(obj, commands.Cog) and obj is not commands.Cog:
                        cog_class_name = name
                        break

                if cog_class_name:
                    cog_class = getattr(cog_module, cog_class_name)
                    print(f"Classe Cog encontrada: {cog_class_name}")

                    # Obtém as dependências necessárias para este Cog
                    if cog_class_name in dependencias_cogs:
                        nomes_servicos = dependencias_cogs[cog_class_name]
                        # Obtém as instâncias dos casos de uso do container
                        try:
                            casos_de_uso = [container.resolve(nome) for nome in nomes_servicos]
                            # Instancia o Cog com o bot e as dependências injetadas
                            cog_instance = cog_class(bot, *casos_de_uso)
                            # Adiciona o Cog instanciado ao bot
                            await bot.add_cog(cog_instance)
                            print(f"✅ Cog '{cog_class_name}' carregado e adicionado com sucesso.")
                        except Exception as e: # Captura erro na resolução ou instanciação
                             print(f"⚠️ Erro ao resolver/instanciar dependências para {cog_class_name}: {e}")
                             print(f"   Dependências requeridas: {nomes_servicos}")

                    elif cog_class_name in ['AdminCog', 'UtilCog']: # Cogs sem dependências explícitas por enquanto
                         try:
                              cog_instance = cog_class(bot) # Instancia apenas com o bot
                              await bot.add_cog(cog_instance)
                              print(f"✅ Cog '{cog_class_name}' carregado e adicionado com sucesso (sem UCs injetadas).")
                         except Exception as e:
                              print(f"⚠️ Erro ao instanciar {cog_class_name} (sem UCs): {e}")
                    else:
                        print(f"⚠️ Dependências não definidas para o Cog '{cog_class_name}' no loader.py. Pulando.")

                else:
                    print(f"⚠️ Nenhuma classe Cog encontrada em {module_path}.")

            except commands.ExtensionAlreadyLoaded:
                print(f"ℹ️ Extensão '{module_path}' já estava carregada.")
            except commands.ExtensionNotFound:
                print(f"❌ Erro: Extensão '{module_path}' não encontrada.")
            except commands.NoEntryPointError:
                print(f"❌ Erro: Extensão '{module_path}' não possui uma função 'setup'.")
            except ImportError as e:
                print(f"❌ Erro de importação ao carregar '{module_path}': {e}")
            except Exception as e:
                print(f"❌ Erro inesperado ao carregar '{module_path}': {e}")
                import traceback
                traceback.print_exc() # Imprime o traceback completo para depuração

    print("Carregamento de Cogs concluído.")

# Exemplo de como seria chamado (isso iria no ostervalt.py):
# async def main():
#     intents = discord.Intents.default()
#     intents.message_content = True # Ou outras intents necessárias
#     bot = commands.Bot(command_prefix="!", intents=intents)
#
#     # --- Configuração do Container de Injeção de Dependência ---
#     # container = configurar_container() # Função que cria e configura o container
#
#     @bot.event
#     async def on_ready():
#         print(f'Bot conectado como {bot.user}')
#         print("Carregando Cogs...")
#         # await carregar_cogs(bot, container) # Passa o container
#         print("Sincronizando comandos...")
#         try:
#             synced = await bot.tree.sync()
#             print(f"Sincronizados {len(synced)} comandos.")
#         except Exception as e:
#             print(f"Erro ao sincronizar comandos: {e}")
#         print("Bot pronto!")
#
#     # await bot.start('SEU_TOKEN_AQUI')
#
# if __name__ == "__main__":
#     # asyncio.run(main())
    pass