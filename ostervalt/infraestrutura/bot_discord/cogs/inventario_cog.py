import discord
from discord.ext import commands
from discord import app_commands

# Importar casos de uso e DTOs necessários
from ostervalt.nucleo.casos_de_uso.listar_inventario import ListarInventario
from ostervalt.nucleo.casos_de_uso.adicionar_item_inventario import AdicionarItemInventario
from ostervalt.nucleo.casos_de_uso.remover_item_inventario import RemoverItemInventario
# Removido ComandoDTO se não for usado em outros lugares
from ostervalt.nucleo.casos_de_uso.dtos import InventarioDTO, PersonagemDTO # Adicionado PersonagemDTO
# Adicionar importação de ListarPersonagens se necessário para obter personagem ativo
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens

class InventarioCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        listar_inventario_uc: ListarInventario,
        adicionar_item_uc: AdicionarItemInventario,
        remover_item_uc: RemoverItemInventario,
        # Adicionar listar_personagens_uc se for usado para obter personagem ativo
        listar_personagens_uc: ListarPersonagens,
    ):
        self.bot = bot
        self.listar_inventario_uc = listar_inventario_uc
        self.adicionar_item_uc = adicionar_item_uc
        self.remover_item_uc = remover_item_uc
        self.listar_personagens_uc = listar_personagens_uc # Adicionado
        print("Cog Inventario carregado.")

    # --- Comandos Slash ---

    @app_commands.command(name="inventario", description="Mostra o inventário do seu personagem ativo.")
    async def ver_inventario(self, interaction: discord.Interaction):
        """Exibe os itens no inventário do personagem."""
        await interaction.response.defer(ephemeral=True)
        try:
            user_id = interaction.user.id
            server_id = interaction.guild_id
            if not server_id:
                 await interaction.followup.send("❌ Este comando só pode ser usado em um servidor.", ephemeral=True)
                 return

            # 1. Obter ID do personagem ativo (PRECISA IMPLEMENTAR A LÓGICA CORRETA)
            personagens_usuario: list[PersonagemDTO] = self.listar_personagens_uc.executar(
                usuario_id=user_id, servidor_id=server_id
            )
            personagem_ativo_id: int | None = None
            personagem_ativo_nome: str | None = None
            for p in personagens_usuario:
                # Assumindo que PersonagemDTO tem um campo 'status' ou similar
                # if p.status == 'ativo': # Ajustar conforme a definição de PersonagemDTO
                personagem_ativo_id = p.id
                personagem_ativo_nome = p.nome # Guardar nome para o título do embed
                break # Pega o primeiro encontrado

            if personagem_ativo_id is None:
                 await interaction.followup.send("❌ Você não tem um personagem ativo neste servidor.", ephemeral=True)
                 return

            # 2. Executar caso de uso com personagem_id
            # O caso de uso ListarInventario retorna List[ItemInventario], não um DTO complexo
            itens_inventario = self.listar_inventario_uc.executar(personagem_id=personagem_ativo_id) # Chamada corrigida

            if not itens_inventario:
                await interaction.followup.send("🎒 Seu inventário está vazio.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🎒 Inventário de {personagem_ativo_nome or 'Personagem Ativo'}", # Usa nome guardado
                color=discord.Color.orange()
            )
            # Agrupa itens para melhor visualização
            itens_agrupados = {}
            for item in itens_inventario: # Iterar sobre a lista retornada pelo UC
                # Precisamos buscar o nome e descrição do item mestre (isso pode exigir outro UC ou ajuste no ListarInventario)
                # Placeholder:
                nome_item_placeholder = f"Item ID {item.item_id}"
                descricao_item_placeholder = "Descrição não disponível"

                if item.item_id not in itens_agrupados:
                    itens_agrupados[item.item_id] = {'nome': nome_item_placeholder, 'quantidade': 0, 'descricao': descricao_item_placeholder}
                itens_agrupados[item.item_id]['quantidade'] += item.quantidade

            for item_id, data in itens_agrupados.items():
                 embed.add_field(
                    name=f"{data['nome']} (ID: {item_id})",
                    value=f"Quantidade: {data['quantidade']}\n*'{data['descricao']}'*",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Erro ao listar inventário: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro ao buscar seu inventário.", ephemeral=True) # Mensagem genérica

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
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao adicionar o item.", ephemeral=True)

    @app_commands.command(name="remitem", description="Remove uma quantidade de um item do seu inventário.")
    @app_commands.describe(item_id="ID do item a remover", quantidade="Quantidade a remover")
    async def remover_item(self, interaction: discord.Interaction, item_id: int, quantidade: int = 1):
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

            # 1. Obter ID do personagem ativo (PRECISA IMPLEMENTAR A LÓGICA CORRETA)
            personagens_usuario: list[PersonagemDTO] = self.listar_personagens_uc.executar(
                usuario_id=user_id, servidor_id=server_id
            )
            personagem_ativo_id: int | None = None
            for p in personagens_usuario:
                # if p.status == 'ativo': # Ajustar conforme a definição de PersonagemDTO
                personagem_ativo_id = p.id
                break

            if personagem_ativo_id is None:
                 await interaction.followup.send("❌ Não foi possível determinar seu personagem ativo.", ephemeral=True)
                 return

            # 2. Executar caso de uso remover_item
            # TODO: A lógica de quantidade precisa ser tratada. O UC atual remove o item inteiro.
            # Se for para remover quantidade específica, o UC precisa ser modificado ou
            # precisamos buscar o item, verificar quantidade e chamar atualizar_quantidade do repo.
            self.remover_item_uc.executar(
                item_id=item_id,
                personagem_id=personagem_ativo_id
            )

            await interaction.followup.send(f"✅ Item ID {item_id} removido do seu inventário (lógica de quantidade a ser revisada).", ephemeral=True)

        except ValueError as e: # Captura erros como item não encontrado no inventário
            print(f"Erro de valor ao remover item: {e}")
            await interaction.followup.send(f"❌ Erro ao remover item: {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao remover item: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao remover o item.", ephemeral=True)

    @adicionar_item.error
    async def additem_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            # Usar followup se a resposta já foi deferida
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