"""
Gerenciamento do banco de dados SQLite para o Jarvis.

Este módulo fornece funções para:
- Criar e gerenciar conexões com o banco de dados SQLite
- Inicializar o esquema do banco (criar tabelas)
- Operações básicas de persistência

O banco de dados SQLite é usado para armazenar:
- Usuários (users) - informações básicas dos usuários
- Categorias de gastos (categories) - categorias personalizadas por usuário
- Transações financeiras (transactions) - registro de todos os gastos
- Regras de limite de gastos (user_rules) - limites por categoria e período
- Histórico de conversas (conversation_history) - mensagens e respostas para contexto

Todas as operações de banco de dados são feitas através do SQLTool
(em tools/sql_tool.py), que fornece uma interface mais amigável.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Garantir que variáveis de ambiente estejam carregadas (útil em scripts isolados)
# Isso permite que este módulo funcione independentemente de outros módulos
load_dotenv()

# Caminho padrão do banco de dados SQLite
# Pode ser sobrescrito via variável de ambiente DATABASE_PATH
# Padrão: jarvis.db na raiz do projeto
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "jarvis.db"))


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Retorna uma conexão com o banco de dados SQLite.
    
    Esta função é usada por todas as operações de banco de dados no sistema.
    Ela configura a conexão para retornar resultados como dicionários (Row factory),
    facilitando o acesso aos dados.
    
    IMPORTANTE: Sempre use esta função com context manager (with) para garantir
    que a conexão seja fechada corretamente:
        with get_connection() as conn:
            cursor = conn.execute("SELECT ...")
    
    Parameters
    ----------
    db_path: Optional[Path]
        Caminho alternativo para o arquivo SQLite. Se não for informado,
        utiliza o caminho padrão definido em `DATABASE_PATH`.
        Útil para testes ou múltiplos bancos de dados.
    
    Returns
    -------
    sqlite3.Connection
        Conexão configurada com row_factory=sqlite3.Row (permite acesso como dict)
    
    Exemplo
    -------
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()
            for row in rows:
                print(row['user_phone'])  # Acesso como dicionário
    """
    # Usa caminho fornecido ou padrão
    target = Path(db_path) if db_path else DATABASE_PATH
    
    # Cria diretório pai se não existir (útil se db_path for em subdiretório)
    target.parent.mkdir(parents=True, exist_ok=True)
    
    # Cria conexão com o banco
    connection = sqlite3.connect(target)
    
    # Configura row_factory para retornar resultados como dicionários
    # Isso permite acessar colunas por nome: row['user_phone'] em vez de row[0]
    connection.row_factory = sqlite3.Row
    
    return connection


def init_database(db_path: Optional[Path] = None) -> None:
    """
    Cria as tabelas necessárias para o funcionamento do Jarvis.
    
    Esta função deve ser chamada uma vez no início da aplicação (geralmente em bot.py).
    Ela cria todas as tabelas do banco de dados se elas não existirem.
    
    Tabelas criadas (5 tabelas no total):
    
    1. users: Usuários do sistema
       - user_phone (PK): ID único do usuário (telefone ou ID do Telegram)
       - user_name: Nome do usuário
       - created_at: Data de criação do registro
       - last_message_at: Data da última mensagem recebida
       - setup_step: Etapa atual do setup (NULL se concluído)
       Relacionamentos: 1:N com categories, transactions, user_rules, conversation_history
    
    2. categories: Categorias de gastos por usuário
       - category_id (PK): ID único da categoria (AUTOINCREMENT)
       - user_phone (FK): Referência ao usuário (users.user_phone)
       - category_name: Nome da categoria (ex: "Alimentação", "Transporte")
       - description: Descrição da categoria
       - created_at: Data de criação
       Relacionamentos: N:1 com users, 1:N com transactions e user_rules
    
    3. transactions: Transações financeiras (gastos)
       - transaction_id (PK): ID único da transação (AUTOINCREMENT)
       - user_phone (FK): Referência ao usuário (users.user_phone)
       - category_id (FK): Referência à categoria (categories.category_id)
       - amount: Valor da transação em reais (REAL = float)
       - expense_description: Descrição do gasto
       - created_at: Data e hora da transação
       Relacionamentos: N:1 com users e categories
    
    4. user_rules: Regras de limite de gastos
       - rule_id (PK): ID único da regra (AUTOINCREMENT)
       - user_phone (FK): Referência ao usuário (users.user_phone)
       - category_id (FK): Referência à categoria (categories.category_id)
       - period_type: Tipo de período ("mensal", "semanal", "diário")
       - period_start: Início do período
       - period_end: Fim do período (opcional)
       - limit_value: Valor máximo permitido em reais
       - current_total: Total atual gasto no período
       - last_updated: Última atualização
       - active: Se a regra está ativa (1) ou não (0)
       Relacionamentos: N:1 com users e categories
    
    5. conversation_history: Histórico de conversas
       - message_id (PK): ID único da mensagem (AUTOINCREMENT)
       - user_phone (FK): Referência ao usuário (users.user_phone)
       - user_message: Mensagem enviada pelo usuário
       - bot_response: Resposta gerada pelo bot
       - created_at: Data/hora da mensagem
       Relacionamentos: N:1 com users
       Índice: idx_conversation_user_date (user_phone, created_at DESC) para otimização
    
    Parameters
    ----------
    db_path: Optional[Path]
        Caminho alternativo para o banco. Se None, usa DATABASE_PATH.
    
    Exemplo
    -------
        # No início da aplicação
        init_database()
        
        # Ou com caminho customizado
        init_database(Path("test.db"))
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # ========================================================================
        # TABELA: users - Usuários do sistema
        # ========================================================================
        # Propósito: Armazena informações básicas de cada usuário do bot.
        # 
        # Relacionamentos:
        #   - 1:N com categories (um usuário pode ter várias categorias)
        #   - 1:N com transactions (um usuário pode ter várias transações)
        #   - 1:N com user_rules (um usuário pode ter várias regras de limite)
        #   - 1:N com conversation_history (um usuário pode ter várias mensagens)
        #
        # Campos:
        #   - user_phone (TEXT, PK): ID único do usuário. Usado como chave primária.
        #                            Formato: número de telefone ou ID do Telegram
        #   - user_name (TEXT, NULL): Nome do usuário, coletado durante o setup
        #   - created_at (DATETIME): Data/hora de criação do registro (timestamp automático)
        #   - last_message_at (DATETIME, NULL): Data/hora da última mensagem recebida
        #                                       Atualizado a cada interação
        #   - setup_step (TEXT, NULL): Etapa atual do setup guiado do usuário.
        #                              Valores possíveis: "start", "get_name", "categories", "limits"
        #                              NULL = setup concluído
        #
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_phone TEXT PRIMARY KEY,  -- Chave primária: ID único do usuário
                user_name TEXT,               -- Nome do usuário (coletado no setup)
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Data de criação automática
                last_message_at DATETIME,     -- Data da última mensagem (atualizado a cada interação)
                setup_step TEXT               -- Etapa do setup (NULL = concluído)
            )
            """
        )

        # ========================================================================
        # TABELA: categories - Categorias de gastos por usuário
        # ========================================================================
        # Propósito: Armazena categorias personalizadas de gastos criadas por cada usuário.
        #            Cada usuário pode criar suas próprias categorias (ex: "Alimentação", 
        #            "Transporte", "Lazer", etc.) para organizar seus gastos.
        #
        # Relacionamentos:
        #   - N:1 com users (muitas categorias pertencem a um usuário)
        #         Foreign Key: user_phone → users.user_phone
        #   - 1:N com transactions (uma categoria pode ter várias transações)
        #   - 1:N com user_rules (uma categoria pode ter várias regras de limite)
        #
        # Campos:
        #   - category_id (INTEGER, PK, AUTOINCREMENT): ID único da categoria (gerado automaticamente)
        #   - user_phone (TEXT, FK): Referência ao usuário dono da categoria
        #                            Foreign Key para users.user_phone
        #   - category_name (TEXT): Nome da categoria (ex: "Alimentação", "Transporte")
        #                          Único por usuário (mesma categoria pode existir para usuários diferentes)
        #   - description (TEXT, NULL): Descrição opcional da categoria
        #                               Usada para esclarecer o que se encaixa nesta categoria
        #   - created_at (DATETIME): Data/hora de criação da categoria (timestamp automático)
        #
        # Exemplos de uso:
        #   - Usuário cria categoria "Alimentação" durante setup
        #   - Sistema cria categorias padrão para novos usuários
        #   - Usuário pode adicionar novas categorias a qualquer momento
        #
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único (gerado automaticamente)
                user_phone TEXT,                                -- FK para users.user_phone
                category_name TEXT,                             -- Nome da categoria (ex: "Alimentação")
                description TEXT,                               -- Descrição opcional
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Data de criação automática
                FOREIGN KEY (user_phone) REFERENCES users(user_phone)  -- Relacionamento N:1 com users
            )
            """
        )

        # ========================================================================
        # TABELA: transactions - Transações financeiras (gastos)
        # ========================================================================
        # Propósito: Armazena todos os gastos registrados pelos usuários.
        #            Cada transação representa um gasto único vinculado a uma categoria.
        #
        # Relacionamentos:
        #   - N:1 com users (muitas transações pertencem a um usuário)
        #         Foreign Key: user_phone → users.user_phone
        #   - N:1 com categories (muitas transações pertencem a uma categoria)
        #         Foreign Key: category_id → categories.category_id
        #
        # Campos:
        #   - transaction_id (INTEGER, PK, AUTOINCREMENT): ID único da transação (gerado automaticamente)
        #   - user_phone (TEXT, FK): Referência ao usuário que fez o gasto
        #                            Foreign Key para users.user_phone
        #   - category_id (INTEGER, FK): Referência à categoria do gasto
        #                                Foreign Key para categories.category_id
        #                                Pode ser NULL se categoria não foi especificada
        #   - amount (REAL): Valor monetário da transação em reais (R$)
        #                    Tipo REAL permite valores decimais (ex: 45.50)
        #                    Sempre positivo (representa um gasto)
        #   - expense_description (TEXT, NULL): Descrição opcional do gasto
        #                                       Ex: "Almoço no restaurante", "Uber para o trabalho"
        #   - created_at (DATETIME): Data/hora em que a transação foi registrada
        #                            Timestamp automático no momento da inserção
        #                            Usado para consultas por período (hoje, semana, mês)
        #
        # Casos de uso:
        #   - Usuário registra: "gastei 50 reais no mercado"
        #   - Sistema calcula totais por categoria e período
        #   - Consultas de histórico de gastos
        #   - Verificação de limites de gasto
        #
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único (gerado automaticamente)
                user_phone TEXT,                                   -- FK para users.user_phone
                category_id INTEGER,                               -- FK para categories.category_id
                amount REAL,                                       -- Valor monetário (R$)
                expense_description TEXT,                          -- Descrição do gasto
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,     -- Data/hora do registro automática
                FOREIGN KEY (user_phone) REFERENCES users(user_phone),           -- Relacionamento N:1 com users
                FOREIGN KEY (category_id) REFERENCES categories(category_id)     -- Relacionamento N:1 com categories
            )
            """
        )

        # ========================================================================
        # TABELA: user_rules - Regras de limite de gastos
        # ========================================================================
        # Propósito: Permite que usuários definam limites de gasto por categoria e período.
        #            O sistema verifica automaticamente se o limite foi excedido e gera alertas.
        #            Exemplo: "Máximo de R$ 500 em Transporte por mês"
        #
        # Relacionamentos:
        #   - N:1 com users (muitas regras pertencem a um usuário)
        #         Foreign Key: user_phone → users.user_phone
        #   - N:1 com categories (muitas regras podem ser para uma categoria, mas normalmente 1:1)
        #         Foreign Key: category_id → categories.category_id
        #
        # Campos:
        #   - rule_id (INTEGER, PK, AUTOINCREMENT): ID único da regra (gerado automaticamente)
        #   - user_phone (TEXT, FK): Referência ao usuário dono da regra
        #                            Foreign Key para users.user_phone
        #   - category_id (INTEGER, FK): Referência à categoria que a regra monitora
        #                                Foreign Key para categories.category_id
        #   - period_type (TEXT): Tipo de período do limite
        #                        Valores: "mensal", "semanal", "diário"
        #                        Padrão: "mensal"
        #   - period_start (DATETIME): Data/hora de início do período atual
        #                              Usado para calcular gastos do período
        #                              Padrão: momento da criação da regra
        #   - period_end (DATETIME, NULL): Data/hora de fim do período (opcional)
        #                                  Se NULL, o período é calculado dinamicamente
        #                                  baseado em period_type
        #   - limit_value (REAL): Valor máximo permitido para a categoria no período
        #                         Em reais (R$)
        #                         Ex: 500.00 = limite de R$ 500,00
        #   - current_total (REAL): Total atual gasto na categoria no período atual
        #                           Atualizado automaticamente quando novas transações são criadas
        #                           Comparado com limit_value para verificar excedência
        #                           Padrão: 0.00
        #   - last_updated (DATETIME, NULL): Data/hora da última atualização do current_total
        #                                    Usado para sincronização e debug
        #   - active (INTEGER): Se a regra está ativa (1) ou desativada (0)
        #                       Permite desativar limites temporariamente sem deletar
        #                       Padrão: 1 (ativa)
        #                       Tipo INTEGER para compatibilidade com SQLite (booleano)
        #
        # Fluxo de funcionamento:
        #   1. Usuário cria regra: "Limite de R$ 300 em Lazer por mês"
        #   2. Sistema cria registro com limit_value=300, period_type="mensal"
        #   3. A cada nova transação na categoria, current_total é atualizado
        #   4. Sistema verifica se current_total >= limit_value e gera alerta
        #   5. No início de um novo período, period_start e current_total são resetados
        #
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,        -- ID único (gerado automaticamente)
                user_phone TEXT,                                  -- FK para users.user_phone
                category_id INTEGER,                              -- FK para categories.category_id
                period_type TEXT DEFAULT 'mensal',                -- Tipo de período: "mensal", "semanal", "diário"
                period_start DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Início do período atual
                period_end DATETIME,                              -- Fim do período (NULL = dinâmico)
                limit_value REAL,                                 -- Valor máximo permitido (R$)
                current_total REAL DEFAULT 0,                     -- Total gasto atual no período
                last_updated DATETIME,                            -- Última atualização do total
                active INTEGER DEFAULT 1,                         -- 1=ativa, 0=desativada
                FOREIGN KEY (user_phone) REFERENCES users(user_phone),           -- Relacionamento N:1 com users
                FOREIGN KEY (category_id) REFERENCES categories(category_id)     -- Relacionamento N:1 com categories
            )
            """
        )

        # ========================================================================
        # TABELA: conversation_history - Histórico de conversas
        # ========================================================================
        # Propósito: Armazena mensagens do usuário e respostas do bot para manter contexto
        #            e permitir análise do histórico de interações.
        #
        # Relacionamentos:
        #   - N:1 com users (muitas mensagens pertencem a um usuário)
        #         Foreign Key: user_phone → users.user_phone
        #
        # Campos:
        #   - message_id (INTEGER, PK, AUTOINCREMENT): ID único da mensagem (gerado automaticamente)
        #   - user_phone (TEXT, FK): Referência ao usuário que enviou a mensagem
        #                            Foreign Key para users.user_phone
        #   - user_message (TEXT): Texto da mensagem enviada pelo usuário
        #                          Armazenada para contexto futuro e análise
        #   - bot_response (TEXT): Texto da resposta gerada pelo bot
        #                          Armazenada para contexto e auditoria
        #   - created_at (DATETIME): Data/hora em que a mensagem foi processada
        #                            Timestamp automático
        #                            Usado para ordenar conversas e filtrar por período
        #
        # Casos de uso:
        #   - Manter contexto de conversas anteriores
        #   - Análise de padrões de uso
        #   - Debug de problemas reportados
        #   - Melhoria contínua do sistema
        #
        # Índice: idx_conversation_user_date
        #   - Criado para otimizar consultas por usuário ordenadas por data
        #   - Campos indexados: user_phone, created_at (DESC)
        #   - Melhora performance em consultas do tipo:
        #     "Buscar últimas N mensagens do usuário X ordenadas por data"
        #
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único (gerado automaticamente)
                user_phone TEXT,                               -- FK para users.user_phone
                user_message TEXT,                             -- Mensagem do usuário
                bot_response TEXT,                             -- Resposta do bot
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Data/hora automática
                FOREIGN KEY (user_phone) REFERENCES users(user_phone)  -- Relacionamento N:1 com users
            )
            """
        )

        # Índice composto para otimizar consultas frequentes de histórico por usuário
        # Permite buscar mensagens de um usuário ordenadas por data de forma eficiente
        # Ordem DESC (decrescente) para buscar mensagens mais recentes primeiro
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversation_user_date 
            ON conversation_history(user_phone, created_at DESC)
            """
        )

        # Confirma todas as alterações no banco
        conn.commit()


def save_message(user_phone: str, message_text: str, db_path: Optional[Path] = None) -> None:
    """
    Função de exemplo: salva uma interação simples do usuário.
    
    NOTA: Esta função é um exemplo e não é mais usada no fluxo principal.
    O sistema agora usa SQLTool para todas as operações de banco de dados.
    
    Esta função demonstra como:
    - Garantir que o usuário exista na tabela `users`
    - Atualizar o campo `last_message_at`
    - Registrar a mensagem como uma transação com valor 0 (placeholder)
    
    Parameters
    ----------
    user_phone: str
        ID único do usuário (telefone ou ID do Telegram)
    message_text: str
        Texto da mensagem a ser salva
    db_path: Optional[Path]
        Caminho alternativo para o banco (opcional)
    
    Exemplo
    -------
        save_message("123456789", "gastei 50 reais")
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users (user_phone, user_name, last_message_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_phone) DO UPDATE SET last_message_at=CURRENT_TIMESTAMP
            """,
            (user_phone, None),
        )

        cursor.execute(
            """
            INSERT INTO transactions (user_phone, category_id, amount, expense_description)
            VALUES (?, NULL, ?, ?)
            """,
            (user_phone, 0.0, message_text),
        )

        conn.commit()
