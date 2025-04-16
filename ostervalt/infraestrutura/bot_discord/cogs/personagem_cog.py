import discord
from discord.ext import commands
from discord import app_commands, Member
from typing import List
import traceback

# Importar casos de uso e DTOs necessários
from ostervalt.nucleo.casos_de_uso.criar_personagem import CriarPersonagem
from ostervalt.nucleo.casos_de_uso.obter_personagem import ObterPersonagem
from ostervalt.nucleo.casos_de_uso.listar_personagens import ListarPersonagens
from ostervalt.nucleo.casos_de_uso.dtos import PersonagemDTO, ListaPersonagensDTO
from ostervalt.infraestrutura.persistencia.models import StatusPersonagem
# from ostervalt.infraestrutura.bot_discord.autocomplete import autocomplete_character # Removido
from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
from ostervalt.nucleo.entidades.personagem import Personagem
# Importar utilitários do Cog
from ostervalt.infraestrutura.bot_discord.discord_helpers import (
    obter_contexto_comando,
    buscar_personagem_por_nome,
    autocomplete_character as util_autocomplete_character, # Importa e renomeia
    autocomplete_active_character as util_autocomplete_active_character, # Importa e renomeia
    ComandoForaDeServidorError,
    PersonagemNaoEncontradoError,
    CogUtilsError
)

class PersonagemCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        criar_personagem_uc: CriarPersonagem,
        obter_personagem_uc: ObterPersonagem,
        listar_personagens_uc: ListarPersonagens,
        repo_personagens: RepositorioPersonagensSQLAlchemy,
    ):
        self.bot = bot
        self.criar_personagem_uc = criar_personagem_uc
        self.obter_personagem_uc = obter_personagem_uc
        self.listar_personagens_uc = listar_personagens_uc
        self.repo_personagens = repo_personagens
        print("Cog Personagem carregado.")
    
        # --- Autocomplete (Usando funções de cog_utils) ---
        async def autocomplete_character(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
            # TODO: Passar ListarPersonagensUC para a função utilitária quando ela for adaptada,
            #       por enquanto, a função utilitária usa o repo diretamente.
            return await util_autocomplete_character(interaction, current, self.repo_personagens)
    
        async def autocomplete_active_character(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
            # TODO: Passar ListarPersonagensUC para a função utilitária quando ela for adaptada,
            #       por enquanto, a função utilitária usa o repo diretamente.
            return await util_autocomplete_active_character(interaction, current, self.repo_personagens)
    
        # --- Comandos Slash ---

    @app_commands.command(name="criar", description="Cria um novo personagem.")
    @app_commands.describe(nome="O nome do seu novo personagem")
    async def criar_personagem(self, interaction: discord.Interaction, nome: str):
        """Cria um novo personagem para o usuário."""
        await interaction.response.defer(ephemeral=True)
        try:
            user_id, server_id = await obter_contexto_comando(interaction)

            resultado_personagem = self.criar_personagem_uc.executar(
                nome=nome,
                usuario_id=user_id,
                servidor_id=server_id
            )
            resultado_dto = PersonagemDTO(
                id=resultado_personagem.id,
                nome=resultado_personagem.nome,
                nivel=resultado_personagem.nivel,
                dinheiro=resultado_personagem.dinheiro
            )

            embed = discord.Embed(
                title="🎉 Personagem Criado!",
                description=f"Bem-vindo(a) a Ostervalt, **{resultado_dto.nome}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="ID", value=resultado_dto.id, inline=True)
            embed.add_field(name="Nível", value=resultado_dto.nivel, inline=True)
            embed.add_field(name="Dinheiro", value=f"🪙 {resultado_dto.dinheiro}", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except ComandoForaDeServidorError as e:
             await interaction.followup.send(f"❌ {e.mensagem}", ephemeral=True)
        except ValueError as e:
            print(f"Erro de valor ao criar personagem: {e}")
            await interaction.followup.send(f"❌ Erro ao criar o personagem: {e}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao criar personagem: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao criar o personagem.", ephemeral=True)

    @app_commands.command(name="perfil", description="Exibe o perfil de um personagem.")
    @app_commands.describe(character="O nome do personagem que você quer ver") # Alterado para nome
    @app_commands.autocomplete(character=autocomplete_character) # Usa autocomplete geral
    async def ver_perfil(self, interaction: discord.Interaction, character: str): # Alterado para receber nome
        """Exibe o perfil de um personagem."""
        await interaction.response.defer(ephemeral=True)
        try:
            # Usar função utilitária para buscar personagem (inclui obter contexto)
            target_personagem = await buscar_personagem_por_nome(
                interaction, character, self.listar_personagens_uc, apenas_ativos=False # Busca qualquer status
            )

            # Criar DTO a partir da entidade
            resultado_dto = PersonagemDTO(
                id=target_personagem.id,
                nome=target_personagem.nome,
                nivel=target_personagem.nivel,
                dinheiro=target_personagem.dinheiro,
                criado_em=getattr(target_personagem, 'criado_em', None)
            )

            embed = discord.Embed(
                title=f"👤 Perfil de {resultado_dto.nome}",
                color=discord.Color.blue()
            )
            embed.add_field(name="ID", value=resultado_dto.id, inline=True)
            embed.add_field(name="Nível", value=resultado_dto.nivel, inline=True)
            embed.add_field(name="Dinheiro", value=f"🪙 {resultado_dto.dinheiro}", inline=True)
            status_str = f" ({target_personagem.status.value.capitalize()})" if target_personagem.status else ""
            embed.add_field(name="Status", value=status_str if status_str else "Ativo", inline=True)
            if resultado_dto.criado_em:
                embed.set_footer(text=f"Criado em: {resultado_dto.criado_em.strftime('%d/%m/%Y %H:%M')}")

            await interaction.followup.send(embed=embed, ephemeral=True)
        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             await interaction.followup.send(f"❌ {e.mensagem}", ephemeral=True)
        except ValueError as e: # Erros específicos do caso de uso (se houver)
            print(f"Erro de valor ao obter perfil: {e}")
            await interaction.followup.send(f"❌ Erro ao buscar perfil: {e}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao obter perfil: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao buscar o perfil.", ephemeral=True)

    @app_commands.command(name="personagens", description="Lista todos os seus personagens.")
    async def listar_personagens(self, interaction: discord.Interaction):
        """Lista todos os personagens pertencentes ao usuário."""
        await interaction.response.defer(ephemeral=True)
        try:
            user_id, server_id = await obter_contexto_comando(interaction)

            personagens = self.listar_personagens_uc.executar(usuario_id=user_id, servidor_id=server_id)

            if not personagens:
                await interaction.followup.send("você ainda não criou nenhum personagem. Use `/criar`!", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🎭 Seus Personagens ({len(personagens)})",
                color=discord.Color.purple()
            )
            personagens.sort(key=lambda p: p.status == StatusPersonagem.APOSENTADO if p.status else False)
            for p in personagens:
                status_str = f" ({p.status.value.capitalize()})" if p.status else ""
                embed.add_field(
                    name=f"{p.nome} (ID: {p.id}){status_str}",
                    value=f"Nível: {p.nivel} | Dinheiro: 🪙 {p.dinheiro}",
                    inline=False
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except ComandoForaDeServidorError as e:
             await interaction.followup.send(f"❌ {e.mensagem}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao listar personagens: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro ao listar seus personagens.", ephemeral=True)

    @app_commands.command(name="inss", description="Aposenta um personagem ativo") # Descrição ajustada
    @app_commands.describe(character="Nome do personagem ativo a aposentar") # Descrição ajustada
    @app_commands.autocomplete(character=autocomplete_active_character) # Usa autocomplete de ativos
    async def inss(self, interaction: discord.Interaction, character: str):
        """Aposenta um personagem alterando seu status para APOSENTADO."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Usar função utilitária para buscar personagem ATIVO
            personagem_encontrado = await buscar_personagem_por_nome(
                interaction, character, self.listar_personagens_uc, apenas_ativos=True
            )

            # A função buscar_personagem_por_nome já garante que o personagem foi encontrado
            # e está ativo se apenas_ativos=True. Não precisamos mais das checagens manuais.

            # Buscar a entidade completa para atualizar (pode ser necessário se o UC de listar não retornar tudo)
            # Se ListarPersonagens já retorna a entidade completa, podemos usar personagem_encontrado diretamente.
            # Assumindo que precisamos buscar novamente com ObterPersonagem para ter certeza:
            personagem_para_atualizar = self.obter_personagem_uc.executar(personagem_id=personagem_encontrado.id)
            if not personagem_para_atualizar:
                 # Este erro não deveria acontecer se buscar_personagem_por_nome funcionou
                 await interaction.followup.send(f"❌ Erro interno ao re-buscar personagem {personagem_encontrado.nome}.", ephemeral=True)
                 return

            # Verificar se já está aposentado (redundante se buscar_personagem_por_nome(apenas_ativos=True) funcionou)
            if personagem_para_atualizar.status == StatusPersonagem.APOSENTADO:
                 await interaction.followup.send(f"ℹ️ O personagem {personagem_para_atualizar.nome} já está aposentado.", ephemeral=True)
                 return

            personagem_para_atualizar.status = StatusPersonagem.APOSENTADO
            self.repo_personagens.atualizar(personagem_para_atualizar)
            await interaction.followup.send(f"✅ Personagem **{personagem_para_atualizar.nome}** foi aposentado com sucesso.", ephemeral=True)

        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             # PersonagemNaoEncontradoError aqui significa que não achou um ATIVO com esse nome
             await interaction.followup.send(f"❌ {e.mensagem}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao aposentar personagem {character}: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao tentar aposentar o personagem.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # A injeção é feita pelo carregador_cogs.py
    pass