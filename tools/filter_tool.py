"""FilterTool - Filtros e seleção de dados."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class FilterTool:
    """
    Tool para aplicar filtros sobre conjuntos de dados.
    
    Permite selecionar subconjuntos de transações baseados em critérios
    como categoria, data e valor.
    """
    
    @staticmethod
    def filter_by_date_range(
        transactions: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        date_field: str = 'created_at'
    ) -> List[Dict[str, Any]]:
        """
        Filtra transações por intervalo de datas.
        
        Args:
            transactions: Lista de transações
            start_date: Data inicial
            end_date: Data final
            date_field: Nome do campo de data
            
        Returns:
            Transações filtradas
        """
        filtered = []
        for t in transactions:
            date_value = t.get(date_field)
            if isinstance(date_value, str):
                date_value = datetime.fromisoformat(date_value)
            
            if date_value and start_date <= date_value <= end_date:
                filtered.append(t)
        
        return filtered
    
    @staticmethod
    def filter_by_category(
        transactions: List[Dict[str, Any]],
        category_id: Optional[int] = None,
        category_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filtra transações por categoria.
        
        Args:
            transactions: Lista de transações
            category_id: ID da categoria (opcional)
            category_name: Nome da categoria (opcional)
            
        Returns:
            Transações filtradas
        """
        filtered = []
        for t in transactions:
            if category_id and t.get('category_id') == category_id:
                filtered.append(t)
            elif category_name and t.get('category_name', '').lower() == category_name.lower():
                filtered.append(t)
        
        return filtered if (category_id or category_name) else transactions
    
    @staticmethod
    def filter_by_amount_range(
        transactions: List[Dict[str, Any]],
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Filtra transações por faixa de valor.
        
        Args:
            transactions: Lista de transações
            min_amount: Valor mínimo (opcional)
            max_amount: Valor máximo (opcional)
            
        Returns:
            Transações filtradas
        """
        filtered = []
        for t in transactions:
            amount = t.get('amount', 0)
            
            if min_amount is not None and amount < min_amount:
                continue
            if max_amount is not None and amount > max_amount:
                continue
            
            filtered.append(t)
        
        return filtered
    
    @staticmethod
    def filter_last_n_days(
        transactions: List[Dict[str, Any]],
        days: int,
        date_field: str = 'created_at'
    ) -> List[Dict[str, Any]]:
        """
        Filtra transações dos últimos N dias.
        
        Args:
            transactions: Lista de transações
            days: Número de dias
            date_field: Nome do campo de data
            
        Returns:
            Transações filtradas
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered = []
        for t in transactions:
            date_value = t.get(date_field)
            if isinstance(date_value, str):
                date_value = datetime.fromisoformat(date_value)
            
            if date_value and date_value >= cutoff_date:
                filtered.append(t)
        
        return filtered
    
    @staticmethod
    def filter_this_week(
        transactions: List[Dict[str, Any]],
        date_field: str = 'created_at'
    ) -> List[Dict[str, Any]]:
        """
        Filtra transações da semana atual.
        
        Returns:
            Transações da semana
        """
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return FilterTool.filter_by_date_range(
            transactions,
            start_of_week,
            now,
            date_field
        )
    
    @staticmethod
    def filter_this_month(
        transactions: List[Dict[str, Any]],
        date_field: str = 'created_at'
    ) -> List[Dict[str, Any]]:
        """
        Filtra transações do mês atual.
        
        Returns:
            Transações do mês
        """
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return FilterTool.filter_by_date_range(
            transactions,
            start_of_month,
            now,
            date_field
        )
    
    @staticmethod
    def filter_last_month(
        transactions: List[Dict[str, Any]],
        date_field: str = 'created_at'
    ) -> List[Dict[str, Any]]:
        """
        Filtra transações do mês passado.
        
        Returns:
            Transações do mês anterior
        """
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_last_month = start_of_month - timedelta(days=1)
        start_of_last_month = end_of_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return FilterTool.filter_by_date_range(
            transactions,
            start_of_last_month,
            end_of_last_month,
            date_field
        )
    
    @staticmethod
    def sort_by_amount(
        transactions: List[Dict[str, Any]],
        descending: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Ordena transações por valor.
        
        Args:
            transactions: Lista de transações
            descending: Se True, maior para menor; se False, menor para maior
            
        Returns:
            Lista ordenada
        """
        return sorted(
            transactions,
            key=lambda x: x.get('amount', 0),
            reverse=descending
        )
    
    @staticmethod
    def sort_by_date(
        transactions: List[Dict[str, Any]],
        descending: bool = True,
        date_field: str = 'created_at'
    ) -> List[Dict[str, Any]]:
        """
        Ordena transações por data.
        
        Args:
            transactions: Lista de transações
            descending: Se True, mais recente primeiro
            date_field: Nome do campo de data
            
        Returns:
            Lista ordenada
        """
        def get_date(t):
            date_value = t.get(date_field)
            if isinstance(date_value, str):
                return datetime.fromisoformat(date_value)
            return date_value or datetime.min
        
        return sorted(
            transactions,
            key=get_date,
            reverse=descending
        )
    
    @staticmethod
    def limit_results(
        transactions: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Limita o número de resultados.
        
        Args:
            transactions: Lista de transações
            limit: Número máximo de itens
            
        Returns:
            Lista limitada
        """
        return transactions[:limit]

