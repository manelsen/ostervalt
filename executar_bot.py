# -*- coding: utf-8 -*-
import os
import discord
import asyncio
import yaml # Import adicionado
import sys # Import adicionado para error handler
import traceback # Import adicionado para error handler
from discord.ext import commands
from dotenv import load_dotenv

# Carrega variáveis de ambiente (como o TOKEN)
load_dotenv()

# Importações da nossa aplicação
from ostervalt.infraestrutura.configuracao.db import criar_tabelas
from ostervalt.infraestrutura.configuracao.container import configurar_container, Container
from ostervalt.infraestrutura.bot_discord.carregador_cogs import carregar_cogs # Import renomeado
from ostervalt.infraestrutura.bot_discord.definicao_bot import RPGBot # Import da classe do bot
from ostervalt.infraestrutura.bot_discord.error_handler import setup_error_handlers # Import do error handler

# --- Configuração Inicial ---

# 0. Carregar Configuração Geral
def load_config():
    """
    Carrega as configurações do arquivo config.yaml.
    Retorna um dicionário vazio se o arquivo não for encontrado.
    """
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            print("Configuração (config.yaml) carregada.")
            return config_data if config_data else {}
    except FileNotFoundError:
        print("Aviso: Arquivo config.yaml não encontrado. Usando configuração padrão/vazia.")
        return {}
    except Exception as e:
        print(f"Erro ao carregar config.yaml: {e}. Usando configuração padrão/vazia.")
        return {}

config = load_config()

# 1. Cria as tabelas do banco de dados (se não existirem)
try:
    criar_tabelas()
    print("Tabelas do banco de dados verificadas/criadas.")
except Exception as e:
    print(f"Erro ao criar/verificar tabelas do banco de dados: {e}")
    # exit(1) # Descomente para parar se o DB for essencial

# 2. Configura o container de injeção de dependência
try:
    container = configurar_container()
    print("Container de injeção de dependência configurado.")
except Exception as e:
    print(f"Erro crítico ao configurar o container de dependências: {e}")
    exit(1) # Para a execução se o container falhar

# 3. Define as Intents do Bot
intents = discord.Intents.default()
intents.message_content = True # Necessário para comandos de prefixo
# intents.members = True # Descomente se precisar acessar informações de membros

# --- Classe Principal do Bot (Adaptada para execução) ---

class BotExecutor(RPGBot): # Herda da definição base
    """Classe que executa o bot, carregando cogs e handlers."""
    def __init__(self, container: Container, intents: discord.Intents):
        # Passa prefixo e intents para a classe base RPGBot
        super().__init__(command_prefix=config.get("prefixo_comando", "!"), intents=intents)
        self.container = container
        print("Instância do BotExecutor criada.")

    async def setup_hook(self):
        """Carrega Cogs, configura handlers e sincroniza comandos."""
        print("Executando setup_hook do BotExecutor...")

        # Carrega Cogs
        print("Carregando Cogs...")
        try:
            # Usa a função importada do carregador_cogs.py
            await carregar_cogs(self, self.container)
            print("Cogs carregados via carregador_cogs.")
        except Exception as e:
            print(f"Erro durante o carregamento dos Cogs: {e}")
            traceback.print_exc()

        # Configura Handlers de Erro
        print("Configurando handlers de erro...")
        try:
            await setup_error_handlers(self) # Chama a função do error_handler.py
            print("Handlers de erro configurados.")
        except Exception as e:
            print(f"Erro ao configurar handlers de erro: {e}")
            traceback.print_exc()

        # Sincroniza comandos de aplicação
        print("Sincronizando comandos de aplicação...")
        try:
            # Sincronização global
            synced = await self.tree.sync()
            print(f"Sincronizados {len(synced)} comandos de aplicação globalmente.")
            # Descomente para sincronizar apenas em guild de teste
            # guild_id = os.getenv("TEST_GUILD_ID")
            # if guild_id:
            #     guild = discord.Object(id=int(guild_id))
            #     self.tree.copy_global_to(guild=guild)
            #     synced_guild = await self.tree.sync(guild=guild)
            #     print(f"Sincronizados {len(synced_guild)} comandos para o servidor de teste {guild_id}.")

        except Exception as e:
            print(f"Erro ao sincronizar comandos: {e}")
            traceback.print_exc()

    async def on_ready(self):
        """Sobrescreve on_ready para mensagem final."""
        print("-" * 30)
        print(f'Bot conectado como: {self.user} (ID: {self.user.id})')
        print(f'Servidores conectados: {len(self.guilds)}')
        print(f'Versão do discord.py: {discord.__version__}')
        print("-" * 30)
        print("Ostervalt (executar_bot.py) está pronto para a aventura!")

    # Tratamento de erro global movido para error_handler.py

# --- Inicialização do Bot ---

def main():
    """Função principal para iniciar o bot."""
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        raise ValueError("Nenhum token encontrado. Certifique-se de que você tem um arquivo .env com DISCORD_TOKEN definido.")

    # Usa a nova classe BotExecutor que herda de RPGBot
    bot = BotExecutor(container=container, intents=intents)

    try:
        print("Iniciando o bot (executar_bot.py)...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("Erro: Token inválido. Verifique seu arquivo .env")
    except Exception as e:
        print(f"Erro inesperado ao iniciar ou rodar o bot: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()