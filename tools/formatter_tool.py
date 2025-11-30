"""FormatterTool - Formatação de mensagens e valores."""

from datetime import datetime
from typing import List, Dict, Any


class FormatterTool:
    """
    Tool para formatar saídas de texto, valores monetários e mensagens.
    
    Garante padronização na comunicação com o usuário.
    """
    
    @staticmethod
    def format_currency(value: float) -> str:
        """
        Formata um valor numérico para o padrão monetário brasileiro.
        
        Args:
            value: Valor numérico
            
        Returns:
            String formatada (ex: "R$ 1.234,56")
        """
        if value < 0:
            return f"-R$ {abs(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @staticmethod
    def format_date(date: datetime, format_type: str = "short") -> str:
        """
        Formata uma data de forma legível.
        
        Args:
            date: Data a ser formatada
            format_type: "short" (DD/MM/YYYY) ou "long" (DD de Mês de YYYY)
            
        Returns:
            Data formatada
        """
        if format_type == "long":
            meses = [
                "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
            ]
            return f"{date.day} de {meses[date.month - 1]} de {date.year}"
        
        return date.strftime("%d/%m/%Y")
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """
        Formata data e hora.
        
        Returns:
            String no formato "DD/MM/YYYY às HH:MM"
        """
        return dt.strftime("%d/%m/%Y às %H:%M")
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """
        Formata um valor percentual.
        
        Args:
            value: Valor percentual (ex: 25.5 para 25,5%)
            decimals: Casas decimais
            
        Returns:
            String formatada (ex: "25,5%")
        """
        formatted = f"{value:.{decimals}f}".replace('.', ',')
        return f"{formatted}%"
    
    @staticmethod
    def format_transaction_list(transactions: List[Dict[str, Any]]) -> str:
        """
        Formata uma lista de transações para exibição.
        
        Args:
            transactions: Lista de dicionários com transaction_id, amount, 
                         expense_description, created_at, category_name
            
        Returns:
            String formatada com a lista de transações (inclui data e horário)
        """
        if not transactions:
            return "Nenhuma transação encontrada."
        
        lines = ["📋 *Transações:*\n"]
        
        for t in transactions:
            # Converte created_at para datetime se for string
            created_at = t.get('created_at')
            if created_at is None:
                continue
                
            if isinstance(created_at, str):
                # Tenta parsear como ISO format primeiro
                try:
                    date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    # Se falhar, tenta outros formatos comuns do SQLite
                    try:
                        # Formato: YYYY-MM-DD HH:MM:SS
                        date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            # Formato: YYYY-MM-DD HH:MM:SS.ffffff
                            date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
                        except:
                            # Último recurso: tenta parsear como date apenas
                            try:
                                date = datetime.strptime(created_at, '%Y-%m-%d')
                            except:
                                # Se tudo falhar, usa data atual
                                date = datetime.now()
            elif isinstance(created_at, datetime):
                date = created_at
            else:
                # Se for outro tipo, usa data atual
                date = datetime.now()
            
            # Formata data e horário
            datetime_str = FormatterTool.format_datetime(date)
            amount_str = FormatterTool.format_currency(t['amount'])
            category = t.get('category_name', 'Sem categoria')
            description = t.get('expense_description', 'Sem descrição')
            
            lines.append(
                f"• {datetime_str} - {amount_str}\n"
                f"  {description} ({category})"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def format_category_summary(spending_data: List[Dict[str, Any]]) -> str:
        """
        Formata resumo de gastos por categoria.
        
        Args:
            spending_data: Lista de dicionários com category_name, total_amount, 
                          transaction_count, avg_amount
            
        Returns:
            String formatada
        """
        if not spending_data:
            return "Nenhum gasto registrado ainda."
        
        lines = ["💰 *Gastos por Categoria:*\n"]
        total_geral = sum(item.get('total_amount', 0) or 0 for item in spending_data)
        
        for item in spending_data:
            if not item.get('total_amount'):
                continue
                
            cat_name = item['category_name']
            total = item['total_amount']
            count = item.get('transaction_count', 0)
            avg = item.get('avg_amount', 0)
            
            percentual = (total / total_geral * 100) if total_geral > 0 else 0
            
            lines.append(
                f"• *{cat_name}*: {FormatterTool.format_currency(total)}\n"
                f"  {count} transações • Média: {FormatterTool.format_currency(avg)} "
                f"({FormatterTool.format_percentage(percentual)})"
            )
        
        lines.append(f"\n*Total Geral:* {FormatterTool.format_currency(total_geral)}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_limit_alert(
        category_name: str,
        current_total: float,
        limit_value: float,
        period_type: str
    ) -> str:
        """
        Formata mensagem de alerta de limite.
        
        Returns:
            Mensagem formatada
        """
        percentage = (current_total / limit_value * 100) if limit_value > 0 else 0
        
        if percentage >= 100:
            emoji = "🔴"
            status = "EXCEDIDO"
        elif percentage >= 80:
            emoji = "🟡"
            status = "ATENÇÃO"
        else:
            emoji = "🟢"
            status = "OK"
        
        return (
            f"{emoji} *Alerta de Limite* {emoji}\n\n"
            f"Categoria: *{category_name}*\n"
            f"Período: {period_type}\n"
            f"Gasto atual: {FormatterTool.format_currency(current_total)}\n"
            f"Limite: {FormatterTool.format_currency(limit_value)}\n"
            f"Status: *{status}* ({FormatterTool.format_percentage(percentage)})"
        )
    
    @staticmethod
    def format_comparison(
        period1_total: float,
        period2_total: float,
        period1_label: str = "Período anterior",
        period2_label: str = "Período atual"
    ) -> str:
        """
        Formata comparação entre dois períodos.
        
        Returns:
            String formatada com comparação
        """
        diff = period2_total - period1_total
        
        if period1_total > 0:
            percentage_change = (diff / period1_total) * 100
        else:
            percentage_change = 100.0 if period2_total > 0 else 0.0
        
        if diff > 0:
            emoji = "📈"
            verb = "aumentou"
        elif diff < 0:
            emoji = "📉"
            verb = "diminuiu"
        else:
            emoji = "➡️"
            verb = "manteve"
        
        return (
            f"{emoji} *Comparação:*\n\n"
            f"{period1_label}: {FormatterTool.format_currency(period1_total)}\n"
            f"{period2_label}: {FormatterTool.format_currency(period2_total)}\n\n"
            f"Diferença: {FormatterTool.format_currency(abs(diff))}\n"
            f"Seus gastos {verb} {FormatterTool.format_percentage(abs(percentage_change))}"
        )
    
    @staticmethod
    def format_confirmation(
        amount: float,
        category: str,
        description: str
    ) -> str:
        """
        Formata mensagem de confirmação de gasto.
        
        Returns:
            String formatada
        """
        return (
            f"✅ *Confirmar Registro:*\n\n"
            f"Valor: {FormatterTool.format_currency(amount)}\n"
            f"Categoria: {category}\n"
            f"Descrição: {description}\n\n"
            f"Está correto? (Sim/Não)"
        )
    
    @staticmethod
    def format_success_message(message: str) -> str:
        """Formata mensagem de sucesso."""
        return f"✅ {message}"
    
    @staticmethod
    def format_error_message(message: str) -> str:
        """Formata mensagem de erro."""
        return f"❌ {message}"
    
    @staticmethod
    def format_info_message(message: str) -> str:
        """Formata mensagem informativa."""
        return f"ℹ️ {message}"

