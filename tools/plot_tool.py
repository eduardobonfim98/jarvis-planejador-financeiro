"""PlotTool - Geração de gráficos financeiros."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from config import PLOTS_DIR


class PlotTool:
    """
    Tool para gerar visualizações gráficas dos dados financeiros.
    
    Utiliza Matplotlib para criar gráficos de pizza, barras e séries temporais.
    """
    
    @staticmethod
    def plot_pie_chart(
        data: Dict[str, float],
        title: str = "Gastos por Categoria",
        filename: Optional[str] = None
    ) -> Path:
        """
        Gera um gráfico de pizza.
        
        Args:
            data: Dicionário {categoria: valor}
            title: Título do gráfico
            filename: Nome do arquivo (gerado automaticamente se None)
            
        Returns:
            Caminho do arquivo gerado
        """
        if not filename:
            filename = f"pie_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = PLOTS_DIR / filename
        
        # Filtrar valores zero
        filtered_data = {k: v for k, v in data.items() if v > 0}
        
        if not filtered_data:
            # Criar gráfico vazio
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Sem dados para exibir', 
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            labels = list(filtered_data.keys())
            sizes = list(filtered_data.values())
            
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    @staticmethod
    def plot_bar_chart(
        data: Dict[str, float],
        title: str = "Comparativo de Gastos",
        xlabel: str = "Categoria",
        ylabel: str = "Valor (R$)",
        filename: Optional[str] = None,
        horizontal: bool = False
    ) -> Path:
        """
        Gera um gráfico de barras.
        
        Args:
            data: Dicionário {categoria: valor}
            title: Título do gráfico
            xlabel: Rótulo do eixo X
            ylabel: Rótulo do eixo Y
            filename: Nome do arquivo
            horizontal: Se True, barras horizontais
            
        Returns:
            Caminho do arquivo gerado
        """
        if not filename:
            filename = f"bar_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = PLOTS_DIR / filename
        
        if not data:
            # Criar gráfico vazio
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Sem dados para exibir', 
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            labels = list(data.keys())
            values = list(data.values())
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if horizontal:
                ax.barh(labels, values, color='steelblue')
                ax.set_xlabel(ylabel)
                ax.set_ylabel(xlabel)
            else:
                ax.bar(labels, values, color='steelblue')
                ax.set_xlabel(xlabel)
                ax.set_ylabel(ylabel)
                plt.xticks(rotation=45, ha='right')
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    @staticmethod
    def plot_time_series(
        dates: List[datetime],
        values: List[float],
        title: str = "Evolução dos Gastos",
        ylabel: str = "Valor (R$)",
        filename: Optional[str] = None
    ) -> Path:
        """
        Gera um gráfico de série temporal.
        
        Args:
            dates: Lista de datas
            values: Lista de valores correspondentes
            title: Título do gráfico
            ylabel: Rótulo do eixo Y
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo gerado
        """
        if not filename:
            filename = f"timeseries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = PLOTS_DIR / filename
        
        if not dates or not values:
            # Criar gráfico vazio
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'Sem dados para exibir', 
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(dates, values, marker='o', linestyle='-', linewidth=2, markersize=6)
            
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_ylabel(ylabel, fontsize=12)
            ax.set_xlabel("Data", fontsize=12)
            
            # Formatar datas no eixo X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 10)))
            plt.xticks(rotation=45, ha='right')
            
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    @staticmethod
    def plot_comparison_bars(
        labels: List[str],
        group1_values: List[float],
        group2_values: List[float],
        group1_label: str = "Período 1",
        group2_label: str = "Período 2",
        title: str = "Comparativo entre Períodos",
        filename: Optional[str] = None
    ) -> Path:
        """
        Gera gráfico de barras comparando dois grupos.
        
        Args:
            labels: Rótulos das categorias
            group1_values: Valores do primeiro grupo
            group2_values: Valores do segundo grupo
            group1_label: Legenda do primeiro grupo
            group2_label: Legenda do segundo grupo
            title: Título do gráfico
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo gerado
        """
        if not filename:
            filename = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = PLOTS_DIR / filename
        
        import numpy as np
        
        x = np.arange(len(labels))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars1 = ax.bar(x - width/2, group1_values, width, label=group1_label, color='steelblue')
        bars2 = ax.bar(x + width/2, group2_values, width, label=group2_label, color='coral')
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_ylabel('Valor (R$)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    @staticmethod
    def plot_daily_spending(
        transactions: List[Dict[str, Any]],
        title: str = "Gastos Diários",
        filename: Optional[str] = None
    ) -> Path:
        """
        Gera gráfico de gastos diários a partir de transações.
        
        Args:
            transactions: Lista de transações com 'created_at' e 'amount'
            title: Título do gráfico
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo gerado
        """
        # Agregar por dia
        daily_totals = {}
        for t in transactions:
            date = t.get('created_at')
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            
            if date:
                day_key = date.date()
                daily_totals[day_key] = daily_totals.get(day_key, 0) + t.get('amount', 0)
        
        # Ordenar por data
        sorted_days = sorted(daily_totals.keys())
        dates = [datetime.combine(d, datetime.min.time()) for d in sorted_days]
        values = [daily_totals[d] for d in sorted_days]
        
        return PlotTool.plot_time_series(dates, values, title, filename=filename)

