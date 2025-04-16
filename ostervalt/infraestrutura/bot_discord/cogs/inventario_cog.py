import discord
from discord.ext import commands
from discord import app_commands, Member # Adicionado Member
from typing import List
import traceback # Adicionado

# Importar casos de uso e DTOs necessários
from ostervalt.nucleo.casos_de_uso.listar_inventario import ListarInventario
from ostervalt.nucleo.casos_de_uso.adicionar_item_inventario import AdicionarItemInventario
from ostervalt.nucleo.casos_de_uso.remover_item_inventario import RemoverItemInventario
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens # Adicionado
from ostervalt.nucleo.casos_de_uso.dtos import InventarioDTO, PersonagemDTO # Removido ComandoDTO
from ostervalt.nucleo.entidades.item import ItemInventario # Adicionado
from ostervalt.nucleo.entidades.personagem import Personagem # Adicionado
from ostervalt.infraestrutura.persistencia.models import StatusPersonagem # Adicionado
from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy # Import adicionado
from ostervalt.infraestrutura.persistencia.repositorio_itens import RepositorioItensSQLAlchemy # Import adicionado
# Importar utilitários do Cog
from ostervalt.infraestrutura.bot_discord.discord_helpers import (
    obter_contexto_comando,
    buscar_personagem_por_nome,
    autocomplete_active_character as util_autocomplete_active_character, # Importa e renomeia
    autocomplete_item as util_autocomplete_item, # Importa e renomeia
    ComandoForaDeServidorError,
    PersonagemNaoEncontradoError,
    CogUtilsError
)

class InventarioCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        listar_inventario_uc: ListarInventario,
        adicionar_item_uc: AdicionarItemInventario,
        remover_item_uc: RemoverItemInventario,
        listar_personagens_uc: ListarPersonagens,
        repo_personagens: RepositorioPersonagensSQLAlchemy, # Dependência adicionada
        repo_itens: RepositorioItensSQLAlchemy, # Dependência adicionada
    ):
        self.bot = bot
        self.listar_inventario_uc = listar_inventario_uc
        self.adicionar_item_uc = adicionar_item_uc
        self.remover_item_uc = remover_item_uc
        self.listar_personagens_uc = listar_personagens_uc
        self.repo_personagens = repo_personagens # Dependência armazenada
        self.repo_itens = repo_itens # Dependência armazenada
        print("Cog Inventario carregado.")

    # --- Autocomplete ---

    # Usa a função centralizada de discord_helpers, passando o repositório injetado
    async def character_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return await util_autocomplete_active_character(interaction, current, self.repo_personagens)

    # Usa a função centralizada de discord_helpers, passando o repositório injetado
    async def autocomplete_item(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return await util_autocomplete_item(interaction, current, self.repo_itens)

    # TODO: Implementar autocomplete_item_in_inventory se necessário para /removeritem

    # --- Comandos Slash ---

    @app_commands.command(name="inventario", description="Mostra o inventário de um personagem ativo.")
    @app_commands.describe(character="Nome do personagem ativo") # Adicionado describe
    @app_commands.autocomplete(character=character_autocomplete) # Autocomplete ativado
    async def ver_inventario(self, interaction: discord.Interaction, character: str): # Adicionado parâmetro character
        """Exibe os itens no inventário do personagem."""
        await interaction.response.defer(ephemeral=True)
        try:
            # 1. Buscar personagem ativo selecionado
            personagem_selecionado = await buscar_personagem_por_nome(
                interaction, character, self.listar_personagens_uc, apenas_ativos=True
            )

            # 2. Executar caso de uso com personagem_id
            itens_inventario: List[ItemInventario] = self.listar_inventario_uc.executar(personagem_id=personagem_selecionado.id)

            if not itens_inventario:
                await interaction.followup.send(f"🎒 O inventário de {personagem_selecionado.nome} está vazio.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🎒 Inventário de {personagem_selecionado.nome}",
                color=discord.Color.orange()
            )
            # TODO: Buscar nomes/descrições dos itens mestres
            itens_agrupados = {}
            for item in itens_inventario:
                nome_item_placeholder = f"Item ID {item.item_id}"
                descricao_item_placeholder = "Descrição não disponível"
                if item.item_id not in itens_agrupados:
                    itens_agrupados[item.item_id] = {'nome': nome_item_placeholder, 'quantidade': 0, 'descricao': descricao_item_placeholder}
                itens_agrupados[item.item_id]['quantidade'] += item.quantidade

            if not itens_agrupados: # Checagem extra caso a lógica acima falhe
                 await interaction.followup.send(f"🎒 O inventário de {personagem_selecionado.nome} está vazio.", ephemeral=True)
                 return

            for item_id, data in itens_agrupados.items():
                 embed.add_field(
                    name=f"{data['nome']} (ID: {item_id})",
                    value=f"Quantidade: {data['quantidade']}\n*'{data['descricao']}'*",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             await interaction.followup.send(f"❌ {e.mensagem}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao listar inventário para {character}: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro ao buscar o inventário.", ephemeral=True)

    @app_commands.command(name="additem", description="[Admin] Adiciona um item ao inventário de um personagem.")
    @app_commands.describe(personagem_id="ID do personagem", item="Nome do item", quantidade="Quantidade a adicionar")
    @app_commands.autocomplete(item=autocomplete_item) # Autocomplete adicionado
    @app_commands.checks.has_permissions(administrator=True)
    async def adicionar_item(self, interaction: discord.Interaction, personagem_id: int, item: str, quantidade: int = 1):
        """Adiciona um item ao inventário (comando administrativo)."""
        await interaction.response.defer(ephemeral=True)
        if quantidade <= 0:
            await interaction.followup.send("❌ A quantidade deve ser positiva.", ephemeral=True)
            return
        try:
            # 1. Buscar o item mestre pelo nome
            item_mestre = self.repo_itens.obter_por_nome(item)
            if not item_mestre:
                await interaction.followup.send(f"❌ Item mestre '{item}' não encontrado.", ephemeral=True)
                return

            # TODO: Considerar buscar personagem por ID para validar existência antes de adicionar item
            # personagem = self.repo_personagens.obter_por_id(personagem_id)
            # if not personagem:
            #    await interaction.followup.send(f"❌ Personagem com ID {personagem_id} não encontrado.", ephemeral=True)
            #    return

            # 2. Executar caso de uso com ID do item encontrado
            self.adicionar_item_uc.executar(
                personagem_id=personagem_id,
                item_id=item_mestre.id, # Usar ID do item encontrado
                quantidade=quantidade
            )
            await interaction.followup.send(f"✅ {quantidade}x '{item_mestre.nome}' adicionado ao inventário do personagem ID {personagem_id}.", ephemeral=True)

        except ValueError as e:
             print(f"Erro de valor ao adicionar item '{item}': {e}")
             await interaction.followup.send(f"❌ Erro ao adicionar o item '{item}': {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao adicionar item: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao adicionar o item.", ephemeral=True)

    @app_commands.command(name="removeritem", description="Remove uma quantidade de um item do inventário de um personagem ativo.")
    @app_commands.describe(character="Nome do personagem ativo", item="Nome do item a remover", quantidade="Quantidade a remover")
    @app_commands.autocomplete(character=character_autocomplete, item=autocomplete_item) # Autocomplete ativado para ambos
    async def remover_item_inventario(self, interaction: discord.Interaction, character: str, item: str, quantidade: int = 1):
        """Remove um item do inventário do personagem ativo."""
        await interaction.response.defer(ephemeral=True)
        if quantidade <= 0:
            await interaction.followup.send("❌ A quantidade deve ser positiva.", ephemeral=True)
            return
        try:
            # 1. Buscar personagem ativo selecionado
            personagem_selecionado = await buscar_personagem_por_nome(
                interaction, character, self.listar_personagens_uc, apenas_ativos=True
            )

            # 2. Buscar o item mestre pelo nome
            item_mestre = self.repo_itens.obter_por_nome(item)
            if not item_mestre:
                await interaction.followup.send(f"❌ Item mestre '{item}' não encontrado.", ephemeral=True)
                return

            # 3. Executar caso de uso remover_item com ID do item encontrado
            # TODO: A lógica de quantidade precisa ser tratada. O UC atual remove o item inteiro.
            #       Para remover quantidade específica, precisaríamos buscar o item no inventário,
            #       verificar a quantidade e chamar o repo.atualizar_quantidade ou modificar o UC.
            #       Por ora, vamos remover o item inteiro se a quantidade for >= 1.
            if quantidade >= 1:
                self.remover_item_uc.executar(
                    item_id=item_mestre.id, # Usar ID do item encontrado
                    personagem_id=personagem_selecionado.id # Usar ID do personagem encontrado
                )
                await interaction.followup.send(f"✅ Item '{item_mestre.nome}' removido do inventário de {personagem_selecionado.nome}.", ephemeral=True)
            else:
                 await interaction.followup.send(f"ℹ️ Nenhuma ação realizada para quantidade {quantidade}.", ephemeral=True)


        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             await interaction.followup.send(f"❌ {e.mensagem}", ephemeral=True)
        except ValueError as e: # Captura erros específicos do UC remover_item (ex: item não existe no inventário)
            print(f"Erro de valor ao remover item '{item}': {e}")
            await interaction.followup.send(f"❌ Erro ao remover o item '{item}': {e}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao remover item {item_id} de {character}: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao remover o item.", ephemeral=True)

    @adicionar_item.error
    async def additem_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            if interaction.response.is_done():
                 await interaction.followup.send("🚫 Você não tem permissão para usar este comando.", ephemeral=True)
            else:
                 await interaction.response.send_message("🚫 Você não tem permissão para usar este comando.", ephemeral=True)
        else:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ Erro inesperado no comando additem: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Erro inesperado no comando additem: {error}", ephemeral=True)
            print(f"Erro não tratado em additem: {error}")


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # A injeção é feita pelo carregador_cogs.py
    pass