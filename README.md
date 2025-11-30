# 🤖 Jarvis - Planejador Financeiro

Assistente financeiro conversacional inteligente desenvolvido com arquitetura multi-agente, utilizando LangGraph para orquestração e Google Gemini (LLM) para processamento de linguagem natural. O bot funciona no Telegram e permite que usuários gerenciem seus gastos através de conversas naturais em português.

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Arquitetura](#-arquitetura)
- [Estrutura de Arquivos](#-estrutura-de-arquivos)
- [Agentes](#-agentes)
- [Tools](#-tools)
- [Banco de Dados](#-banco-de-dados)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Scripts Utilitários](#-scripts-utilitários)
- [Desenvolvimento](#-desenvolvimento)

---

## ✨ Funcionalidades

### Funcionalidades Principais

1. **Registro de Gastos**
   - Registro de gastos através de linguagem natural
   - Exemplos: "gastei 50 reais no mercado", "paguei 30 de uber"
   - Extração automática de valor, categoria e descrição usando LLM

2. **Consulta de Gastos**
   - Consulta de gastos por período (hoje, semana, mês)
   - Consulta por categoria
   - Resumo geral de gastos

3. **Gestão de Categorias**
   - Criação de categorias personalizadas
   - Listagem de categorias cadastradas
   - Remoção de categorias (quando não há transações associadas)

4. **Limites de Gastos**
   - Definição de limites por categoria e período (mensal, semanal)
   - Verificação automática de limites ao registrar gastos
   - Alertas quando limite é excedido ou próximo de ser excedido

5. **Setup Inicial Guiado**
   - Fluxo guiado para novos usuários
   - Criação de categorias padrão
   - Configuração opcional de limites iniciais

6. **Tratamento de Ambiguidades**
   - Identificação inteligente de informações faltantes
   - Esclarecimento automático quando necessário
   - Processamento flexível com suposições razoáveis

7. **Histórico de Conversas**
   - Armazenamento de todas as interações
   - Contexto mantido para melhor compreensão

---

## 🛠️ Tecnologias

### Stack Principal

- **Python 3.11+**: Linguagem de programação principal
- **LangGraph**: Orquestração de agentes multi-agente
- **Google Gemini (LLM)**: Processamento de linguagem natural
  - Suporte para Gemini API direta e Vertex AI
- **Telegram Bot API**: Interface de mensageria
- **SQLite**: Banco de dados relacional local
- **uv**: Gerenciador de pacotes e ambientes virtuais Python

### Dependências Principais

```toml
python-telegram-bot==20.7      # Cliente Telegram Bot API
langgraph>=0.2.0                # Orquestração de agentes
langchain-core>=0.3.0          # Componentes base do LangChain
google-generativeai==0.3.2     # Gemini API direta
google-cloud-aiplatform>=1.115.0  # Vertex AI (alternativa)
pandas>=2.3.3                  # Manipulação de dados
python-dotenv==1.0.0           # Variáveis de ambiente
```

### Ferramentas de Desenvolvimento

- `ipykernel>=7.1.0`: Kernel Jupyter para notebooks
- `jupyter>=1.1.1`: Jupyter Notebook para análise

---

## 🏗️ Arquitetura

### Visão Geral

O sistema utiliza uma **arquitetura multi-agente** baseada em LangGraph, onde diferentes agentes especializados processam mensagens do usuário de forma sequencial e coordenada.

### Fluxo de Processamento

```
Mensagem do Telegram
    ↓
[PartnerAgent] - Validação de segurança e filtro inicial
    ↓
[RouterAgent] - Análise e roteamento inteligente usando LLM
    ↓
    ├──→ [FinanceAgent] - Processamento de operações financeiras
    ├──→ [SetupAgent] - Configuração inicial guiada
    └──→ [ClarificationNode] - Esclarecimento de ambiguidades
    ↓
[OutputAgent] - Validação e formatação final da resposta
    ↓
Resposta para o usuário
```

### Componentes Principais

1. **Input Layer** (Camada de Entrada)
   - `PartnerAgent`: Validação de segurança e sanitização de mensagens

2. **Routing Layer** (Camada de Roteamento)
   - `RouterAgent`: Análise inteligente com LLM para decidir o próximo agente

3. **Core Functionalities** (Funcionalidades Principais)
   - `FinanceAgent`: Operações financeiras (registro, consulta, limites)
   - `SetupAgent`: Configuração inicial guiada para novos usuários

4. **Output Layer** (Camada de Saída)
   - `OutputAgent`: Validação e formatação final das respostas

5. **Shared Tools** (Ferramentas Compartilhadas)
   - `SQLTool`: Interface para operações no banco de dados
   - `FormatterTool`: Formatação de valores monetários e mensagens

### Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                              │
│  [PartnerAgent] ──→ [RouterAgent]                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              CORE FUNCTIONALITIES                           │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ SetupAgent   │      │ FinanceAgent │                    │
│  └──────────────┘      └──────────────┘                    │
│         │                    │                              │
│         └────────────────────┴──────────────┐              │
└─────────────────────────────────────────────┼──────────────┘
                                              │
┌─────────────────────────────────────────────┼──────────────┐
│              SHARED TOOLS                   │              │
│  ┌──────────────┐      ┌──────────────┐    │              │
│  │   SQLTool    │      │ FormatterTool│    │              │
│  └──────────────┘      └──────────────┘    │              │
└─────────────────────────────────────────────┴──────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                             │
│                    [OutputAgent]                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Arquivos

```
jarvis-planejador-financeiro/
│
├── agents/                      # Agentes do sistema
│   ├── __init__.py
│   ├── base_agent.py           # Classe base abstrata para todos os agentes
│   ├── partner_agent.py        # Validação de segurança (gateway)
│   ├── router_agent.py         # Roteamento inteligente usando LLM
│   ├── finance_agent.py        # Operações financeiras
│   ├── setup_agent.py          # Configuração inicial guiada
│   └── output_agent.py         # Validação e formatação final
│
├── tools/                       # Ferramentas compartilhadas
│   ├── __init__.py
│   ├── sql_tool.py             # Interface para operações no banco de dados
│   └── formatter_tool.py       # Formatação de valores e mensagens
│
├── graph/                       # Orquestração LangGraph
│   ├── __init__.py
│   ├── state.py                # Estado compartilhado (GraphState)
│   └── workflow.py             # Definição do grafo e nós
│
├── database/                    # Gerenciamento do banco de dados
│   ├── __init__.py
│   └── models.py               # Schema e inicialização do banco
│
├── notebooks/                   # Notebooks Jupyter para análise
│   └── db_check.ipynb          # Inspeção do banco de dados
│
├── bot.py                      # Arquivo principal - inicializa o bot
├── llm_client.py               # Cliente unificado para Gemini API e Vertex AI
├── config.py                   # Configurações globais do projeto
│
├── clear_database.py           # Script utilitário: limpar banco de dados
├── populate_test_cases.py      # Script utilitário: popular dados de teste
│
├── jarvis.db                   # Banco de dados SQLite (gerado automaticamente)
├── .env                        # Variáveis de ambiente (não versionado)
├── pyproject.toml              # Configuração do projeto e dependências
├── uv.lock                     # Lock file das dependências
└── README.md                   # Este arquivo
```

---

## 🤖 Agentes

### 1. PartnerAgent

**Responsabilidade**: Gateway de segurança e validação inicial

**Funcionalidades**:
- Valida tamanho da mensagem (máximo 2000 caracteres)
- Bloqueia conteúdo malicioso (SQL injection, XSS)
- Limpa e normaliza mensagens (remove espaços extras)
- Detecta novos usuários e inicia setup automaticamente

**Localização**: `agents/partner_agent.py`

**Fluxo**:
```
Mensagem recebida → Validação → Mensagem limpa ou erro
```

---

### 2. RouterAgent

**Responsabilidade**: Roteamento inteligente usando LLM

**Funcionalidades**:
- Analisa mensagem com LLM para detectar intenção
- Identifica ambiguidades que precisam esclarecimento
- Decide qual agente deve processar (FinanceAgent, SetupAgent, ou ClarificationNode)
- Mantém contexto do usuário (setup em andamento, etc.)

**Intenções detectadas**:
- `REGISTRO`: Registrar gasto
- `CONSULTA`: Ver gastos
- `CONSULTA_LIMITES`: Ver limites configurados
- `ADICIONAR_CATEGORIA`: Criar nova categoria
- `SETUP`: Configurar sistema
- `AJUDA`: Pedido de ajuda
- `FORA_ESCOPO`: Não relacionado a finanças

**Localização**: `agents/router_agent.py`

---

### 3. FinanceAgent

**Responsabilidade**: Processamento de operações financeiras

**Funcionalidades**:
- Registro de gastos com extração automática de informações
- Consulta de gastos por período e categoria
- Gerenciamento de categorias (criar, listar, remover)
- Consulta e gerenciamento de limites de gastos
- Verificação automática de limites ao registrar gastos
- Tratamento de ambiguidades com esclarecimento inteligente

**Operações suportadas**:
- `insert_transaction`: Registrar novo gasto
- `get_transactions`: Consultar transações
- `get_spending_by_category`: Resumo por categoria
- `create_category`: Criar categoria
- `get_active_rules`: Consultar limites ativos
- `create_limit_rule`: Criar limite de gasto

**Localização**: `agents/finance_agent.py`

---

### 4. SetupAgent

**Responsabilidade**: Configuração inicial guiada para novos usuários

**Funcionalidades**:
- Fluxo guiado passo a passo usando LLM
- Criação de categorias padrão automaticamente
- Coleta de nome do usuário
- Permite adicionar categorias personalizadas
- Configuração opcional de limites iniciais

**Etapas do Setup**:
1. `start`: Apresentação e início
2. `get_name`: Coleta nome do usuário
3. `categories`: Criação de categorias padrão e opção de adicionar mais
4. `limits`: Configuração opcional de limites
5. `complete`: Conclusão do setup

**Localização**: `agents/setup_agent.py`

---

### 5. OutputAgent

**Responsabilidade**: Validação e formatação final das respostas

**Funcionalidades**:
- Valida se resposta está completa e coerente
- Melhora formatação (emoji, Markdown)
- Garante tom amigável e profissional
- Validação básica de segurança

**Localização**: `agents/output_agent.py`

---

## 🔧 Tools

### SQLTool

**Localização**: `tools/sql_tool.py`

Interface unificada para todas as operações no banco de dados SQLite.

**Métodos Principais**:

- **Gestão de Usuários**:
  - `get_or_create_user()`: Busca ou cria usuário
  - `update_last_message()`: Atualiza timestamp da última mensagem

- **Gestão de Categorias**:
  - `create_category()`: Cria nova categoria
  - `get_user_categories()`: Lista categorias do usuário
  - `get_category_by_name()`: Busca categoria pelo nome
  - `delete_category()`: Remove categoria (se não houver transações)

- **Gestão de Transações**:
  - `insert_transaction()`: Insere nova transação
  - `get_transactions()`: Consulta transações com filtros
  - `get_total_by_category()`: Calcula total gasto em categoria
  - `get_total_by_period()`: Calcula total gasto em período
  - `delete_transaction()`: Remove transação específica

- **Gestão de Limites**:
  - `create_limit_rule()`: Cria regra de limite
  - `get_active_rules()`: Lista limites ativos do usuário
  - `update_rule_total()`: Atualiza total acumulado de limite
  - `delete_limit_rule()`: Remove limite (marca como inactive)

- **Histórico de Conversas**:
  - `save_conversation()`: Salva interação no histórico
  - `get_conversation_history()`: Busca histórico do usuário
  - `clear_conversation_history()`: Limpa histórico (para testes)

**Relacionamentos Utilizados**:
- Todas as queries utilizam relacionamentos entre tabelas via foreign keys
- JOINs entre `transactions` ↔ `categories` para obter nomes de categorias
- JOINs entre `user_rules` ↔ `categories` para informações completas de limites

---

### FormatterTool

**Localização**: `tools/formatter_tool.py`

Ferramenta para formatação padronizada de valores monetários, datas e mensagens.

**Métodos Principais**:

- `format_currency(value)`: Formata valor monetário (ex: R$ 1.234,56)
- `format_date(date, format_type)`: Formata data (curta ou longa)
- `format_datetime(dt)`: Formata data e hora (ex: 25/12/2024 às 14:30)
- `format_percentage(value)`: Formata percentual (ex: 25,5%)
- `format_transaction_list(transactions)`: Formata lista de transações
- `format_category_summary(spending_data)`: Formata resumo por categoria
- `format_limit_alert(...)`: Formata alerta de limite excedido
- `format_comparison(...)`: Formata comparação entre períodos

---

## 💾 Banco de Dados

### Visão Geral

O sistema utiliza **SQLite** como banco de dados relacional local. O arquivo `jarvis.db` é criado automaticamente na raiz do projeto quando o sistema é iniciado pela primeira vez.

### Schema do Banco de Dados

O banco possui **5 tabelas** principais relacionadas entre si através de foreign keys:

```
┌─────────────┐
│    users    │
└─────────────┘
      │
      ├── 1:N ──→ ┌──────────────┐
      │            │  categories  │
      │            └──────────────┘
      │                  │
      │                  ├── 1:N ──→ ┌───────────────┐
      │                  │            │ transactions  │
      │                  │            └───────────────┘
      │                  │
      │                  └── 1:N ──→ ┌──────────────┐
      │                               │  user_rules  │
      │                               └──────────────┘
      │
      └── 1:N ──→ ┌──────────────────────┐
                   │ conversation_history │
                   └──────────────────────┘
```

### Tabelas Detalhadas

#### 1. `users` - Usuários do Sistema

Armazena informações básicas de cada usuário do bot.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `user_phone` | TEXT (PK) | ID único do usuário (telefone ou ID do Telegram) |
| `user_name` | TEXT | Nome do usuário (coletado durante setup) |
| `created_at` | DATETIME | Data/hora de criação do registro (automático) |
| `last_message_at` | DATETIME | Data/hora da última mensagem recebida |
| `setup_step` | TEXT | Etapa atual do setup (NULL = concluído) |

**Relacionamentos**:
- 1:N com `categories` (um usuário pode ter várias categorias)
- 1:N com `transactions` (um usuário pode ter várias transações)
- 1:N com `user_rules` (um usuário pode ter várias regras)
- 1:N com `conversation_history` (um usuário pode ter várias mensagens)

---

#### 2. `categories` - Categorias de Gastos

Armazena categorias personalizadas de gastos criadas por cada usuário.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `category_id` | INTEGER (PK, AI) | ID único da categoria (auto-incremento) |
| `user_phone` | TEXT (FK) | Referência ao usuário (users.user_phone) |
| `category_name` | TEXT | Nome da categoria (ex: "Alimentação") |
| `description` | TEXT | Descrição opcional da categoria |
| `created_at` | DATETIME | Data/hora de criação (automático) |

**Relacionamentos**:
- N:1 com `users` (muitas categorias pertencem a um usuário)
- 1:N com `transactions` (uma categoria pode ter várias transações)
- 1:N com `user_rules` (uma categoria pode ter várias regras)

**Exemplos de categorias**:
- Alimentação
- Transporte
- Lazer
- Moradia
- Saúde

---

#### 3. `transactions` - Transações Financeiras

Armazena todos os gastos registrados pelos usuários.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `transaction_id` | INTEGER (PK, AI) | ID único da transação (auto-incremento) |
| `user_phone` | TEXT (FK) | Referência ao usuário (users.user_phone) |
| `category_id` | INTEGER (FK) | Referência à categoria (categories.category_id) |
| `amount` | REAL | Valor monetário da transação em reais |
| `expense_description` | TEXT | Descrição do gasto |
| `created_at` | DATETIME | Data/hora do registro (automático) |

**Relacionamentos**:
- N:1 com `users` (muitas transações pertencem a um usuário)
- N:1 com `categories` (muitas transações pertencem a uma categoria)

**Exemplo de registro**:
```sql
transaction_id: 1
user_phone: "123456789"
category_id: 2
amount: 50.00
expense_description: "Almoço no restaurante"
created_at: "2024-12-25 14:30:00"
```

---

#### 4. `user_rules` - Regras de Limite de Gastos

Armazena limites de gasto configurados por categoria e período.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `rule_id` | INTEGER (PK, AI) | ID único da regra (auto-incremento) |
| `user_phone` | TEXT (FK) | Referência ao usuário (users.user_phone) |
| `category_id` | INTEGER (FK) | Referência à categoria (categories.category_id) |
| `period_type` | TEXT | Tipo de período ("mensal", "semanal", "diário") |
| `period_start` | DATETIME | Data/hora de início do período atual |
| `period_end` | DATETIME | Data/hora de fim do período (opcional, NULL = dinâmico) |
| `limit_value` | REAL | Valor máximo permitido em reais |
| `current_total` | REAL | Total atual gasto no período |
| `last_updated` | DATETIME | Data/hora da última atualização do total |
| `active` | INTEGER | Se está ativa (1) ou desativada (0) |

**Relacionamentos**:
- N:1 com `users` (muitas regras pertencem a um usuário)
- N:1 com `categories` (muitas regras podem ser para uma categoria)

**Exemplo de regra**:
```sql
rule_id: 1
user_phone: "123456789"
category_id: 3
period_type: "mensal"
limit_value: 500.00
current_total: 320.50
active: 1
```

**Funcionamento**:
- Ao registrar uma nova transação, `current_total` é atualizado automaticamente
- Sistema verifica se `current_total >= limit_value` e gera alerta
- No início de um novo período, `current_total` e `period_start` são resetados

---

#### 5. `conversation_history` - Histórico de Conversas

Armazena mensagens do usuário e respostas do bot para manter contexto e análise.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `message_id` | INTEGER (PK, AI) | ID único da mensagem (auto-incremento) |
| `user_phone` | TEXT (FK) | Referência ao usuário (users.user_phone) |
| `user_message` | TEXT | Mensagem enviada pelo usuário |
| `bot_response` | TEXT | Resposta gerada pelo bot |
| `created_at` | DATETIME | Data/hora da mensagem (automático) |

**Relacionamentos**:
- N:1 com `users` (muitas mensagens pertencem a um usuário)

**Índice**:
- `idx_conversation_user_date`: Índice composto em (user_phone, created_at DESC) para otimizar consultas de histórico

---

### Relacionamentos e Cardinalidades

| Relacionamento | Tipo | Foreign Key |
|----------------|------|-------------|
| `users` → `categories` | 1:N | `categories.user_phone` → `users.user_phone` |
| `users` → `transactions` | 1:N | `transactions.user_phone` → `users.user_phone` |
| `users` → `user_rules` | 1:N | `user_rules.user_phone` → `users.user_phone` |
| `users` → `conversation_history` | 1:N | `conversation_history.user_phone` → `users.user_phone` |
| `categories` → `transactions` | 1:N | `transactions.category_id` → `categories.category_id` |
| `categories` → `user_rules` | 1:N | `user_rules.category_id` → `categories.category_id` |

### Queries Exemplos

#### Buscar transações com nome da categoria:
```sql
SELECT 
    t.transaction_id,
    t.amount,
    t.expense_description,
    c.category_name
FROM transactions t
LEFT JOIN categories c ON t.category_id = c.category_id
WHERE t.user_phone = ?
ORDER BY t.created_at DESC
```

#### Calcular gastos por categoria:
```sql
SELECT 
    c.category_name,
    SUM(t.amount) as total_amount,
    COUNT(t.transaction_id) as transaction_count
FROM categories c
LEFT JOIN transactions t ON c.category_id = t.category_id
WHERE c.user_phone = ?
GROUP BY c.category_id, c.category_name
ORDER BY total_amount DESC
```

#### Buscar limites ativos com nome da categoria:
```sql
SELECT 
    r.rule_id,
    c.category_name,
    r.limit_value,
    r.current_total
FROM user_rules r
JOIN categories c ON r.category_id = c.category_id
WHERE r.user_phone = ? AND r.active = 1
```

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.11 ou superior
- `uv` instalado ([veja como instalar](https://github.com/astral-sh/uv))
- Conta no Telegram (pode ser do celular)
- Chave de API do Google Gemini (obtenha em [Google AI Studio](https://makersuite.google.com/app/apikey))

### Passo a Passo

#### 1. Criar o Bot no Telegram

Para usar o Jarvis no seu próprio celular, você precisa criar um bot no Telegram e obter o token:

1. **Abra o Telegram no seu celular ou computador**

2. **Procure pelo BotFather**:
   - No app do Telegram, use a barra de busca e procure por `@BotFather`
   - Ou acesse diretamente: [t.me/BotFather](https://t.me/BotFather)

3. **Inicie uma conversa com o BotFather**:
   - Clique em "Start" ou envie `/start` para iniciar

4. **Crie um novo bot**:
   - Envie o comando `/newbot`
   - O BotFather pedirá um **nome** para o bot (ex: "Meu Assistente Financeiro")
   - Em seguida, pedirá um **username** único que termine com `bot` (ex: `meu_assistente_financeiro_bot`)

5. **Copie o token**:
   - Após criar o bot, o BotFather enviará uma mensagem com o token
   - O token tem o formato: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - **Guarde este token com segurança** - você precisará dele na configuração

6. **Opcional - Personalizar o bot**:
   - Você pode usar `/setdescription` para adicionar uma descrição
   - Use `/setabouttext` para adicionar um texto "Sobre"
   - Use `/setuserpic` para adicionar uma foto de perfil

7. **Teste o bot**:
   - Procure pelo seu bot pelo username no Telegram (ex: `@meu_assistente_financeiro_bot`)
   - Inicie uma conversa clicando em "Start"
   - O bot ainda não responderá - isso é normal! Você precisa rodar o código primeiro.

**Importante**: 
- O token do bot é confidencial. Não compartilhe publicamente.
- Com o token, qualquer pessoa pode controlar seu bot.
- Se suspeitar que o token foi comprometido, use `/revoke` no BotFather para gerar um novo.

#### 2. Clone o repositório

```bash
git clone <url-do-repositório>
cd jarvis-planejador-financeiro
```

#### 3. Instale as dependências usando `uv`

```bash
uv sync
```

Isso irá:
- Criar um ambiente virtual Python
- Instalar todas as dependências do projeto
- Gerar o arquivo `uv.lock`

#### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env  # Se houver um arquivo de exemplo
# Ou crie manualmente o arquivo .env
```

Edite o arquivo `.env` e adicione:

```env
# Token do bot do Telegram (obrigatório)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# Chave da API do Google Gemini (obrigatório)
GEMINI_API_KEY=sua_chave_aqui

# ID do projeto Google Cloud (opcional, apenas para Vertex AI)
GOOGLE_CLOUD_PROJECT=seu-project-id

# Modelo do Gemini a usar (opcional, padrão: gemini-2.5-flash)
GEMINI_MODEL=gemini-2.5-flash

# Caminho do banco de dados (opcional, padrão: jarvis.db)
DATABASE_PATH=jarvis.db
```

**Onde obter as chaves**:

- **TELEGRAM_BOT_TOKEN**: Token que você copiou do BotFather (passo 1 acima)
- **GEMINI_API_KEY**: 
  - Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Faça login com sua conta Google
  - Clique em "Get API Key" ou "Criar chave"
  - Copie a chave gerada (formato: `AIza...`)

#### 5. Inicialize o banco de dados
O banco será criado automaticamente na primeira execução. Mas você pode popular com dados de teste:

```bash
uv run python populate_test_cases.py
```

---

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `TELEGRAM_BOT_TOKEN` | Sim | Token do bot obtido em [@BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | Sim | Chave de API do Google Gemini (formato: `AIza...` ou `AQ...`) |
| `GOOGLE_CLOUD_PROJECT` | Não* | ID do projeto Google Cloud (necessário apenas para Vertex AI) |
| `GEMINI_MODEL` | Não | Nome do modelo (padrão: `gemini-2.5-flash`) |
| `DATABASE_PATH` | Não | Caminho do arquivo SQLite (padrão: `jarvis.db`) |
| `DEBUG` | Não | Ativar modo debug (padrão: `False`) |
| `LOG_LEVEL` | Não | Nível de log (padrão: `INFO`) |

\* Necessário apenas se usar Vertex AI ao invés de Gemini API direta.

### Escolhendo entre Gemini API e Vertex AI

O sistema detecta automaticamente qual usar baseado na chave:

- **Gemini API Direta**: Chaves começando com `AIza...`
  - Mais simples de configurar
  - Não requer Google Cloud
  - Ideal para desenvolvimento e testes

- **Vertex AI**: Chaves começando com `AQ...` ou com `GOOGLE_CLOUD_PROJECT` configurado
  - Requer Google Cloud Project configurado
  - Requer autenticação (`gcloud auth application-default login`)
  - Ideal para produção com recursos avançados

---

## 💻 Uso

### Iniciar o Bot

```bash
uv run python bot.py
```

O bot iniciará e ficará escutando mensagens do Telegram. Você verá logs no console indicando o status:

```
🤖 Iniciando bot do Telegram...
✅ Bot rodando! Pressione Ctrl+C para parar.
```

**Importante**: 
- O bot precisa estar rodando para receber e responder mensagens
- Enquanto o bot estiver rodando, ele processará todas as mensagens enviadas a ele
- Para parar o bot, pressione `Ctrl+C` no terminal

### Usando o Bot no Seu Celular

Após iniciar o bot no computador, você pode usá-lo normalmente no Telegram do seu celular:

1. **Abra o Telegram no celular**

2. **Procure pelo seu bot**:
   - Use a barra de busca e digite o username do bot que você criou (ex: `@meu_assistente_financeiro_bot`)
   - Ou procure na lista de conversas se já tiver iniciado antes

3. **Inicie uma conversa**:
   - Clique no bot e depois em "Start" ou envie `/start`
   - O bot responderá com uma mensagem de boas-vindas

4. **Comece a usar**:
   - Envie mensagens em linguagem natural como: "gastei 50 reais no mercado"
   - O bot processará e responderá automaticamente
   - Todas as mensagens são processadas pelo código rodando no seu computador

**Dicas**:
- O bot funciona enquanto o programa `bot.py` estiver rodando no computador
- Se o computador desligar ou o programa parar, o bot não responderá até você iniciá-lo novamente
- Você pode usar o bot em qualquer dispositivo Telegram (celular, tablet, desktop) - todos conversam com o mesmo bot

### Comandos Disponíveis

- `/start`: Mensagem de boas-vindas e apresentação do bot

### Exemplos de Uso

#### Registrar Gastos
```
Usuário: "gastei 50 reais no mercado"
Bot: ✅ Gasto registrado: R$ 50,00 em Alimentação - mercado

Usuário: "paguei 30 de uber"
Bot: ✅ Gasto registrado: R$ 30,00 em Transporte - uber
```

#### Consultar Gastos
```
Usuário: "quanto gastei hoje?"
Bot: 📊 Você gastou R$ 85,00 hoje...

Usuário: "resumo dos meus gastos"
Bot: 📋 Resumo dos seus gastos...
```

#### Gerenciar Categorias
```
Usuário: "adicionar categoria Pets"
Bot: ✅ Categoria "Pets" criada com sucesso!

Usuário: "minhas categorias"
Bot: 📁 Suas categorias:
  • Alimentação
  • Transporte
  • Lazer
  ...
```

#### Configurar Limites
```
Usuário: "limite de 500 reais em transporte por mês"
Bot: ✅ Limite configurado: R$ 500,00 em Transporte (mensal)
```

---

## 🛠️ Scripts Utilitários

### `clear_database.py`

Script para limpar todos os dados do banco de dados mantendo a estrutura das tabelas.

**Uso**:
```bash
# Com confirmação interativa
uv run python clear_database.py

# Sem confirmação (automático)
uv run python clear_database.py --yes
```

**O que faz**:
- Remove todos os registros de todas as tabelas
- Reseta contadores de auto-incremento
- Mantém a estrutura das tabelas intacta

**Tabelas limpas**:
- `conversation_history`
- `user_rules`
- `transactions`
- `categories`
- `users`

---

### `populate_test_cases.py`

Script para popular o banco de dados com dados de teste que demonstram todas as funcionalidades.

**Uso**:
```bash
# Com user_id padrão (123456789)
uv run python populate_test_cases.py

# Com user_id customizado
uv run python populate_test_cases.py <user_id>
```

**O que cria**:
- 1 usuário de teste
- 6 categorias padrão (Alimentação, Transporte, Lazer, Moradia, Saúde, Delivery)
- Múltiplas transações distribuídas em diferentes períodos
- 3 limites configurados (para testar alertas)

**Útil para**:
- Testar funcionalidades rapidamente
- Demonstrar o sistema
- Desenvolvimento e debugging

---

## 🔨 Desenvolvimento

### Estrutura do Código

O código segue uma arquitetura modular:

- **Agentes**: Lógica de processamento especializada
- **Tools**: Ferramentas reutilizáveis
- **Graph**: Orquestração do fluxo
- **Database**: Camada de persistência

### Adicionando Novos Agentes

1. Crie um novo arquivo em `agents/` herdando de `BaseAgent`:
```python
from agents.base_agent import BaseAgent

class MeuAgent(BaseAgent):
    def __init__(self):
        super().__init__("MeuAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Sua lógica aqui
        return {"response": "OK"}
```

2. Adicione o nó no `graph/workflow.py`
3. Configure o roteamento no `RouterAgent`

### Adicionando Novas Tools

1. Adicione métodos estáticos em `SQLTool` ou `FormatterTool`
2. Importe e use nos agentes necessários

### Debugging

- Logs aparecem no console com formato: `[HH:MM:SS] [NomeDoAgente] LEVEL: mensagem`
- Use `self.log()` nos agentes para adicionar logs
- Erros são capturados e mensagens genéricas são enviadas ao usuário

### Testando

1. Use `populate_test_cases.py` para criar dados de teste
2. Execute o bot e teste via Telegram
3. Use `db_check.ipynb` para inspecionar o banco de dados


