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
        Insere uma nova transação no banco.
        
        Returns:
            ID da transação criada
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
        Retorna todas as categorias de um usuário.
        
        Returns:
            Lista de dicionários com informações das categorias
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
        Calcula o total gasto em uma categoria.
        
        Args:
            user_phone: Telefone do usuário
            category_id: ID da categoria
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Total gasto
        """
        query = """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_phone = ? AND category_id = ?
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
        
        Returns:
            Lista de transações
        """
        query = """
            SELECT 
                t.transaction_id,
                t.amount,
                t.expense_description,
                t.created_at,
                c.category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            WHERE t.user_phone = ?
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
        
        Returns:
            Lista com totais por categoria
        """
        query = """
            SELECT 
                c.category_name,
                c.category_id,
                COUNT(t.transaction_id) as transaction_count,
                SUM(t.amount) as total_amount,
                AVG(t.amount) as avg_amount
            FROM categories c
            LEFT JOIN transactions t ON c.category_id = t.category_id
            WHERE c.user_phone = ?
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
        
        Returns:
            ID da categoria criada
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
        Cria uma regra de limite de gasto.
        
        Args:
            period_type: 'semanal', 'mensal', etc.
            
        Returns:
            ID da regra criada
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
        Retorna regras ativas do usuário.
        
        Returns:
            Lista de regras com informações da categoria
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
                   JOIN categories c ON r.category_id = c.category_id
                   WHERE r.user_phone = ? AND r.active = 1""",
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

