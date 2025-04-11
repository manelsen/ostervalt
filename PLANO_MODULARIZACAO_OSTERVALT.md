# Plano Analítico de Modularização e Extração de Funcionalidades - ostervalt.jl

## 1. Diagnóstico Atual

- O arquivo `ostervalt.jl` possui mais de 2200 linhas, com múltiplas responsabilidades misturadas.
- Os módulos em `src/` cobrem menos de 30% do código original.
- Diversos handlers, funções auxiliares, integrações, utilitários e lógica de inicialização ainda não foram extraídos.

---

## 2. Funções e Blocos NÃO Extraídos (por categoria)

### 2.1. Handlers de Comandos Discord (slash commands)

- **Handlers não extraídos ou incompletos:**
  - handler_comando_criar (duplicidade e lógica incompleta)
  - handler_comando_ajuda (mensagem de ajuda parcial)
  - handler_comando_up (lógica de progressão e integração)
  - handler_comando_marcos
  - handler_comando_mochila (inventário, descrição de item)
  - handler_comando_comprar (integração com estoque)
  - handler_comando_dinheiro (operações de saldo)
  - handler_comando_saldo
  - handler_comando_pix (transferência entre personagens)
  - handler_comando_trabalhar (recompensa, limites)
  - handler_comando_crime (probabilidade, penalidades)
  - handler_comando_cargos (gestão de permissões)
  - handler_comando_estoque (abastecimento, CSV, preços)
  - handler_comando_loja (exibição de itens)
  - handler_comando_inserir (inserção de item)
  - handler_comando_remover (remoção de item)
  - limpar_handler_comando_estoque
  - handler_comando_backup (exportação de dados)
  - handler_comando_mensagens (mensagens customizadas)
  - handler_comando_tiers (configuração de tiers)
  - prob_handler_comando_crime (probabilidade de crime)
  - handler_comando_rip (remoção de personagem)
  - handler_comando_inss (aposentadoria de personagem)

### 2.2. Funções Auxiliares e Utilitários

- obter_descricao_item
- criar_personagem (versão correta e completa)
- gerar_mensagem_ajuda
- Funções de manipulação de inventário, saldo, marcos, tiers, permissões, etc.
- Funções de integração com arquivos CSV, JSON, persistência.

### 2.3. Inicialização e Integração

- Função principal de inicialização do bot (start, add_handler, registrar_handlers_comandos)
- Registro dinâmico de comandos (guild e global)
- Handler global de erros (handler_erro_personalizado)
- Funções de integração entre módulos (includes/usings)
- Adaptação de variáveis globais/configuração

### 2.4. Lógica de Backup e Persistência

- backhandler_comando_up (backup de dados)
- Lógica de exportação/importação de JSON
- Lógica de fallback para ostervalt.jl original

### 2.5. Docstrings, Comentários e Padrões

- Docstrings detalhadas para todas as funções
- Comentários explicativos de fluxo e integrações
- Padrão de modularização consistente

---

## 3. Plano Incremental de Extração e Refatoração

### 3.1. Extração de Handlers

- Extrair **cada handler** de comando Discord individualmente para `src/comandos_discord.jl`, garantindo que toda a lógica, validações e integrações estejam completas.
- Garantir que handlers duplicados ou incompletos sejam unificados e revisados.

### 3.2. Funções Auxiliares

- Extrair todas as funções auxiliares (ex: criar_personagem, obter_descricao_item, utilitários de inventário, saldo, tiers, permissões) para módulos apropriados.
- Garantir que dependências entre funções estejam explícitas.

### 3.3. Integração e Inicialização

- Centralizar a inicialização do bot, registro de comandos e handlers em `src/inicializacao.jl`.
- Garantir que includes/usings estejam corretos e não haja dependências circulares.

### 3.4. Backup, Persistência e Utilitários

- Extrair e revisar toda a lógica de backup, exportação/importação de dados.
- Implementar fallback seguro para ostervalt.jl original.

### 3.5. Documentação e Padrões

- Adicionar docstrings e comentários detalhados em todas as funções extraídas.
- Garantir padrão de modularização consistente e fácil manutenção.

---

## 4. Recomendações Finais

- Atualizar o Banco de Memória a cada etapa significativa.
- Documentar explicitamente as dependências e pontos de integração entre módulos.

---

**Este plano serve como roteiro incremental para garantir a modularização completa, segura e sustentável do projeto Ostervalt.**