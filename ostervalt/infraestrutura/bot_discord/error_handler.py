# -*- coding: utf-8 -*-
import discord
import sys # Para sys.exc_info()
import traceback # Para imprimir traceback completo
from discord.ext import commands
from discord import app_commands

# TODO: Importar config se necessário para mensagens de erro personalizadas
# from ostervalt.infraestrutura.configuracao.loader import load_config
# config = load_config()

# Placeholder para config
config = {
    "messages": {
        "erros": {
            "comando_desconhecido": "Comando não encontrado.",
            "erro_inesperado": "Ocorreu um erro inesperado ao processar seu comando.",
            "permissao_comando_prefixo": "Você não tem permissão para usar este comando de prefixo.",
            "permissao_comando_slash": "Você não tem permissão para usar este comando." # Mensagem genérica para slash
            # Adicionar outras mensagens de erro conforme necessário
        }
    }
}

async def setup_error_handlers(bot: commands.Bot):
    """Configura os handlers de erro globais para o bot."""

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Trata erros globais nos comandos de slash."""
        # Logar o erro completo no console/arquivo de log
        command_name = interaction.command.name if interaction.command else 'desconhecido'
        print(f"Erro no comando de aplicação '{command_name}': {error.__class__.__name__}: {error}")
        # traceback.print_exc() # Descomentar para traceback completo no log

        # Tratar erros específicos de forma mais amigável
        error_message = config["messages"]["erros"]["erro_inesperado"] # Mensagem padrão

        if isinstance(error, app_commands.CommandNotFound):
            # Este erro geralmente não deveria acontecer com slash commands registrados
            error_message = "Comando de slash não encontrado (isso não deveria acontecer!)."
        elif isinstance(error, app_commands.MissingPermissions):
            error_message = config["messages"]["erros"]["permissao_comando_slash"]
        elif isinstance(error, app_commands.BotMissingPermissions):
             error_message = f"Eu não tenho as permissões necessárias para executar este comando: {', '.join(error.missing_permissions)}"
        elif isinstance(error, app_commands.CheckFailure):
            # CheckFailure genérico, pode ser permissão ou outra checagem customizada
             error_message = "Você não atende aos requisitos para usar este comando."
        elif isinstance(error, app_commands.CommandOnCooldown):
             error_message = f"Este comando está em cooldown. Tente novamente em {error.retry_after:.1f} segundos."
        elif isinstance(error, app_commands.NoPrivateMessage):
             error_message = "Este comando não pode ser usado em mensagens privadas."
        elif isinstance(error, app_commands.TransformerError):
             error_message = f"Erro ao converter o argumento '{error.parameter.name}': {error}"
        # Adicionar tratamento para outros erros específicos do app_commands se necessário
        # elif isinstance(error, SuaExcecaoCustomizada):
        #      error_message = "Mensagem específica para SuaExcecaoCustomizada"

        # Enviar resposta ao usuário
        try:
            # Tenta enviar uma resposta inicial se ainda não foi enviada
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ {error_message}", ephemeral=True)
            else:
                # Se a resposta já foi enviada (e.g., via defer), usa followup
                await interaction.followup.send(f"❌ {error_message}", ephemeral=True)
        except discord.HTTPException as http_error:
             print(f"Erro ao enviar mensagem de erro para interação: {http_error}")


    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError):
        """Trata erros globais nos comandos de prefixo."""
        # Logar o erro completo
        command_name = ctx.command.name if ctx.command else 'desconhecido'
        print(f"Erro no comando de prefixo '{command_name}': {error.__class__.__name__}: {error}")
        # traceback.print_exc() # Descomentar para traceback completo no log

        # Ignorar certos erros ou tratar especificamente
        if isinstance(error, commands.CommandNotFound):
            # Opcional: enviar mensagem ou simplesmente ignorar
            # await ctx.send(config["messages"]["erros"]["comando_desconhecido"])
            return
        elif isinstance(error, commands.UserInputError): # Categoria mais ampla para erros de entrada
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"Argumento faltando: `{error.param.name}`. Use `{ctx.prefix}help {ctx.command.qualified_name}` para ajuda.")
            elif isinstance(error, commands.BadArgument):
                await ctx.send(f"Argumento inválido fornecido. Verifique o tipo esperado ou use `{ctx.prefix}help {ctx.command.qualified_name}`.")
            elif isinstance(error, commands.TooManyArguments):
                 await ctx.send(f"Muitos argumentos fornecidos. Use `{ctx.prefix}help {ctx.command.qualified_name}`.")
            else: # Outros UserInputError
                 await ctx.send(f"Erro na sua entrada: {error}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Este comando está em cooldown. Tente novamente em {error.retry_after:.1f} segundos.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(config["messages"]["erros"]["permissao_comando_prefixo"])
        elif isinstance(error, commands.BotMissingPermissions):
             await ctx.send(f"Eu não tenho as permissões necessárias para executar este comando: {', '.join(error.missing_permissions)}")
        elif isinstance(error, commands.NotOwner):
             await ctx.send("Apenas o dono do bot pode usar este comando.")
        elif isinstance(error, commands.CheckFailure):
             # CheckFailure genérico
             await ctx.send("Você não atende aos requisitos para usar este comando.")
        # Adicionar tratamento para outros erros específicos do commands
        else:
            # Erro genérico
            await ctx.send(config["messages"]["erros"]["erro_inesperado"])

    @bot.event
    async def on_error(event_method: str, *args, **kwargs):
        """Trata erros não capturados em eventos específicos (on_message, etc.)."""
        # Logar o erro completo com traceback
        print(f"Erro não capturado no evento '{event_method}':")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        # Opcional: Enviar notificação para um canal de logs/desenvolvedor
        # log_channel_id = SEU_CANAL_DE_LOG_ID
        # ... (código para enviar para canal de log) ...

    print("Handlers de erro globais configurados.")