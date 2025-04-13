# -*- coding: utf-8 -*-
import discord
from discord.ext import commands

class RPGBot(commands.Bot):
    """
    Classe principal do bot RPG, herda de commands.Bot.

    Responsável por inicializar o bot, sincronizar comandos e tratar eventos.
    """
    # Removido container daqui, será passado em executar_bot.py se necessário
    # O __init__ agora recebe intents explicitamente
    def __init__(self, command_prefix: str, intents: discord.Intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        print("Instância do RPGBot (definicao_bot.py) criada.")

    # Mantendo setup_hook e on_ready aqui por enquanto,
    # mas a lógica principal (carregar cogs, sync) estará em executar_bot.py.
    async def setup_hook(self):
        """
        Método chamado ANTES do bot logar. Cogs e sync são feitos depois em executar_bot.py.
        """
        print("RPGBot setup_hook chamado (definicao_bot.py).")
        # Não fazer sync ou load cogs aqui.

    async def on_ready(self):
        """
        Evento chamado quando o bot está pronto e conectado ao Discord.
        """
        # A lógica principal de on_ready estará em executar_bot.py
        print(f'{self.user} (definicao_bot.py) está online!')