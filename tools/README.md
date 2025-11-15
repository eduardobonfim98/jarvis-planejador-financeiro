# Tools do Jarvis

Este diretório contém as ferramentas (Tools) utilizadas pelos agentes do Jarvis para executar ações concretas, seguindo os princípios do **ReAct** (Reasoning + Acting) e **Toolformer**.

## Arquitetura

As Tools separam o **raciocínio** (feito pelos agentes) da **ação** (executada pelas Tools), garantindo:
- **Modularidade**: cada Tool tem uma responsabilidade específica
- **Reusabilidade**: Tools podem ser usadas por diferentes agentes
- **Testabilidade**: Tools podem ser testadas independentemente

## Tools Implementadas

### 1. SQLTool (`sql_tool.py`)

Interface para todas as operações no banco de dados SQLite.

**Principais métodos:**
- `insert_transaction()` - Insere nova transação
- `get_user_categories()` - Lista categorias do usuário
- `get_total_by_category()` - Calcula total por categoria
- `get_total_by_period()` - Calcula total por período
- `get_transactions()` - Busca transações com filtros
- `get_spending_by_category()` - Agrupa gastos por categoria
- `create_category()` - Cria nova categoria
- `get_or_create_user()` - Busca ou cria usuário
- `create_limit_rule()` - Cria regra de limite
- `get_active_rules()` - Lista regras ativas
- `update_rule_total()` - Atualiza total de regra

### 2. FormatterTool (`formatter_tool.py`)

Formatação de valores e mensagens para exibição ao usuário.

**Principais métodos:**
- `format_currency()` - Formata valores em R$ (ex: "R$ 1.234,56")
- `format_date()` - Formata datas (DD/MM/YYYY)
- `format_datetime()` - Formata data e hora
- `format_percentage()` - Formata percentuais
- `format_transaction_list()` - Lista de transações formatada
- `format_category_summary()` - Resumo por categoria
- `format_limit_alert()` - Alerta de limite
- `format_comparison()` - Comparação entre períodos
- `format_confirmation()` - Mensagem de confirmação

### 3. CalculatorTool (`calculator_tool.py`)

Cálculos matemáticos e financeiros.

**Principais métodos:**
- `sum_values()` - Soma lista de valores
- `calculate_average()` - Média aritmética
- `calculate_median()` - Mediana
- `percent_change()` - Variação percentual
- `calculate_difference()` - Diferença entre valores
- `calculate_percentage_of_total()` - Percentual do total
- `check_limit_exceeded()` - Verifica se excedeu limite
- `calculate_remaining()` - Calcula valor restante
- `calculate_daily_average()` - Média diária
- `project_monthly_spending()` - Projeção mensal
- `rank_categories_by_spending()` - Ranking de categorias

### 4. FilterTool (`filter_tool.py`)

Filtros e seleção de dados.

**Principais métodos:**
- `filter_by_date_range()` - Filtra por intervalo de datas
- `filter_by_category()` - Filtra por categoria
- `filter_by_amount_range()` - Filtra por faixa de valor
- `filter_last_n_days()` - Últimos N dias
- `filter_this_week()` - Semana atual
- `filter_this_month()` - Mês atual
- `filter_last_month()` - Mês anterior
- `sort_by_amount()` - Ordena por valor
- `sort_by_date()` - Ordena por data
- `limit_results()` - Limita quantidade de resultados

### 5. PlotTool (`plot_tool.py`)

Geração de gráficos e visualizações.

**Principais métodos:**
- `plot_pie_chart()` - Gráfico de pizza (distribuição por categoria)
- `plot_bar_chart()` - Gráfico de barras
- `plot_time_series()` - Série temporal (evolução)
- `plot_comparison_bars()` - Comparação entre grupos
- `plot_daily_spending()` - Gastos diários

**Características:**
- Usa Matplotlib para geração
- Salva imagens em `plots/` (criado automaticamente)
- Retorna `Path` do arquivo gerado
- Alta resolução (300 dpi) para qualidade

## Uso

```python
from tools import SQLTool, FormatterTool, CalculatorTool

# Exemplo: buscar total e formatar
total = SQLTool.get_total_by_category("5511999999999", 1)
formatted = FormatterTool.format_currency(total)
print(formatted)  # "R$ 1.234,56"

# Exemplo: calcular variação
old_value = 1000
new_value = 1250
change = CalculatorTool.percent_change(old_value, new_value)
print(f"Variação: {change}%")  # "Variação: 25.0%"
```

## Próximos Passos

Essas Tools serão utilizadas pelos agentes (FinanceAgent, SetupAgent, etc.) para executar as funcionalidades do Jarvis.

O agente decide **quando** e **como** usar cada Tool baseado na solicitação do usuário.

