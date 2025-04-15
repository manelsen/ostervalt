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

class InventarioCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        listar_inventario_uc: ListarInventario,
        adicionar_item_uc: AdicionarItemInventario,
        remover_item_uc: RemoverItemInventario,
        listar_personagens_uc: ListarPersonagens,
    ):
        self.bot = bot
        self.listar_inventario_uc = listar_inventario_uc
        self.adicionar_item_uc = adicionar_item_uc
        self.remover_item_uc = remover_item_uc
        self.listar_personagens_uc = listar_personagens_uc
        print("Cog Inventario carregado.")

    # --- Autocomplete ---
    async def autocomplete_active_character(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocompleta apenas com personagens ATIVOS do usuário."""
        if not interaction.guild_id: return []
        user_id = interaction.user.id
        server_id = interaction.guild_id
        try:
            personagens: List[Personagem] = self.listar_personagens_uc.executar(usuario_id=user_id, servidor_id=server_id)
            choices = [
                app_commands.Choice(name=p.nome, value=p.nome)
                for p in personagens
                if p.status == StatusPersonagem.ATIVO and current.lower() in p.nome.lower() # Filtro ATIVO
            ]
            return choices[:25]
        except Exception as e:
            print(f"Erro no autocomplete_active_character (InventarioCog): {e}")
            return []

    # TODO: Implementar autocomplete_item_in_inventory se necessário para /removeritem

    # --- Comandos Slash ---

    @app_commands.command(name="inventario", description="Mostra o inventário de um personagem ativo.")
    @app_commands.describe(character="Nome do personagem ativo") # Adicionado describe
    @app_commands.autocomplete(character=autocomplete_active_character) # Adicionado autocomplete
    async def ver_inventario(self, interaction: discord.Interaction, character: str): # Adicionado parâmetro character
        """Exibe os itens no inventário do personagem."""
        await interaction.response.defer(ephemeral=True)
        try:
            user_id = interaction.user.id
            server_id = interaction.guild_id
            if not server_id:
                 await interaction.followup.send("❌ Este comando só pode ser usado em um servidor.", ephemeral=True)
                 return

            # 1. Encontrar o ID do personagem ativo selecionado
            personagens_usuario: list[Personagem] = self.listar_personagens_uc.executar(
                usuario_id=user_id, servidor_id=server_id
            )
            personagem_selecionado_id: int | None = None
            personagem_selecionado_nome: str | None = None
            for p in personagens_usuario:
                if p.nome.lower() == character.lower() and p.status == StatusPersonagem.ATIVO:
                    personagem_selecionado_id = p.id
                    personagem_selecionado_nome = p.nome
                    break

            if personagem_selecionado_id is None:
                 await interaction.followup.send(f"❌ Personagem ativo '{character}' não encontrado.", ephemeral=True)
                 return

            # 2. Executar caso de uso com personagem_id
            itens_inventario: List[ItemInventario] = self.listar_inventario_uc.executar(personagem_id=personagem_selecionado_id)

            if not itens_inventario:
                await interaction.followup.send(f"🎒 O inventário de {personagem_selecionado_nome} está vazio.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🎒 Inventário de {personagem_selecionado_nome}",
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
                 await interaction.followup.send(f"🎒 O inventário de {personagem_selecionado_nome} está vazio.", ephemeral=True)
                 return

            for item_id, data in itens_agrupados.items():
                 embed.add_field(
                    name=f"{data['nome']} (ID: {item_id})",
                    value=f"Quantidade: {data['quantidade']}\n*'{data['descricao']}'*",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Erro ao listar inventário: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro ao buscar o inventário.", ephemeral=True)

    @app_commands.command(name="additem", description="[Admin] Adiciona um item ao inventário de um personagem.")
    @app_commands.describe(personagem_id="ID do personagem", item_id="ID do item", quantidade="Quantidade a adicionar")
    @app_commands.checks.has_permissions(administrator=True)
    async def adicionar_item(self, interaction: discord.Interaction, personagem_id: int, item_id: int, quantidade: int = 1):
        """Adiciona um item ao inventário (comando administrativo)."""
        await interaction.response.defer(ephemeral=True)
        if quantidade <= 0:
            await interaction.followup.send("❌ A quantidade deve ser positiva.", ephemeral=True)
            return
        try:
            self.adicionar_item_uc.executar(
                personagem_id=personagem_id,
                item_id=item_id,
                quantidade=quantidade
            )
            await interaction.followup.send(f"✅ {quantidade}x Item ID {item_id} adicionado ao inventário do personagem ID {personagem_id}.", ephemeral=True)

        except ValueError as e:
             print(f"Erro de valor ao adicionar item: {e}")
             await interaction.followup.send(f"❌ Erro ao adicionar item: {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao adicionar item: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao adicionar o item.", ephemeral=True)

    # Comando renomeado de remitem para removeritem e ajustado para usar nome do item
    @app_commands.command(name="removeritem", description="Remove uma quantidade de um item do inventário de um personagem ativo.")
    @app_commands.describe(character="Nome do personagem ativo", item_id="ID do item a remover", quantidade="Quantidade a remover")
    @app_commands.autocomplete(character=autocomplete_active_character) # TODO: Adicionar autocomplete para item_id (baseado no inventário do char)
    async def remover_item_inventario(self, interaction: discord.Interaction, character: str, item_id: int, quantidade: int = 1):
        """Remove um item do inventário do personagem ativo."""
        await interaction.response.defer(ephemeral=True)
        if quantidade <= 0:
            await interaction.followup.send("❌ A quantidade deve ser positiva.", ephemeral=True)
            return
        try:
            user_id = interaction.user.id
            server_id = interaction.guild_id
            if not server_id:
                 await interaction.followup.send("❌ Este comando só pode ser usado em um servidor.", ephemeral=True)
                 return

            # 1. Encontrar o ID do personagem ativo selecionado
            personagens_usuario: list[Personagem] = self.listar_personagens_uc.executar(
                usuario_id=user_id, servidor_id=server_id
            )
            personagem_selecionado_id: int | None = None
            for p in personagens_usuario:
                if p.nome.lower() == character.lower() and p.status == StatusPersonagem.ATIVO:
                    personagem_selecionado_id = p.id
                    break

            if personagem_selecionado_id is None:
                 await interaction.followup.send(f"❌ Personagem ativo '{character}' não encontrado.", ephemeral=True)
                 return

            # 2. Executar caso de uso remover_item
            # TODO: A lógica de quantidade precisa ser tratada. O UC atual remove o item inteiro.
            #       Para remover quantidade específica, precisaríamos buscar o item no inventário,
            #       verificar a quantidade e chamar o repo.atualizar_quantidade ou modificar o UC.
            #       Por ora, vamos remover o item inteiro se a quantidade for >= 1.
            if quantidade >= 1:
                self.remover_item_uc.executar(
                    item_id=item_id,
                    personagem_id=personagem_selecionado_id
                )
                await interaction.followup.send(f"✅ Item ID {item_id} removido do inventário de {character}.", ephemeral=True)
            else:
                 await interaction.followup.send(f"ℹ️ Nenhuma ação realizada para quantidade {quantidade}.", ephemeral=True)


        except ValueError as e: # Captura erros como item não encontrado no inventário
            print(f"Erro de valor ao remover item: {e}")
            await interaction.followup.send(f"❌ Erro ao remover item: {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao remover item: {e}")
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