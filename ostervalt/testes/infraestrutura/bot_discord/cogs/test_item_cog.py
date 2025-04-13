import pytest
from unittest.mock import AsyncMock, MagicMock
from ostervalt.infraestrutura.bot_discord.cogs.item_cog import ItemCog
from discord.ext import commands # Import necessário
from ostervalt.nucleo.casos_de_uso.obter_item import ObterItem       # Import necessário
from ostervalt.nucleo.casos_de_uso.listar_itens import ListarItens     # Import necessário
from ostervalt.nucleo.casos_de_uso.dtos import ItemDTO, ListaItensDTO # Importar DTOs

@pytest.mark.asyncio
async def test_ver_item_info_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_obter_item = AsyncMock(spec=ObterItem)
    # Retornar um DTO válido (sem o campo 'tipo')
    item_dto_mock = ItemDTO(id=1, nome="Espada Curta", descricao="Uma espada simples.", raridade="comum", valor=50)
    caso_uso_obter_item.executar.return_value = item_dto_mock
    caso_uso_listar_itens = AsyncMock(spec=ListarItens) # Mock para o segundo argumento
    caso_uso_listar_itens = AsyncMock(spec=ListarItens) # Mock para o segundo argumento
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = ItemCog(bot_mock, obter_item_uc=caso_uso_obter_item, listar_itens_uc=caso_uso_listar_itens) # bot como primeiro argumento posicional
    await cog.ver_item_info.callback(cog, interaction, item_id=1) # Chamar o callback do comando
    # Verificar followup.send pois defer foi usado
    assert interaction.followup.send.called

@pytest.mark.asyncio
async def test_ver_loja_sucesso():
    interaction = AsyncMock()
    interaction.user.id = 123
    interaction.response = AsyncMock()
    caso_uso_listar_itens = AsyncMock(spec=ListarItens)
    # Corrigir valor de retorno para ser um ListaItensDTO
    item1_dto = ItemDTO(id=1, nome="item1", descricao="desc1", raridade="comum", valor=10)
    item2_dto = ItemDTO(id=2, nome="item2", descricao="desc2", raridade="incomum", valor=20)
    caso_uso_listar_itens.executar.return_value = ListaItensDTO(itens=[item1_dto, item2_dto])
    caso_uso_obter_item = AsyncMock(spec=ObterItem) # Mock para o primeiro argumento
    caso_uso_obter_item = AsyncMock(spec=ObterItem) # Mock para o primeiro argumento
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    bot_mock = AsyncMock(spec=commands.Bot) # Mock do bot
    cog = ItemCog(bot_mock, obter_item_uc=caso_uso_obter_item, listar_itens_uc=caso_uso_listar_itens) # bot como primeiro argumento posicional
    await cog.ver_loja.callback(cog, interaction) # Chamar o callback do comando
    # Verificar followup.send pois defer foi usado
    assert interaction.followup.send.called