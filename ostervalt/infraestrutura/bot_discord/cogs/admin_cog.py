# -*- coding: utf-8 -*-
import discord
import asyncio
import yaml
import json
import random
import os
import datetime
import traceback # Para log de erro
from discord.ext import commands
from discord import app_commands, Role, Member, Interaction # Adicionado Interaction
from typing import List, Optional

# Importar tipos dos repositórios e entidades
from ostervalt.infraestrutura.persistencia.repositorio_configuracao_servidor import RepositorioConfiguracaoServidor
from ostervalt.infraestrutura.persistencia.repositorio_estoque_loja import RepositorioEstoqueLoja
from ostervalt.infraestrutura.persistencia.repositorio_personagens import RepositorioPersonagensSQLAlchemy
from ostervalt.infraestrutura.persistencia.repositorio_itens import RepositorioItensSQLAlchemy
from ostervalt.infraestrutura.persistencia.models import EstoqueLojaItemModel, ItemModel, StatusPersonagem
from ostervalt.nucleo.entidades.item import Item
from ostervalt.nucleo.entidades.personagem import Personagem
# Importar utilitários do Cog
from ostervalt.infraestrutura.bot_discord.discord_helpers import (
    obter_contexto_comando,
    buscar_personagem_por_nome_para_usuario, # Função para buscar char de outro user
    autocomplete_character_for_user as util_autocomplete_character_for_user, # Renomeado para evitar conflito
    autocomplete_item as util_autocomplete_item, # Renomeado para evitar conflito
    ComandoForaDeServidorError,
    PersonagemNaoEncontradoError,
    CogUtilsError
)


# Função para carregar config (pode ser movida para um utilitário compartilhado depois)
def load_config_from_file():
    """Carrega as configurações do arquivo config.yaml."""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            print("AdminCog: Configuração (config.yaml) lida para sincronização.")
            return config_data if config_data else {}
    except FileNotFoundError:
        print("AdminCog: Aviso - Arquivo config.yaml não encontrado durante sync.")
        return {}
    except Exception as e:
        print(f"AdminCog: Erro ao carregar config.yaml durante sync: {e}")
        return {}

class AdminCog(commands.Cog):
    """Cog para comandos administrativos e de configuração."""
    def __init__(
        self,
        bot: commands.Bot,
        repo_config_servidor: RepositorioConfiguracaoServidor,
        repo_estoque_loja: RepositorioEstoqueLoja,
        repo_personagens: RepositorioPersonagensSQLAlchemy,
        repo_itens: RepositorioItensSQLAlchemy,
    ):
        self.bot = bot
        self.repo_config_servidor = repo_config_servidor
        self.repo_estoque_loja = repo_estoque_loja
        self.repo_personagens = repo_personagens
        self.repo_itens = repo_itens
        print("Cog Admin carregado.")

    # --- Autocomplete Methods (Usando as funções de cog_utils) ---
    async def autocomplete_character_for_user(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        # Chama a função utilitária passando o repositório
        return await util_autocomplete_character_for_user(interaction, current, self.repo_personagens)

    async def autocomplete_item(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        # Chama a função utilitária passando o repositório
        return await util_autocomplete_item(interaction, current, self.repo_itens)

    # --- Comandos de prefixo (Mantidos como estão) ---
    @commands.command(name="sync_commands")
    @commands.is_owner()
    async def sync_commands_prefix(self, ctx):
        """Sincroniza os comandos de slash com o Discord."""
        guild = ctx.guild
        try:
            if guild:
                self.bot.tree.clear_commands(guild=guild)
                synced = await self.bot.tree.sync(guild=guild)
                await ctx.send(f"Sincronizados {len(synced)} comandos para este servidor.")
            else:
                 synced = await self.bot.tree.sync()
                 await ctx.send(f"Sincronizados {len(synced)} comandos globais.")
        except Exception as e:
            await ctx.send(f"Erro ao sincronizar: {e}")
            traceback.print_exc()


    @commands.command(name="list_commands")
    @commands.is_owner()
    async def list_commands_prefix(self, ctx):
        """Lista todos os comandos disponíveis no servidor."""
        guild = ctx.guild
        try:
            if guild:
                guild_commands = await self.bot.tree.fetch_commands(guild=guild)
                await ctx.send(f"Comandos do servidor: {', '.join(cmd.name for cmd in guild_commands)}")
            else:
                 global_commands = await self.bot.tree.fetch_commands()
                 await ctx.send(f"Comandos globais: {', '.join(cmd.name for cmd in global_commands)}")
        except Exception as e:
             await ctx.send(f"Erro ao listar comandos: {e}")


    # --- Comandos de aplicação (slash commands) ---
    @app_commands.command(name="cargos", description="Define cargos com permissões especiais")
    @app_commands.describe(
        tipo="Tipo de permissão (saldo ou marcos)",
        acao="Adicionar ou remover cargo",
        cargo="Cargo a ser adicionado ou removido"
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Saldo", value="saldo"),
            app_commands.Choice(name="Marcos", value="marcos")
        ],
        acao=[
            app_commands.Choice(name="Adicionar", value="add"),
            app_commands.Choice(name="Remover", value="remove")
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def cargos(self, interaction: Interaction, tipo: str, acao: str, cargo: Role):
        """Gerencia os cargos com permissões especiais."""
        try:
            # Usar obter_contexto_comando para validar que está em servidor
            _, server_id = await obter_contexto_comando(interaction)
            key = f"cargos_{tipo}_ids"

            cargos_lista = self.repo_config_servidor.obter_valor(server_id, key, default=[])

            if acao == "add":
                if cargo.id not in cargos_lista:
                    cargos_lista.append(cargo.id)
                    self.repo_config_servidor.adicionar_ou_atualizar(server_id, key, cargos_lista)
                    await interaction.response.send_message(f"Cargo {cargo.name} adicionado às permissões de {tipo}.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Cargo {cargo.name} já está nas permissões de {tipo}.", ephemeral=True)
            elif acao == "remove":
                if cargo.id in cargos_lista:
                    cargos_lista.remove(cargo.id)
                    self.repo_config_servidor.adicionar_ou_atualizar(server_id, key, cargos_lista)
                    await interaction.response.send_message(f"Cargo {cargo.name} removido das permissões de {tipo}.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Cargo {cargo.name} não estava nas permissões de {tipo}.", ephemeral=True)

        except ComandoForaDeServidorError as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao gerenciar cargos para servidor {interaction.guild_id}: {e}") # Usar interaction.guild_id aqui é seguro pois passou por obter_contexto_comando
            traceback.print_exc()
            await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao gerenciar cargos.", ephemeral=True)

    @app_commands.command(name="estoque", description="Gera um novo estoque para a loja")
    @app_commands.describe(
        common="Número de itens comuns",
        uncommon="Número de itens incomuns",
        rare="Número de itens raros",
        very_rare="Número de itens muito raros"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def estoque(self, interaction: Interaction, common: int, uncommon: int, rare: int, very_rare: int):
        """Gera um novo estoque de itens para a loja."""
        try:
            _, server_id = await obter_contexto_comando(interaction)
            await interaction.response.defer(ephemeral=True)

            self.repo_estoque_loja.limpar_estoque_servidor(server_id)
            await interaction.followup.send("Estoque antigo limpo. Gerando novo estoque...", ephemeral=True)

            rarities = {'common': common, 'uncommon': uncommon, 'rare': rare, 'very rare': very_rare}
            preco_padrao_fallback = self.repo_config_servidor.obter_valor(server_id, 'preco_item_padrao', default=100)
            itens_adicionados = []

            for raridade_str, count_req in rarities.items():
                if count_req <= 0: continue

                itens_disponiveis: list[Item] = self.repo_itens.listar_por_raridade(raridade_str)

                if not itens_disponiveis:
                    await interaction.followup.send(f"⚠️ Nenhum item encontrado para a raridade: {raridade_str}", ephemeral=True)
                    continue

                available_count = len(itens_disponiveis)
                count = min(count_req, available_count)

                if count_req > available_count:
                     await interaction.followup.send(f"ℹ️ Solicitados {count_req} itens {raridade_str}, mas apenas {available_count} disponíveis.", ephemeral=True)

                itens_selecionados = random.sample(itens_disponiveis, count)
                await interaction.followup.send(f"Definindo preços para {count} itens {raridade_str}:", ephemeral=True)

                for item_obj in itens_selecionados:
                    preco_final = None
                    attempts = 0
                    while preco_final is None and attempts < 3:
                        await interaction.followup.send(f"Digite o preço para **{item_obj.nome}** (em moedas):", ephemeral=True)
                        try:
                            price_message = await self.bot.wait_for(
                                'message',
                                check=lambda m: m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit(),
                                timeout=60.0
                            )
                            price = int(price_message.content)
                            if price >= 0: preco_final = price
                            else:
                                await interaction.followup.send("O preço não pode ser negativo. Tente novamente.", ephemeral=True)
                                attempts += 1
                        except asyncio.TimeoutError:
                            await interaction.followup.send(f"Tempo esgotado para {item_obj.nome}. Tentativa {attempts + 1} de 3.", ephemeral=True)
                            attempts += 1
                        except Exception as e_price:
                             await interaction.followup.send(f"Erro inesperado ao processar preço para {item_obj.nome}: {e_price}", ephemeral=True)
                             attempts += 1

                    if preco_final is None:
                        preco_final = item_obj.valor # Usa o valor base do item como fallback
                        await interaction.followup.send(f"Falha ao definir preço para {item_obj.nome}. Usando preço padrão de {preco_final} moedas.", ephemeral=True)

                    item_estoque = EstoqueLojaItemModel(
                        servidor_id=server_id,
                        item_id=item_obj.id,
                        quantidade=1, # Adiciona 1 de cada item selecionado
                        preco_especifico=preco_final
                    )
                    self.repo_estoque_loja.adicionar(item_estoque)
                    itens_adicionados.append(f"{item_obj.nome} ({raridade_str}) - {preco_final} moedas")
                    await interaction.followup.send(f"✅ Preço de {item_obj.nome} definido como {preco_final} moedas e adicionado ao estoque.", ephemeral=True)

            if itens_adicionados:
                summary = "✅ Novo estoque gerado com sucesso:\n" + "\n".join(f"- {item_info}" for item_info in itens_adicionados)
            else:
                summary = "ℹ️ Nenhum item foi adicionado ao estoque (verifique se existem itens cadastrados no banco de dados)."
            await interaction.followup.send(summary, ephemeral=True)

        except ComandoForaDeServidorError as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True) # Usa send_message se defer falhou
        except Exception as e:
            print(f"Erro ao gerar estoque para {interaction.guild_id}: {e}")
            traceback.print_exc()
            # Tenta followup, se falhar, tenta response (caso o defer não tenha sido chamado)
            try:
                await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao gerar o estoque.", ephemeral=True)
            except (discord.NotFound, discord.InteractionResponded):
                 try:
                      await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao gerar o estoque.", ephemeral=True)
                 except discord.InteractionResponded:
                      pass # Já respondeu de alguma forma

    @app_commands.command(name="inserir", description="Insere um item no estoque da loja")
    @app_commands.describe(
        raridade="Raridade do item", # Raridade não é mais usada para buscar, apenas informativo?
        item="Nome do item a ser inserido",
        quantidade="Quantidade do item",
        valor="Valor do item (opcional, usa valor base se não informado)"
    )
    @app_commands.choices( # Mantido para UI, mas não usado na lógica
        raridade=[
            app_commands.Choice(name="Comum", value="common"),
            app_commands.Choice(name="Incomum", value="uncommon"),
            app_commands.Choice(name="Raro", value="rare"),
            app_commands.Choice(name="Muito Raro", value="very rare")
        ]
    )
    @app_commands.autocomplete(item=autocomplete_item) # Usa o autocomplete refatorado
    @app_commands.checks.has_permissions(administrator=True)
    async def inserir(self, interaction: Interaction, raridade: str, item: str, quantidade: int, valor: Optional[int] = None): # Valor opcional
        """Insere um item no estoque da loja."""
        try:
            _, server_id = await obter_contexto_comando(interaction)

            if quantidade <= 0:
                 await interaction.response.send_message("A quantidade deve ser positiva.", ephemeral=True)
                 return
            if valor is not None and valor < 0:
                 await interaction.response.send_message("O valor não pode ser negativo.", ephemeral=True)
                 return

            item_mestre = self.repo_itens.obter_por_nome(item)
            if not item_mestre:
                await interaction.response.send_message(f"❌ Item mestre '{item}' não encontrado.", ephemeral=True)
                return

            item_estoque_existente = self.repo_estoque_loja.obter_por_servidor_e_item(server_id, item_mestre.id)

            if item_estoque_existente:
                item_estoque_existente.quantidade += quantidade
                if valor is not None: # Atualiza preço apenas se fornecido
                    item_estoque_existente.preco_especifico = valor
                self.repo_estoque_loja.atualizar(item_estoque_existente)
                preco_exibido = item_estoque_existente.preco_especifico if item_estoque_existente.preco_especifico is not None else item_mestre.valor
                await interaction.response.send_message(f"✅ Quantidade do item '{item}' atualizada para {item_estoque_existente.quantidade}. Preço: {preco_exibido} moedas.", ephemeral=True)
            else:
                preco_final = valor if valor is not None else item_mestre.valor # Usa valor base se não especificado

                novo_item_estoque = EstoqueLojaItemModel(
                    servidor_id=server_id,
                    item_id=item_mestre.id,
                    quantidade=quantidade,
                    preco_especifico=valor # Salva None se não fornecido, repo pode usar valor base
                )
                self.repo_estoque_loja.adicionar(novo_item_estoque)
                await interaction.response.send_message(f"✅ Item '{item}' adicionado ao estoque com quantidade {quantidade} e preço {preco_final} moedas.", ephemeral=True)

        except ComandoForaDeServidorError as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except Exception as e:
            print(f"Erro inesperado ao inserir item '{item}' no estoque para {interaction.guild_id}: {type(e).__name__} - {e}")
            traceback.print_exc()
            # Tenta responder se ainda não o fez
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao inserir o item.", ephemeral=True)
            else: # Se já respondeu (ex: erro no repo após adicionar), tenta followup
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao inserir o item.", ephemeral=True)
                 except discord.HTTPException:
                      pass # Evita erro se followup falhar

    @app_commands.command(name="remover", description="Remove um item do estoque da loja")
    @app_commands.describe(
        item="Nome do item a ser removido",
        quantidade="Quantidade a ser removida (padrão: todos)"
    )
    @app_commands.autocomplete(item=autocomplete_item) # Usa o autocomplete refatorado
    @app_commands.checks.has_permissions(administrator=True)
    async def remover(self, interaction: Interaction, item: str, quantidade: Optional[int] = None): # Quantidade opcional
        """Remove um item do estoque da loja."""
        try:
            _, server_id = await obter_contexto_comando(interaction)

            if quantidade is not None and quantidade <= 0:
                 await interaction.response.send_message("A quantidade a remover deve ser positiva.", ephemeral=True)
                 return

            item_mestre = self.repo_itens.obter_por_nome(item)
            if not item_mestre:
                await interaction.response.send_message(f"❌ Item mestre '{item}' não encontrado.", ephemeral=True)
                return

            item_estoque = self.repo_estoque_loja.obter_por_servidor_e_item(server_id, item_mestre.id)
            if not item_estoque:
                await interaction.response.send_message(f"❌ Item '{item}' não encontrado no estoque deste servidor.", ephemeral=True)
                return

            if quantidade is None or quantidade >= item_estoque.quantidade:
                self.repo_estoque_loja.remover(item_estoque)
                await interaction.response.send_message(f"✅ Item '{item}' removido completamente do estoque.", ephemeral=True)
            else:
                item_estoque.quantidade -= quantidade
                self.repo_estoque_loja.atualizar(item_estoque)
                await interaction.response.send_message(f"✅ Removido {quantidade} de '{item}'. Quantidade restante: {item_estoque.quantidade}", ephemeral=True)

        except ComandoForaDeServidorError as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao remover item '{item}' do estoque para {interaction.guild_id}: {e}")
            traceback.print_exc()
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao remover o item.", ephemeral=True)
            else:
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao remover o item.", ephemeral=True)
                 except discord.HTTPException:
                      pass

    @app_commands.command(name="dinheiro", description="[Admin] Define o dinheiro de um personagem específico de um usuário")
    @app_commands.describe(
        usuario="O usuário dono do personagem",
        character="Nome do personagem",
        amount="Quantidade de dinheiro"
    )
    @app_commands.autocomplete(character=autocomplete_character_for_user) # Usa o autocomplete refatorado
    @app_commands.checks.has_permissions(administrator=True)
    async def dinheiro(self, interaction: Interaction, usuario: Member, character: str, amount: int):
        """Define a quantidade de dinheiro de um personagem."""
        try:
            # obter_contexto_comando valida que está em servidor
            await obter_contexto_comando(interaction)

            if amount < 0:
                  await interaction.response.send_message("A quantidade de dinheiro não pode ser negativa.", ephemeral=True)
                  return

            # Usar a função de busca específica para admin
            personagem_encontrado = await buscar_personagem_por_nome_para_usuario(
                interaction, character, usuario.id, self.repo_personagens
            )

            # A função acima já levanta PersonagemNaoEncontradoError se não achar

            personagem_encontrado.dinheiro = amount
            self.repo_personagens.atualizar(personagem_encontrado)
            await interaction.response.send_message(f"✅ Dinheiro de {personagem_encontrado.nome} (usuário: {usuario.display_name}) definido como {amount} moedas.", ephemeral=True)

        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao definir dinheiro para {character} (usuário {usuario.id}) no servidor {interaction.guild_id}: {e}")
            traceback.print_exc()
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao definir o dinheiro.", ephemeral=True)
            else:
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao definir o dinheiro.", ephemeral=True)
                 except discord.HTTPException:
                      pass


    @app_commands.command(name="saldo", description="[Admin] Adiciona/remove dinheiro do saldo de um personagem de um usuário")
    @app_commands.describe(
        usuario="O usuário dono do personagem",
        character="Nome do personagem",
        amount="Quantidade de dinheiro (use números negativos para remover)"
    )
    @app_commands.autocomplete(character=autocomplete_character_for_user) # Usa o autocomplete refatorado
    @app_commands.checks.has_permissions(administrator=True)
    async def saldo(self, interaction: Interaction, usuario: Member, character: str, amount: int):
        """Adiciona ou remove dinheiro do saldo de um personagem."""
        try:
            await obter_contexto_comando(interaction)

            # Usar a função de busca específica para admin
            personagem_encontrado = await buscar_personagem_por_nome_para_usuario(
                interaction, character, usuario.id, self.repo_personagens
            )

            personagem_encontrado.dinheiro += amount
            novo_saldo = personagem_encontrado.dinheiro
            self.repo_personagens.atualizar(personagem_encontrado)

            if amount > 0:
                msg = f"✅ Adicionado {amount} moedas ao saldo de {personagem_encontrado.nome} (usuário: {usuario.display_name}). Novo saldo: {novo_saldo} moedas."
            elif amount < 0:
                msg = f"✅ Removido {abs(amount)} moedas do saldo de {personagem_encontrado.nome} (usuário: {usuario.display_name}). Novo saldo: {novo_saldo} moedas."
            else:
                 msg = f"ℹ️ Nenhuma alteração no saldo de {personagem_encontrado.nome} (usuário: {usuario.display_name}). Saldo atual: {novo_saldo} moedas."
            await interaction.response.send_message(msg, ephemeral=True)

        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao alterar saldo para {character} (usuário {usuario.id}) no servidor {interaction.guild_id}: {e}")
            traceback.print_exc()
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao alterar o saldo.", ephemeral=True)
            else:
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao alterar o saldo.", ephemeral=True)
                 except discord.HTTPException:
                      pass

    @app_commands.command(name="limpar_estoque", description="[Admin] Limpa o estoque atual da loja")
    @app_commands.checks.has_permissions(administrator=True)
    async def limpar_estoque(self, interaction: Interaction):
        """Limpa o estoque atual da loja."""
        try:
            _, server_id = await obter_contexto_comando(interaction)
            self.repo_estoque_loja.limpar_estoque_servidor(server_id)
            await interaction.response.send_message("✅ O estoque da loja foi limpo com sucesso.", ephemeral=True)
        except ComandoForaDeServidorError as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao limpar estoque para {interaction.guild_id}: {e}")
            traceback.print_exc()
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao limpar o estoque.", ephemeral=True)
            else:
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao limpar o estoque.", ephemeral=True)
                 except discord.HTTPException:
                      pass

    @app_commands.command(name="backup", description="[Admin] Mostra/Envia um backup dos dados do servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(self, interaction: Interaction):
        """Mostra um backup de todos os dados do servidor ou envia como arquivo."""
        try:
            _, server_id = await obter_contexto_comando(interaction)
            await interaction.response.defer(ephemeral=True)

            configuracoes = self.repo_config_servidor.listar_por_servidor_como_dict(server_id)
            estoque_db = self.repo_estoque_loja.listar_por_servidor(server_id)
            estoque_formatado = [
                {"item_id": item.item_id, "quantidade": item.quantidade, "preco": item.preco_especifico}
                for item in estoque_db
            ]
            # Usar método específico para backup que retorna dicts
            personagens_servidor = self.repo_personagens.listar_por_servidor_para_backup(server_id)

            backup_data_dict = {
                "configuracoes": configuracoes,
                "estoque_loja": estoque_formatado,
                "personagens": personagens_servidor,
                "timestamp": datetime.datetime.now().isoformat()
            }

            backup_json_str = json.dumps(backup_data_dict, indent=2, ensure_ascii=False)

            if len(backup_json_str) <= 1900:
                await interaction.followup.send(f"```json\n{backup_json_str}\n```", ephemeral=True)
            else:
                timestamp_file = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                backup_filename = f"backup_{server_id}_{timestamp_file}.json"
                temp_dir = "temp_backups"
                os.makedirs(temp_dir, exist_ok=True)
                backup_filepath = os.path.join(temp_dir, backup_filename)

                with open(backup_filepath, "w", encoding='utf-8') as f:
                    f.write(backup_json_str)

                await interaction.followup.send("O backup é muito grande para ser enviado como mensagem. Enviando como arquivo...", file=discord.File(backup_filepath), ephemeral=True)
                os.remove(backup_filepath) # Remove o arquivo temporário após envio

        except ComandoForaDeServidorError as e:
             # Tenta responder se defer falhou
             try: await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
             except discord.InteractionResponded: pass
        except Exception as e:
            print(f"Erro ao gerar backup para servidor {interaction.guild_id}: {e}")
            traceback.print_exc()
            try:
                await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao gerar o backup.", ephemeral=True)
            except (discord.NotFound, discord.InteractionResponded):
                 try:
                      await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao gerar o backup.", ephemeral=True)
                 except discord.InteractionResponded:
                      pass

    @app_commands.command(name="mensagens", description="[Admin] Adiciona uma mensagem para trabalho ou crime")
    @app_commands.describe(
        tipo="Tipo de mensagem (trabalho ou crime)",
        mensagem="A mensagem a ser adicionada"
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Trabalho", value="trabalho"),
            app_commands.Choice(name="Crime", value="crime")
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def mensagens(self, interaction: Interaction, tipo: str, mensagem: str):
        """Adiciona uma mensagem personalizada para trabalho ou crime."""
        try:
            _, server_id = await obter_contexto_comando(interaction)
            chave_config = f"mensagens_{tipo}" # Ajustado para corresponder ao config

            lista_mensagens = self.repo_config_servidor.obter_valor(server_id, chave_config, default=[])
            if not isinstance(lista_mensagens, list): # Garante que é uma lista
                lista_mensagens = []
            lista_mensagens.append(mensagem)
            self.repo_config_servidor.adicionar_ou_atualizar(server_id, chave_config, lista_mensagens)
            await interaction.response.send_message(f"✅ Mensagem adicionada à lista '{tipo}'.", ephemeral=True)

        except ComandoForaDeServidorError as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao adicionar mensagem tipo '{tipo}' para servidor {interaction.guild_id}: {e}")
            traceback.print_exc()
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao adicionar a mensagem.", ephemeral=True)
            else:
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao adicionar a mensagem.", ephemeral=True)
                 except discord.HTTPException:
                      pass

    @app_commands.command(name="tiers", description="[Admin] Define faixas de níveis para diferentes tiers")
    @app_commands.describe(
        tier="Nome do tier",
        nivel_min="Nível mínimo",
        nivel_max="Nível máximo",
        recompensa="Recompensa em dinheiro"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def tiers(self, interaction: Interaction, tier: str, nivel_min: int, nivel_max: int, recompensa: int):
        """Define faixas de níveis e recompensas para tiers."""
        try:
            _, server_id = await obter_contexto_comando(interaction)

            if nivel_min <= 0 or nivel_max <= 0 or nivel_min > nivel_max:
                  await interaction.response.send_message("Erro: Níveis mínimo e máximo devem ser positivos e mínimo <= máximo.", ephemeral=True)
                  return
            if recompensa < 0:
                  await interaction.response.send_message("Erro: Recompensa não pode ser negativa.", ephemeral=True)
                  return

            chave_config = "tiers" # Chave principal para o dict de tiers

            tiers_atuais = self.repo_config_servidor.obter_valor(server_id, chave_config, default={})
            if not isinstance(tiers_atuais, dict): # Garante que é um dict
                tiers_atuais = {}
            tiers_atuais[tier] = {
                "nivel_min": nivel_min,
                "nivel_max": nivel_max,
                "recompensa": recompensa
            }
            self.repo_config_servidor.adicionar_ou_atualizar(server_id, chave_config, tiers_atuais)
            await interaction.response.send_message(f"✅ Tier '{tier}' definido/atualizado para níveis {nivel_min}-{nivel_max} com recompensa de {recompensa} moedas.", ephemeral=True)

        except ComandoForaDeServidorError as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao definir tier '{tier}' para servidor {interaction.guild_id}: {e}")
            traceback.print_exc()
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao definir o tier.", ephemeral=True)
            else:
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao definir o tier.", ephemeral=True)
                 except discord.HTTPException:
                      pass

    @app_commands.command(name="probabilidade_crime", description="[Admin] Define a probabilidade de sucesso para o comando /crime")
    @app_commands.describe(probabilidade="Probabilidade de sucesso (0 a 100)")
    @app_commands.checks.has_permissions(administrator=True)
    async def probabilidade_crime(self, interaction: Interaction, probabilidade: int):
        """Define a probabilidade de sucesso para o comando /crime."""
        try:
            _, server_id = await obter_contexto_comando(interaction)

            if not (0 <= probabilidade <= 100):
                await interaction.response.send_message("Por favor, insira um valor entre 0 e 100.", ephemeral=True)
                return

            chave_config = "probabilidade_crime"
            self.repo_config_servidor.adicionar_ou_atualizar(server_id, chave_config, probabilidade)
            await interaction.response.send_message(f"✅ Probabilidade de sucesso no crime definida para {probabilidade}%.", ephemeral=True)

        except ComandoForaDeServidorError as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except Exception as e:
            print(f"Erro ao definir probabilidade_crime para servidor {interaction.guild_id}: {e}")
            traceback.print_exc()
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao definir a probabilidade.", ephemeral=True)
            else:
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao definir a probabilidade.", ephemeral=True)
                 except discord.HTTPException:
                      pass

    @app_commands.command(name="rip", description="[Admin] Elimina definitivamente um personagem")
    @app_commands.describe(
        usuario="O usuário dono do personagem",
        character="Nome do personagem a ser eliminado"
    )
    @app_commands.autocomplete(character=autocomplete_character_for_user) # Usa o autocomplete refatorado
    @app_commands.checks.has_permissions(administrator=True)
    async def rip(self, interaction: Interaction, usuario: Member, character: str):
        """Elimina definitivamente um personagem de um usuário."""
        try:
            await obter_contexto_comando(interaction) # Valida servidor

            # Usar a função de busca específica para admin
            personagem_a_remover = await buscar_personagem_por_nome_para_usuario(
                interaction, character, usuario.id, self.repo_personagens
            )
            personagem_a_remover_id = personagem_a_remover.id # Pega o ID

            view = discord.ui.View(timeout=30.0)
            confirm_button = discord.ui.Button(label="Confirmar Eliminação", style=discord.ButtonStyle.danger, custom_id=f"confirm_rip_{interaction.id}")
            cancel_button = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary, custom_id=f"cancel_rip_{interaction.id}")

            async def confirm_callback(interaction_confirm: Interaction):
                if interaction_confirm.user.id != interaction.user.id:
                     await interaction_confirm.response.send_message("Apenas o autor do comando pode confirmar.", ephemeral=True)
                     return
                try:
                    self.repo_personagens.remover(personagem_a_remover_id)
                    # TODO: Remover itens do inventário associados? (Considerar um Caso de Uso para isso)
                    await interaction_confirm.response.edit_message(content=f"Personagem **{character}** de {usuario.display_name} foi eliminado com sucesso.", view=None)
                except Exception as e_rip:
                    print(f"Erro ao remover personagem {personagem_a_remover_id} no callback: {e_rip}")
                    traceback.print_exc()
                    await interaction_confirm.response.edit_message(content=f"Erro ao tentar eliminar o personagem **{character}**.", view=None)
                view.stop()

            async def cancel_callback(interaction_cancel: Interaction):
                 if interaction_cancel.user.id != interaction.user.id:
                     await interaction_cancel.response.send_message("Apenas o autor do comando pode cancelar.", ephemeral=True)
                     return
                 await interaction_cancel.response.edit_message(content="Eliminação cancelada.", view=None)
                 view.stop()

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)

            await interaction.response.send_message(f"Tem certeza que deseja eliminar o personagem **{character}** de {usuario.display_name}? Esta ação é **irreversível**.", view=view, ephemeral=True)

            timeout = await view.wait()
            if timeout:
                 try: await interaction.edit_original_response(content="Tempo de confirmação esgotado. O personagem não foi eliminado.", view=None)
                 except discord.NotFound: pass
                 except discord.HTTPException as e_http: print(f"Erro ao editar msg RIP timeout: {e_http}")

        except (ComandoForaDeServidorError, PersonagemNaoEncontradoError) as e:
             await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
        except CogUtilsError as e: # Captura erros gerais dos utils
             await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        except Exception as e:
            print(f"Erro no comando /rip para {character} (usuário {usuario.id}): {e}")
            traceback.print_exc()
            if not interaction.response.is_done():
                 await interaction.response.send_message(f"❌ Ocorreu um erro inesperado ao tentar eliminar o personagem.", ephemeral=True)
            else:
                 try:
                      await interaction.followup.send(f"❌ Ocorreu um erro inesperado ao tentar eliminar o personagem.", ephemeral=True)
                 except discord.HTTPException:
                      pass


    @app_commands.command(name="sync_config", description="[Admin] Sincroniza config.yaml com o banco de dados do servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_config(self, interaction: Interaction):
        """
        Lê o arquivo config.yaml e atualiza as configurações correspondentes
        no banco de dados para este servidor.
        """
        try:
            _, server_id = await obter_contexto_comando(interaction)
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send("🔄 Iniciando sincronização das configurações do `config.yaml` para este servidor...", ephemeral=True)

            config_yaml = load_config_from_file()
            if not config_yaml:
                await interaction.followup.send("❌ Erro: Não foi possível carregar `config.yaml`. Verifique os logs.", ephemeral=True)
                return

            chaves_para_sincronizar = [
                "messages", "tiers", "probabilidades", "cargos_especiais",
                "precos_padroes", "limites", "progressao"
            ]
            configs_sincronizadas = []
            erros_sincronizacao = []

            for chave_principal in chaves_para_sincronizar:
                if chave_principal in config_yaml:
                    valor = config_yaml[chave_principal]
                    try:
                        self.repo_config_servidor.adicionar_ou_atualizar(server_id, chave_principal, valor)
                        configs_sincronizadas.append(chave_principal)
                    except Exception as e_sync:
                        erro_msg = f"Erro ao sincronizar '{chave_principal}': {e_sync}"
                        print(f"Erro sync config para server {server_id}: {erro_msg}")
                        traceback.print_exc()
                        erros_sincronizacao.append(f"'{chave_principal}'")

            # Mensagem final
            if not erros_sincronizacao:
                msg_final = f"✅ Configurações sincronizadas com sucesso para este servidor a partir do `config.yaml`:\n`{', '.join(configs_sincronizadas)}`"
            else:
                msg_final = f"⚠️ Sincronização concluída com erros.\n"
                if configs_sincronizadas:
                    msg_final += f"✅ Sincronizadas: `{', '.join(configs_sincronizadas)}`\n"
                msg_final += f"❌ Falha ao sincronizar: {', '.join(erros_sincronizacao)}"

            await interaction.followup.send(msg_final, ephemeral=True)

        except ComandoForaDeServidorError as e:
             # Tenta responder se defer falhou
             try: await interaction.response.send_message(f"❌ {e.mensagem}", ephemeral=True)
             except discord.InteractionResponded: pass
        except Exception as e:
            print(f"Erro geral no comando /sync_config para servidor {interaction.guild_id}: {e}")
            traceback.print_exc()
            try:
                await interaction.followup.send(f"❌ Ocorreu um erro inesperado durante a sincronização.", ephemeral=True)
            except (discord.NotFound, discord.InteractionResponded):
                 try:
                      await interaction.response.send_message(f"❌ Ocorreu um erro inesperado durante a sincronização.", ephemeral=True)
                 except discord.InteractionResponded:
                      pass


async def setup(bot: commands.Bot):
    """Adiciona o Cog ao bot."""
    # A injeção é feita pelo carregador_cogs.py
    pass