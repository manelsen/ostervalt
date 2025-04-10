# Ostervalt - Bot Discord para RPG em Julia

Este projeto implementa o Ostervalt, um bot para Discord desenvolvido em Julia, focado em funcionalidades para mesas de RPG. Ele gerencia personagens, economia (Marcos e moedas), inventários, loja e permissões.

## Funcionalidades Principais

*   **Gerenciamento de Personagens:** Criação, progressão (níveis e Marcos), inventário e saldo.
*   **Economia:** Sistema de moedas, trabalho, crimes (com risco/recompensa) e transferências (PIX).
*   **Loja:** Estoque de itens com raridades, compra e venda (gerenciamento via comandos de admin).
*   **Permissões:** Cargos especiais para controle de acesso a comandos administrativos.
*   **Persistência:** Dados salvos por servidor em arquivos JSON.
*   **Configuração:** Configurações gerais (limites, progressão, mensagens) via `config.yaml`.
*   **Cache:** Cache para otimizar leitura de dados do servidor.

## Estrutura do Projeto

*   `ostervalt.jl`: Código principal do bot.
*   `config.yaml`: Arquivo de configuração principal.
*   `items.csv` (ou `items_<server_id>.csv`): Arquivo CSV com a lista de itens disponíveis para a loja.
*   `server_data_<server_id>.json`: Arquivos JSON gerados para armazenar os dados de cada servidor (personagens, estoque, etc.).
*   `.env`: Arquivo para variáveis de ambiente (TOKEN, APPLICATION_ID, etc.).
*   `memory-bank/`: Diretório contendo arquivos de contexto e progresso do projeto (gerenciado pelo assistente).
*   `PLANO_DOCUMENTACAO_OSTERVALT.md`: Plano detalhado de documentação gerado durante o desenvolvimento.

## Comandos Principais (Usuário)

*   `/criar <nome>`: Cria um novo personagem.
*   `/ajuda`: Mostra a lista de comandos disponíveis.
*   `/marcos <personagem>`: Mostra os Marcos e nível do personagem.
*   `/mochila <personagem> [item]`: Lista o inventário ou detalha um item específico.
*   `/comprar <personagem> <item>`: Compra um item da loja.
*   `/saldo <personagem>`: Mostra o saldo de moedas do personagem.
*   `/pix <de_personagem> <para_personagem> <quantidade>`: Transfere moedas entre personagens.
*   `/trabalhar <personagem>`: Realiza a ação de trabalho para ganhar moedas.
*   `/crime <personagem>`: Tenta realizar um crime (com risco/recompensa).
*   `/loja`: Mostra os itens disponíveis na loja.

## Comandos Administrativos

*   `/up <personagem>`: Adiciona Marcos a um personagem (requer permissão).
*   `/dinheiro <personagem> <quantidade>`: Adiciona/remove moedas do saldo (requer permissão).
*   `/cargos <tipo> <acao> <cargo>`: Gerencia cargos especiais para permissões (requer permissão de admin).
*   `/estoque <comum> <incomum> <raro> <muito_raro>`: Gera um novo estoque para a loja (requer permissão).
*   `/inserir <raridade> <item> <quantidade> [valor]`: Insere um item específico no estoque (requer permissão).
*   `/remover <item> [quantidade]`: Remove um item do estoque (requer permissão).
*   `/limpar_estoque`: Limpa completamente o estoque da loja (requer permissão).
*   `/backup`: Cria um backup dos dados do servidor (requer permissão de admin).
*   `/mensagens <tipo> <mensagem>`: Adiciona mensagens personalizadas para eventos (requer permissão de admin).
*   `/tiers <tier> <nivel_min> <nivel_max> <recompensa>`: Configura os tiers de níveis (requer permissão de admin).
*   `/probabilidade_crime <probabilidade>`: Define a probabilidade de sucesso no crime (requer permissão).
*   `/rip <personagem>`: Remove um personagem permanentemente (requer permissão).
*   `/inss <personagem>`: Aposenta um personagem (requer permissão).

## Instalação e Configuração

*(Seção a ser detalhada com dependências Julia, processo de build/run e configuração do .env)*

1.  Clone o repositório.
2.  Instale as dependências Julia listadas no `using` no início do `ostervalt.jl`.
3.  Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
    *   `DISCORD_TOKEN`: Token do seu bot Discord.
    *   `APPLICATION_ID`: ID da aplicação do seu bot Discord.
    *   `GUILD`: ID do servidor principal (opcional, para registro rápido de comandos).
    *   `DATABASE_URL` (se aplicável, atualmente não usado diretamente no código mostrado).
    *   `LOG_LEVEL` (opcional, padrão INFO).
4.  Crie o arquivo `config.yaml` com as configurações desejadas (limites, progressão, mensagens padrão, etc.).
5.  Crie o arquivo `items.csv` com a lista de itens (colunas: Name, Rarity, Text).
6.  Execute o bot com `julia ostervalt.jl`.

## Sugestões de Modularização/Refatoração (Futuro)

*   Separar handlers de comandos em módulos/arquivos distintos (ex: `handlers/economy.jl`, `handlers/admin.jl`).
*   Criar um módulo dedicado para persistência de dados (`data_manager.jl`) encapsulando `load_server_data` e `save_server_data`.
*   Criar um módulo para utilitários (`utils.jl`) contendo funções como `calculate_level`, `format_marcos`, `check_permissions`, `get_tier`.
*   Considerar o uso de um banco de dados (como PostgreSQL via `DATABASE_URL`) em vez de arquivos JSON para melhor escalabilidade e gerenciamento de dados concorrentes.
*   Implementar testes unitários para as funções principais.