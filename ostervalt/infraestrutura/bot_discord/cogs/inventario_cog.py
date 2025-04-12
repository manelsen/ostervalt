import discord
from discord.ext import commands
from discord import app_commands

class InventarioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="inventario", description="Visualiza seu inventário")
    async def inventario(self, interaction: discord.Interaction):
        await interaction.response.send_message("Visualizando inventário...")

    @app_commands.command(name="additem", description="Adiciona um item ao inventário (comando de teste)")
    async def adicionar_item(self, interaction: discord.Interaction, item_nome: str):
        await interaction.response.send_message(f"Adicionando item {item_nome} ao inventário...")

    @app_commands.command(name="remitem", description="Remove um item do inventário (comando de teste)")
    async def remover_item(self, interaction: discord.Interaction, item_nome: str):
        await interaction.response.send_message(f"Removendo item {item_nome} do inventário...")

async def setup(bot):
    await bot.add_cog(InventarioCog(bot))
    # --- Comandos Slash ---

    @app_commands.command(name="inventario", description="Mostra o inventário do seu personagem ativo.")
    async def ver_inventario(self, interaction: discord.Interaction):
        """Exibe os itens no inventário do personagem."""
        await interaction.response.defer(ephemeral=True)
        try:
            # TODO: Precisará do ID do personagem ativo
            comando_dto = ComandoDTO(discord_id=interaction.user.id)
            resultado_dto: InventarioDTO = self.listar_inventario_uc.executar(comando_dto)

            if not resultado_dto.itens:
                await interaction.followup.send("🎒 Seu inventário está vazio.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🎒 Inventário de {resultado_dto.nome_personagem}",
                color=discord.Color.orange()
            )
            # Agrupa itens para melhor visualização
            itens_agrupados = {}
            for item in resultado_dto.itens:
                if item.item_id not in itens_agrupados:
                    itens_agrupados[item.item_id] = {'nome': item.nome_item, 'quantidade': 0, 'descricao': item.descricao_item}
                itens_agrupados[item.item_id]['quantidade'] += item.quantidade

            for item_id, data in itens_agrupados.items():
                 embed.add_field(
                    name=f"{data['nome']} (ID: {item_id})",
                    value=f"Quantidade: {data['quantidade']}\n*'{data['descricao']}'*",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            # TODO: Tratar exceções específicas (e.g., personagem não encontrado)
            print(f"Erro ao listar inventário: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro ao buscar seu inventário: {e}", ephemeral=True)

    @app_commands.command(name="additem", description="[Admin] Adiciona um item ao inventário de um personagem.")
    @app_commands.describe(personagem_id="ID do personagem", item_id="ID do item", quantidade="Quantidade a adicionar")
    @app_commands.checks.has_permissions(administrator=True) # Restringe a administradores
    async def adicionar_item(self, interaction: discord.Interaction, personagem_id: int, item_id: int, quantidade: int = 1):
        """Adiciona um item ao inventário (comando administrativo)."""
        await interaction.response.defer(ephemeral=True)
        if quantidade <= 0:
            await interaction.followup.send("❌ A quantidade deve ser positiva.", ephemeral=True)
            return
        try:
            # Este caso de uso pode precisar ser adaptado ou um novo criado,
            # pois o original pode não receber discord_id ou personagem_id diretamente assim.
            # Assumindo que o ComandoDTO pode carregar 'personagem_id' e 'item_id'
            comando_dto = ComandoDTO(
                discord_id=interaction.user.id, # ID do admin que executou
                parametros={
                    'personagem_id': personagem_id,
                    'item_id': item_id,
                    'quantidade': quantidade
                }
            )
            # O DTO de resultado pode variar, usando um genérico por enquanto
            self.adicionar_item_uc.executar(comando_dto)

            await interaction.followup.send(f"✅ {quantidade}x Item ID {item_id} adicionado ao inventário do personagem ID {personagem_id}.", ephemeral=True)

        except Exception as e:
            # TODO: Tratar exceções (ItemNaoEncontrado, PersonagemNaoEncontrado)
            print(f"Erro ao adicionar item: {e}")
            await interaction.followup.send(f"❌ Erro ao adicionar item: {e}", ephemeral=True)

    @app_commands.command(name="remitem", description="Remove uma quantidade de um item do seu inventário.")
    @app_commands.describe(item_id="ID do item a remover", quantidade="Quantidade a remover")
    async def remover_item(self, interaction: discord.Interaction, item_id: int, quantidade: int = 1):
        """Remove um item do inventário do personagem ativo."""
        await interaction.response.defer(ephemeral=True)
        if quantidade <= 0:
            await interaction.followup.send("❌ A quantidade deve ser positiva.", ephemeral=True)
            return
        try:
            # TODO: Precisará do ID do personagem ativo
            comando_dto = ComandoDTO(
                discord_id=interaction.user.id,
                parametros={
                    # 'personagem_id': id_personagem_ativo, # Necessário obter
                    'item_id': item_id,
                    'quantidade': quantidade
                }
            )
            # O DTO de resultado pode variar
            self.remover_item_uc.executar(comando_dto)

            await interaction.followup.send(f"✅ {quantidade}x Item ID {item_id} removido do seu inventário.", ephemeral=True)

        except Exception as e:
            # TODO: Tratar exceções (ItemNaoEncontradoNoInventario, QuantidadeInsuficiente)
            print(f"Erro ao remover item: {e}")
            await interaction.followup.send(f"❌ Erro ao remover item: {e}", ephemeral=True)

    @adicionar_item.error
    async def additem_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("🚫 Você não tem permissão para usar este comando.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Erro inesperado no comando additem: {error}", ephemeral=True)
            print(f"Erro não tratado em additem: {error}")


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # TODO: Instanciar e injetar os casos de uso aqui
    # Exemplo (precisa ser substituído pela injeção real):
    # from ostervalt.infraestrutura.persistencia.repositorio_inventario import RepositorioInventarioSQLAlchemy
    # from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
    # from ostervalt.infraestrutura.persistencia.repositorio_itens import RepositorioItensSQLAlchemy
    # from ostervalt.infraestrutura.configuracao.db import SessionLocal
    # repo_inv = RepositorioInventarioSQLAlchemy(SessionLocal)
    # repo_pers = RepositorioPersonagensSQLAlchemy(SessionLocal) # Necessário para listar
    # repo_item = RepositorioItensSQLAlchemy(SessionLocal) # Necessário para adicionar/remover
    # listar_uc = ListarInventario(repo_inv, repo_pers)
    # add_uc = AdicionarItemInventario(repo_inv, repo_item) # Simplificado
    # rem_uc = RemoverItemInventario(repo_inv) # Simplificado
    # await bot.add_cog(InventarioCog(bot, listar_uc, add_uc, rem_uc))
    print("Função setup do InventarioCog chamada, mas a injeção de dependência real precisa ser configurada.")
    # Por enquanto, não adicionaremos o Cog até a injeção estar pronta no ostervalt.py
    pass