"""SQLTool - Interface para operações no banco de dados."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from database import get_connection


class SQLTool:
    """
    Tool para realizar operações no banco de dados SQLite.
    
    Seguindo os princípios do ReAct e Toolformer, esta classe expõe
    operações de banco de dados como ferramentas utilizáveis pelos agentes.
    """
    
    @staticmethod
    def insert_transaction(
        user_phone: str,
        category_id: int,
        amount: float,
        description: str
    ) -> int:
        """
        Insere uma nova transação no banco de dados.
        
        Cria um registro na tabela transactions que estabelece relacionamentos:
        - transactions (N) → users (1): Via user_phone (FK)
        - transactions (N) → categories (1): Via category_id (FK)
        
        O timestamp created_at é definido automaticamente como CURRENT_TIMESTAMP.
        
        Args:
            user_phone: ID do usuário que fez o gasto (relacionamento com users.user_phone)
            category_id: ID da categoria do gasto (relacionamento com categories.category_id)
            amount: Valor monetário do gasto em reais (float)
            description: Descrição opcional do gasto
        
        Returns:
            ID da transação criada (transaction_id gerado pelo AUTOINCREMENT)
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO transactions 
                   (user_phone, category_id, amount, expense_description, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_phone, category_id, amount, description, datetime.now())
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_user_categories(user_phone: str) -> List[Dict[str, Any]]:
        """
        Retorna todas as categorias de um usuário específico.
        
        Utiliza relacionamento entre tabelas:
        - categories (N) → users (1): Via user_phone (FK)
        
        A query busca categorias que pertencem ao usuário usando o relacionamento
        estabelecido pela foreign key user_phone na tabela categories.
        
        Args:
            user_phone: ID do usuário (relacionamento com users.user_phone)
        
        Returns:
            Lista de dicionários, cada um contendo:
            - category_id: ID único da categoria
            - category_name: Nome da categoria
            - description: Descrição da categoria
            Ordenada alfabeticamente por category_name
        """
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT category_id, category_name, description
                   FROM categories
                   WHERE user_phone = ?
                   ORDER BY category_name""",
                (user_phone,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_category_by_name(user_phone: str, category_name: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma categoria pelo nome.
        
        Returns:
            Dicionário com dados da categoria ou None se não encontrada
        """
        with get_connection() as conn:
            row = conn.execute(
                """SELECT category_id, category_name, description
                   FROM categories
                   WHERE user_phone = ? AND LOWER(category_name) = LOWER(?)""",
                (user_phone, category_name)
            ).fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_total_by_category(
        user_phone: str,
        category_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Calcula o total gasto em uma categoria específica.
        
        Utiliza relacionamentos implícitos:
        - transactions (N) → users (1): Via user_phone (filtro)
        - transactions (N) → categories (1): Via category_id (filtro)
        
        A query agrega (SUM) todas as transações que:
        - Pertencem ao usuário (user_phone)
        - Estão na categoria especificada (category_id)
        - Estão no período opcional (created_at BETWEEN start_date AND end_date)
        
        Args:
            user_phone: ID do usuário (relacionamento com users)
            category_id: ID da categoria (relacionamento com categories)
            start_date: Data inicial para filtrar por período (opcional)
            end_date: Data final para filtrar por período (opcional)
            
        Returns:
            Total gasto (float) na categoria. Retorna 0.0 se não houver transações.
        """
        query = """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_phone = ? AND category_id = ?  -- Filtros pelos relacionamentos com users e categories
        """
        params = [user_phone, category_id]
        
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        
        with get_connection() as conn:
            result = conn.execute(query, params).fetchone()
            return result[0] if result else 0.0
    
    @staticmethod
    def get_total_by_period(
        user_phone: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calcula o total gasto em um período.
        
        Returns:
            Total gasto no período
        """
        with get_connection() as conn:
            result = conn.execute(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM transactions
                   WHERE user_phone = ? AND created_at BETWEEN ? AND ?""",
                (user_phone, start_date, end_date)
            ).fetchone()
            return result[0] if result else 0.0
    
    @staticmethod
    def get_transactions(
        user_phone: str,
        category_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retorna transações com filtros opcionais.
        
        Utiliza relacionamento entre tabelas:
        - LEFT JOIN com categories: Busca o nome da categoria (category_name)
          relacionando transactions.category_id com categories.category_id
        - Filtra por user_phone: Relaciona transações com o usuário
        
        Relacionamentos utilizados:
        - transactions (N) → users (1): Via user_phone
        - transactions (N) → categories (1): Via category_id (LEFT JOIN para incluir transações sem categoria)
        
        Args:
            user_phone: ID do usuário para filtrar transações
            category_id: ID da categoria para filtrar (opcional)
            start_date: Data inicial para filtrar por período (opcional)
            end_date: Data final para filtrar por período (opcional)
            limit: Número máximo de transações a retornar (padrão: 50)
        
        Returns:
            Lista de dicionários com transações, cada um contendo:
            - transaction_id: ID da transação
            - amount: Valor gasto
            - expense_description: Descrição do gasto
            - created_at: Data/hora da transação
            - category_name: Nome da categoria (via JOIN com categories)
        """
        query = """
            SELECT 
                t.transaction_id,
                t.amount,
                t.expense_description,
                t.created_at,
                c.category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id  -- JOIN para obter nome da categoria
            WHERE t.user_phone = ?  -- Filtro pelo relacionamento com users
        """
        params = [user_phone]
        
        if category_id:
            query += " AND t.category_id = ?"
            params.append(category_id)
        
        if start_date:
            query += " AND t.created_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND t.created_at <= ?"
            params.append(end_date)
        
        query += " ORDER BY t.created_at DESC LIMIT ?"
        params.append(limit)
        
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_spending_by_category(
        user_phone: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna gastos agrupados por categoria.
        
        Utiliza relacionamentos entre múltiplas tabelas:
        - LEFT JOIN entre categories e transactions: Agrupa transações por categoria
          usando o relacionamento categories.category_id = transactions.category_id
        - Filtra por user_phone: Relaciona categorias e transações com o usuário
        
        Relacionamentos utilizados:
        - categories (1) → users (1): Via user_phone
        - categories (1) → transactions (N): Via category_id (LEFT JOIN inclui categorias sem transações)
        - transactions (N) → users (1): Via user_phone (implicitamente no filtro)
        
        A query agrupa (GROUP BY) para calcular:
        - Quantidade de transações por categoria (COUNT)
        - Total gasto por categoria (SUM)
        - Média de gastos por categoria (AVG)
        
        Args:
            user_phone: ID do usuário para filtrar categorias e transações
            start_date: Data inicial para filtrar transações por período (opcional)
            end_date: Data final para filtrar transações por período (opcional)
        
        Returns:
            Lista de dicionários com resumo por categoria, cada um contendo:
            - category_name: Nome da categoria
            - category_id: ID da categoria
            - transaction_count: Número de transações na categoria
            - total_amount: Total gasto na categoria (None se não houver transações)
            - avg_amount: Média de gastos por transação na categoria
        """
        query = """
            SELECT 
                c.category_name,
                c.category_id,
                COUNT(t.transaction_id) as transaction_count,
                SUM(t.amount) as total_amount,
                AVG(t.amount) as avg_amount
            FROM categories c
            LEFT JOIN transactions t ON c.category_id = t.category_id  -- JOIN para agrupar transações por categoria
            WHERE c.user_phone = ?  -- Filtro pelo relacionamento categories → users
        """
        params = [user_phone]
        
        if start_date:
            query += " AND (t.created_at IS NULL OR t.created_at >= ?)"
            params.append(start_date)
        
        if end_date:
            query += " AND (t.created_at IS NULL OR t.created_at <= ?)"
            params.append(end_date)
        
        query += " GROUP BY c.category_id, c.category_name ORDER BY total_amount DESC"
        
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def create_category(
        user_phone: str,
        category_name: str,
        description: Optional[str] = None
    ) -> int:
        """
        Cria uma nova categoria para o usuário.
        
        Cria um registro na tabela categories que estabelece relacionamento:
        - categories (N) → users (1): Via user_phone (FK)
        
        O timestamp created_at é definido automaticamente como CURRENT_TIMESTAMP.
        
        Args:
            user_phone: ID do usuário dono da categoria (relacionamento com users.user_phone)
            category_name: Nome da categoria a ser criada (ex: "Alimentação", "Transporte")
            description: Descrição opcional da categoria
        
        Returns:
            ID da categoria criada (category_id gerado pelo AUTOINCREMENT)
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO categories (user_phone, category_name, description)
                   VALUES (?, ?, ?)""",
                (user_phone, category_name, description)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_or_create_user(user_phone: str, user_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Retorna usuário existente ou cria um novo.
        
        Returns:
            Dados do usuário
        """
        with get_connection() as conn:
            # Tenta buscar
            row = conn.execute(
                "SELECT * FROM users WHERE user_phone = ?",
                (user_phone,)
            ).fetchone()
            
            if row:
                return dict(row)
            
            # Se não existe, cria
            conn.execute(
                """INSERT INTO users (user_phone, user_name, created_at, last_message_at)
                   VALUES (?, ?, ?, ?)""",
                (user_phone, user_name, datetime.now(), datetime.now())
            )
            conn.commit()
            
            row = conn.execute(
                "SELECT * FROM users WHERE user_phone = ?",
                (user_phone,)
            ).fetchone()
            return dict(row)
    
    @staticmethod
    def update_last_message(user_phone: str) -> None:
        """Atualiza timestamp da última mensagem do usuário."""
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_message_at = ? WHERE user_phone = ?",
                (datetime.now(), user_phone)
            )
            conn.commit()
    
    @staticmethod
    def create_limit_rule(
        user_phone: str,
        category_id: int,
        period_type: str,
        limit_value: float
    ) -> int:
        """
        Cria uma regra de limite de gasto para uma categoria.
        
        Cria um registro na tabela user_rules que estabelece relacionamentos:
        - user_rules (N) → users (1): Via user_phone (FK)
        - user_rules (N) → categories (1): Via category_id (FK)
        
        A regra é criada com active=1 (ativa) e current_total=0 (sem gastos ainda).
        
        Args:
            user_phone: ID do usuário dono da regra (relacionamento com users.user_phone)
            category_id: ID da categoria a ser monitorada (relacionamento com categories.category_id)
            period_type: Tipo de período ('semanal', 'mensal', 'diário', etc.)
            limit_value: Valor máximo permitido em reais (float)
            
        Returns:
            ID da regra criada (rule_id gerado pelo AUTOINCREMENT)
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO user_rules 
                   (user_phone, category_id, period_type, limit_value, current_total, last_updated, active)
                   VALUES (?, ?, ?, ?, 0, ?, 1)""",
                (user_phone, category_id, period_type, limit_value, datetime.now())
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_active_rules(user_phone: str) -> List[Dict[str, Any]]:
        """
        Retorna regras ativas do usuário com informações da categoria relacionada.
        
        Utiliza relacionamento entre tabelas:
        - JOIN entre user_rules e categories: Obtém o nome da categoria (category_name)
          relacionando user_rules.category_id com categories.category_id
        - Filtra por user_phone: Relaciona regras com o usuário
        
        Relacionamentos utilizados:
        - user_rules (N) → users (1): Via user_phone
        - user_rules (N) → categories (1): Via category_id (INNER JOIN garante que categoria existe)
        
        Args:
            user_phone: ID do usuário para filtrar regras
        
        Returns:
            Lista de dicionários com regras ativas, cada um contendo:
            - rule_id: ID da regra
            - category_id: ID da categoria monitorada
            - category_name: Nome da categoria (via JOIN com categories)
            - period_type: Tipo de período ("mensal", "semanal", etc.)
            - limit_value: Valor máximo permitido
            - current_total: Total atual gasto no período
            - last_updated: Data/hora da última atualização
        """
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT 
                    r.rule_id,
                    r.category_id,
                    c.category_name,
                    r.period_type,
                    r.limit_value,
                    r.current_total,
                    r.last_updated
                   FROM user_rules r
                   JOIN categories c ON r.category_id = c.category_id  -- JOIN para obter nome da categoria
                   WHERE r.user_phone = ? AND r.active = 1  -- Filtro pelo relacionamento user_rules → users
                """,
                (user_phone,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def update_rule_total(rule_id: int, new_total: float) -> None:
        """Atualiza o total acumulado de uma regra."""
        with get_connection() as conn:
            conn.execute(
                """UPDATE user_rules 
                   SET current_total = ?, last_updated = ?
                   WHERE rule_id = ?""",
                (new_total, datetime.now(), rule_id)
            )
            conn.commit()

    @staticmethod
    def delete_category(user_phone: str, category_id: int) -> bool:
        """
        Remove uma categoria do usuário.
        
        Verifica se há transações usando essa categoria antes de deletar.
        Se houver transações, não permite deletar (retorna False).
        Se não houver, remove limites associados e deleta a categoria.
        
        Args:
            user_phone: ID do usuário
            category_id: ID da categoria a ser removida
            
        Returns:
            True se deletou com sucesso, False se não pode deletar (há transações)
        """
        with get_connection() as conn:
            # Verifica se há transações usando essa categoria
            count = conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE category_id = ? AND user_phone = ?",
                (category_id, user_phone)
            ).fetchone()[0]
            
            if count > 0:
                # Não pode deletar se há transações
                return False
            
            # Remove limites associados (marca como inactive)
            conn.execute(
                "UPDATE user_rules SET active = 0 WHERE category_id = ? AND user_phone = ?",
                (category_id, user_phone)
            )
            
            # Remove categoria
            conn.execute(
                "DELETE FROM categories WHERE category_id = ? AND user_phone = ?",
                (category_id, user_phone)
            )
            conn.commit()
            return True
    
    @staticmethod
    def delete_limit_rule(user_phone: str, category_id: int) -> bool:
        """
        Remove um limite de gasto de uma categoria.
        
        Marca a regra como inactive (active = 0) em vez de deletar fisicamente,
        mantendo histórico.
        
        Args:
            user_phone: ID do usuário
            category_id: ID da categoria cujo limite será removido
            
        Returns:
            True se desativou com sucesso, False se não encontrou limite ativo
        """
        with get_connection() as conn:
            # Verifica se existe limite ativo
            count = conn.execute(
                "SELECT COUNT(*) FROM user_rules WHERE category_id = ? AND user_phone = ? AND active = 1",
                (category_id, user_phone)
            ).fetchone()[0]
            
            if count == 0:
                return False
            
            # Marca como inactive
            conn.execute(
                "UPDATE user_rules SET active = 0 WHERE category_id = ? AND user_phone = ? AND active = 1",
                (category_id, user_phone)
            )
            conn.commit()
            return True
    
    @staticmethod
    def save_conversation(user_phone: str, user_message: str, bot_response: str) -> int:
        """
        Salva uma interação de conversa no histórico.
        
        Args:
            user_phone: ID do usuário
            user_message: Mensagem enviada pelo usuário
            bot_response: Resposta do bot
            
        Returns:
            ID da mensagem salva
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO conversation_history (user_phone, user_message, bot_response, created_at)
                   VALUES (?, ?, ?, ?)""",
                (user_phone, user_message, bot_response, datetime.now())
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def delete_transaction(user_phone: str, transaction_id: int) -> bool:
        """
        Remove uma transação específica.
        
        Args:
            user_phone: Telefone do usuário
            transaction_id: ID da transação a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """DELETE FROM transactions 
                   WHERE transaction_id = ? AND user_phone = ?""",
                (transaction_id, user_phone)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def get_conversation_history(user_phone: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna o histórico de conversas do usuário.
        
        Args:
            user_phone: ID do usuário
            limit: Número máximo de mensagens a retornar (padrão: 10)
            
        Returns:
            Lista de dicionários com histórico de conversas, ordenado por data (mais antiga primeiro)
            Cada item contém: user_message, bot_response, created_at
        """
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT user_message, bot_response, created_at
                   FROM conversation_history
                   WHERE user_phone = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (user_phone, limit)
            ).fetchall()
            # Inverte para ter ordem cronológica (mais antiga primeiro)
            return [dict(row) for row in reversed(rows)]
    
    @staticmethod
    def clear_conversation_history(user_phone: str) -> int:
        """
        Limpa o histórico de conversas de um usuário (útil para testes).
        
        Args:
            user_phone: ID do usuário
            
        Returns:
            Número de mensagens deletadas
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM conversation_history WHERE user_phone = ?",
                (user_phone,)
            )
            conn.commit()
            return cursor.rowcount

