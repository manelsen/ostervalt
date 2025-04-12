# -*- coding: utf-8 -*-
import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Carrega variáveis de ambiente (como o TOKEN)
load_dotenv()

# Importações da nossa aplicação
from ostervalt.infraestrutura.configuracao.db import criar_tabelas
from ostervalt.infraestrutura.configuracao.container import configurar_container, Container
from ostervalt.infraestrutura.bot_discord.loader import carregar_cogs

# --- Configuração Inicial ---

# 1. Cria as tabelas do banco de dados (se não existirem)
# É seguro chamar isso toda vez, pois o SQLAlchemy verifica a existência.
try:
    criar_tabelas()
except Exception as e:
    print(f"Erro ao criar/verificar tabelas do banco de dados: {e}")
    # Decide se quer parar a execução ou continuar com um aviso
    # exit(1) # Descomente para parar se o DB for essencial

# 2. Configura o container de injeção de dependência
# Isso instancia todos os repositórios e casos de uso.
try:
    container = configurar_container()
except Exception as e:
    print(f"Erro crítico ao configurar o container de dependências: {e}")
    exit(1) # Para a execução se o container falhar

# 3. Define as Intents do Bot
# Ajuste conforme as necessidades do seu bot (e.g., intents.members = True)
intents = discord.Intents.default()
intents.message_content = True # Necessário para alguns comandos de prefixo, mas não para slash
# intents.members = True # Descomente se precisar acessar informações de membros

# --- Classe Principal do Bot ---

class OstervaltBot(commands.Bot):
    """Classe principal do Bot Ostervalt."""

    def __init__(self, container: Container):
        # Prefixo pode ser removido se usar apenas slash commands
        super().__init__(command_prefix="!", intents=intents)
        self.container = container
        print("Instância do OstervaltBot criada.")

    async def setup_hook(self):
        """
        Método executado antes do bot conectar. Ideal para carregar extensões (Cogs)
        e sincronizar comandos de aplicação.
        """
        print("Executando setup_hook...")

        # Carrega todos os Cogs da pasta especificada, injetando dependências do container
        print("Carregando Cogs...")
        try:
            await carregar_cogs(self, self.container)
            print("Cogs carregados.")
        except Exception as e:
            print(f"Erro durante o carregamento dos Cogs: {e}")
            # Considerar se o bot deve iniciar sem Cogs ou parar
            # import traceback
            # traceback.print_exc()

        # Sincroniza os comandos de aplicação (slash commands) com o Discord
        # Isso garante que os comandos definidos nos Cogs apareçam para os usuários.
        print("Sincronizando comandos de aplicação...")
        try:
            # Sincronização global (pode levar até 1 hora para propagar)
            synced = await self.tree.sync()
            # Para sincronizar em um servidor específico instantaneamente (para testes):
            # guild_id = int(os.getenv("TEST_GUILD_ID", 0)) # Pega de .env ou usa 0
            # if guild_id:
            #     guild = discord.Object(id=guild_id)
            #     self.tree.copy_global_to(guild=guild)
            #     synced = await self.tree.sync(guild=guild)
            #     print(f"Sincronizados {len(synced)} comandos para o servidor de teste {guild_id}.")
            # else:
            #     synced = await self.tree.sync() # Fallback para global se não houver ID de teste
            print(f"Sincronizados {len(synced)} comandos de aplicação globalmente.")
        except Exception as e:
            print(f"Erro ao sincronizar comandos: {e}")

    async def on_ready(self):
        """Evento chamado quando o bot está pronto e conectado ao Discord."""
        print("-" * 30)
        print(f'Bot conectado como: {self.user} (ID: {self.user.id})')
        print(f'Servidores conectados: {len(self.guilds)}')
        print(f'Versão do discord.py: {discord.__version__}')
        print("-" * 30)
        print("Ostervalt (run_bot.py) está pronto para a aventura!")

    async def on_error(self, event, *args, **kwargs):
        """Tratamento global de erros em eventos."""
        print(f"Erro não tratado no evento {event}:")
        import traceback
        traceback.print_exc()

    # O tratamento de erros de comando de aplicação pode ser feito
    # dentro de cada Cog ou usando bot.tree.error aqui.
    # Exemplo de handler global para erros de comando slash:
    # async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
    #     if isinstance(error, commands.CommandNotFound):
    #         return # Ignora comandos não encontrados
    #     elif isinstance(error, commands.MissingPermissions):
    #          await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
    #     # Adicione outros tratamentos específicos aqui
    #     else:
    #         print(f"Erro em comando de aplicação: {error}")
    #         await interaction.response.send_message("Ocorreu um erro inesperado.", ephemeral=True)


# --- Inicialização do Bot ---

def main():
    """Função principal para iniciar o bot."""
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        raise ValueError("Nenhum token encontrado. Certifique-se de que você tem um arquivo .env com DISCORD_TOKEN definido.")

    bot = OstervaltBot(container=container)

    try:
        print("Iniciando o bot...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("Erro: Token inválido. Verifique seu arquivo .env")
    except Exception as e:
        print(f"Erro inesperado ao iniciar ou rodar o bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()