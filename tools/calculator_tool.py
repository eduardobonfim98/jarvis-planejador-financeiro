"""CalculatorTool - Cálculos financeiros e comparativos."""

from typing import List
from statistics import mean, median


class CalculatorTool:
    """
    Tool para realizar cálculos matemáticos relacionados a finanças.
    
    Implementa operações de soma, média, variação percentual e outros
    cálculos úteis para análise financeira.
    """
    
    @staticmethod
    def sum_values(values: List[float]) -> float:
        """
        Soma uma lista de valores.
        
        Args:
            values: Lista de valores numéricos
            
        Returns:
            Soma total
        """
        return sum(values) if values else 0.0
    
    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """
        Calcula a média de uma lista de valores.
        
        Returns:
            Média aritmética
        """
        return mean(values) if values else 0.0
    
    @staticmethod
    def calculate_median(values: List[float]) -> float:
        """
        Calcula a mediana de uma lista de valores.
        
        Returns:
            Mediana
        """
        return median(values) if values else 0.0
    
    @staticmethod
    def percent_change(old_value: float, new_value: float) -> float:
        """
        Calcula a variação percentual entre dois valores.
        
        Args:
            old_value: Valor anterior
            new_value: Valor novo
            
        Returns:
            Percentual de variação
        """
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def calculate_difference(value1: float, value2: float) -> float:
        """
        Calcula a diferença absoluta entre dois valores.
        
        Returns:
            Diferença (positiva ou negativa)
        """
        return value2 - value1
    
    @staticmethod
    def calculate_percentage_of_total(part: float, total: float) -> float:
        """
        Calcula qual percentual uma parte representa do total.
        
        Args:
            part: Valor da parte
            total: Valor total
            
        Returns:
            Percentual que a parte representa
        """
        if total == 0:
            return 0.0
        
        return (part / total) * 100
    
    @staticmethod
    def check_limit_exceeded(current: float, limit: float) -> bool:
        """
        Verifica se um valor atual excedeu um limite.
        
        Returns:
            True se excedeu, False caso contrário
        """
        return current > limit
    
    @staticmethod
    def calculate_remaining(limit: float, current: float) -> float:
        """
        Calcula quanto resta de um limite.
        
        Returns:
            Valor restante (pode ser negativo se excedeu)
        """
        return limit - current
    
    @staticmethod
    def calculate_daily_average(total: float, days: int) -> float:
        """
        Calcula a média diária de gastos.
        
        Args:
            total: Total gasto
            days: Número de dias
            
        Returns:
            Média diária
        """
        if days == 0:
            return 0.0
        
        return total / days
    
    @staticmethod
    def project_monthly_spending(current_total: float, days_elapsed: int, total_days: int = 30) -> float:
        """
        Projeta o gasto mensal com base nos dias passados.
        
        Args:
            current_total: Total gasto até agora
            days_elapsed: Dias que já passaram
            total_days: Total de dias no período (padrão 30)
            
        Returns:
            Projeção de gasto total
        """
        if days_elapsed == 0:
            return 0.0
        
        daily_avg = current_total / days_elapsed
        return daily_avg * total_days
    
    @staticmethod
    def calculate_savings_needed(
        current_spending: float,
        target_spending: float
    ) -> float:
        """
        Calcula quanto é necessário economizar para atingir uma meta.
        
        Returns:
            Valor que precisa economizar (positivo) ou está economizando (negativo)
        """
        return current_spending - target_spending
    
    @staticmethod
    def rank_categories_by_spending(category_totals: dict) -> List[tuple]:
        """
        Ordena categorias por gasto total (maior para menor).
        
        Args:
            category_totals: Dict {categoria: total}
            
        Returns:
            Lista de tuplas (categoria, total) ordenada
        """
        return sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def calculate_category_weight(category_total: float, overall_total: float) -> float:
        """
        Calcula o peso de uma categoria no total geral.
        
        Returns:
            Percentual (0-100)
        """
        return CalculatorTool.calculate_percentage_of_total(category_total, overall_total)

