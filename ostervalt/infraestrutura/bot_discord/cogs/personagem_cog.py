import discord
from discord.ext import commands
from discord import app_commands

class PersonagemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="criar", description="Cria um novo personagem")
    async def criar_personagem(self, interaction: discord.Interaction, nome: str):
        await interaction.response.send_message(f"Criando personagem {nome}...")

    @app_commands.command(name="perfil", description="Visualiza o perfil do seu personagem")
    async def perfil_personagem(self, interaction: discord.Interaction):
        await interaction.response.send_message("Visualizando perfil...")

    @app_commands.command(name="personagens", description="Lista todos os personagens")
    async def listar_personagens(self, interaction: discord.Interaction):
        await interaction.response.send_message("Listando personagens...")

async def setup(bot):
    await bot.add_cog(PersonagemCog(bot))

    # --- Comandos Slash ---

    @app_commands.command(name="criar", description="Cria um novo personagem.")
    @app_commands.describe(nome="O nome do seu novo personagem")
    async def criar_personagem(self, interaction: discord.Interaction, nome: str):
        """Cria um novo personagem para o usuário."""
        await interaction.response.defer(ephemeral=True) # Resposta inicial para evitar timeout
        try:
            comando_dto = ComandoDTO(
                discord_id=interaction.user.id,
                parametros={'nome': nome}
            )
            resultado_dto: PersonagemDTO = self.criar_personagem_uc.executar(comando_dto)
            embed = discord.Embed(
                title="🎉 Personagem Criado!",
                description=f"Bem-vindo(a) a Ostervalt, **{resultado_dto.nome}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="ID", value=resultado_dto.id, inline=True)
            embed.add_field(name="Nível", value=resultado_dto.nivel, inline=True)
            embed.add_field(name="Dinheiro", value=f"🪙 {resultado_dto.dinheiro}", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            # TODO: Tratar exceções específicas (e.g., personagem já existe)
            print(f"Erro ao criar personagem: {e}") # Log de erro
            await interaction.followup.send(f"❌ Ocorreu um erro ao criar o personagem: {e}", ephemeral=True)

    @app_commands.command(name="perfil", description="Exibe o perfil de um personagem.")
    @app_commands.describe(personagem_id="O ID do personagem que você quer ver (opcional, mostra o ativo se omitido)")
    async def ver_perfil(self, interaction: discord.Interaction, personagem_id: int | None = None):
        """Exibe o perfil de um personagem."""
        await interaction.response.defer(ephemeral=True)
        try:
            # TODO: Implementar lógica para obter personagem ativo se ID for None
            if personagem_id is None:
                 await interaction.followup.send("⚠️ Por favor, forneça o ID do personagem.", ephemeral=True)
                 return

            comando_dto = ComandoDTO(
                discord_id=interaction.user.id,
                parametros={'personagem_id': personagem_id}
            )
            resultado_dto: PersonagemDTO = self.obter_personagem_uc.executar(comando_dto)

            embed = discord.Embed(
                title=f"👤 Perfil de {resultado_dto.nome}",
                color=discord.Color.blue()
            )
            embed.add_field(name="ID", value=resultado_dto.id, inline=True)
            embed.add_field(name="Nível", value=resultado_dto.nivel, inline=True)
            embed.add_field(name="Dinheiro", value=f"🪙 {resultado_dto.dinheiro}", inline=True)
            embed.add_field(name="Experiência", value=f"{resultado_dto.experiencia}/{resultado_dto.experiencia_necessaria}", inline=True)
            embed.add_field(name="Energia", value=f"{resultado_dto.energia}/{resultado_dto.energia_maxima}", inline=True)
            embed.add_field(name="Vida", value=f"{resultado_dto.vida}/{resultado_dto.vida_maxima}", inline=True)
            embed.set_footer(text=f"Criado em: {resultado_dto.criado_em.strftime('%d/%m/%Y %H:%M')}")

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            # TODO: Tratar exceção de PersonagemNaoEncontrado
            print(f"Erro ao obter perfil: {e}")
            await interaction.followup.send(f"❌ Não foi possível encontrar o personagem com ID {personagem_id}. Erro: {e}", ephemeral=True)

    @app_commands.command(name="personagens", description="Lista todos os seus personagens.")
    async def listar_personagens(self, interaction: discord.Interaction):
        """Lista todos os personagens pertencentes ao usuário."""
        await interaction.response.defer(ephemeral=True)
        try:
            comando_dto = ComandoDTO(discord_id=interaction.user.id)
            resultado_dto: ListaPersonagensDTO = self.listar_personagens_uc.executar(comando_dto)

            if not resultado_dto.personagens:
                await interaction.followup.send("você ainda não criou nenhum personagem. Use `/criar`!", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🎭 Seus Personagens ({len(resultado_dto.personagens)})",
                color=discord.Color.purple()
            )
            for p in resultado_dto.personagens:
                embed.add_field(
                    name=f"{p.nome} (ID: {p.id})",
                    value=f"Nível: {p.nivel} | Dinheiro: 🪙 {p.dinheiro}",
                    inline=False
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Erro ao listar personagens: {e}")
            await interaction.followup.send(f"❌ Ocorreu um erro ao listar seus personagens: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # TODO: Instanciar e injetar os casos de uso aqui
    # Exemplo (precisa ser substituído pela injeção real):
    # from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
    # from ostervalt.infraestrutura.configuracao.db import SessionLocal
    # repo = RepositorioPersonagensSQLAlchemy(SessionLocal)
    # criar_uc = CriarPersonagem(repo)
    # obter_uc = ObterPersonagem(repo)
    # listar_uc = ListarPersonagens(repo)
    # await bot.add_cog(PersonagemCog(bot, criar_uc, obter_uc, listar_uc))
    print("Função setup do PersonagemCog chamada, mas a injeção de dependência real precisa ser configurada.")
    # Por enquanto, não adicionaremos o Cog até a injeção estar pronta no ostervalt.py
    pass