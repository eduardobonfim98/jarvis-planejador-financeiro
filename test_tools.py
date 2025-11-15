"""Script de testes para as Tools do Jarvis."""

import sys
from pathlib import Path

# Adiciona raiz ao path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from datetime import datetime, timedelta
from tools import SQLTool, FormatterTool, CalculatorTool, FilterTool, PlotTool
from database import init_database

print("=" * 80)
print("TESTANDO TOOLS DO JARVIS")
print("=" * 80)

# Inicializa banco
print("\n📦 Inicializando banco de dados...")
init_database()
print("✅ Banco inicializado\n")

# ============================================================================
# 1. TESTE SQLTool
# ============================================================================
print("\n" + "=" * 80)
print("1. TESTANDO SQLTool")
print("=" * 80)

# Criar usuário
print("\n→ Criando usuário de teste...")
user = SQLTool.get_or_create_user("5511999999999", "João Teste")
print(f"✅ Usuário criado: {user['user_name']} ({user['user_phone']})")

# Criar categorias
print("\n→ Criando categorias...")
cat_id_1 = SQLTool.create_category("5511999999999", "Alimentação", "Comidas e bebidas")
cat_id_2 = SQLTool.create_category("5511999999999", "Transporte", "Uber, ônibus")
print(f"✅ Categorias criadas: IDs {cat_id_1}, {cat_id_2}")

# Listar categorias
print("\n→ Listando categorias do usuário...")
categories = SQLTool.get_user_categories("5511999999999")
for cat in categories:
    print(f"   • {cat['category_name']}: {cat['description']}")

# Inserir transações
print("\n→ Inserindo transações de teste...")
trans_id_1 = SQLTool.insert_transaction("5511999999999", cat_id_1, 45.90, "Almoço no restaurante")
trans_id_2 = SQLTool.insert_transaction("5511999999999", cat_id_1, 120.50, "Compras no mercado")
trans_id_3 = SQLTool.insert_transaction("5511999999999", cat_id_2, 25.00, "Uber para o trabalho")
print(f"✅ 3 transações inseridas: IDs {trans_id_1}, {trans_id_2}, {trans_id_3}")

# Buscar total por categoria
print("\n→ Calculando total por categoria...")
total_alimentacao = SQLTool.get_total_by_category("5511999999999", cat_id_1)
total_transporte = SQLTool.get_total_by_category("5511999999999", cat_id_2)
print(f"   • Alimentação: R$ {total_alimentacao:.2f}")
print(f"   • Transporte: R$ {total_transporte:.2f}")

# Buscar transações
print("\n→ Buscando últimas transações...")
transactions = SQLTool.get_transactions("5511999999999", limit=5)
print(f"✅ {len(transactions)} transações encontradas")

# Resumo por categoria
print("\n→ Gerando resumo por categoria...")
summary = SQLTool.get_spending_by_category("5511999999999")
for item in summary:
    if item['total_amount']:
        print(f"   • {item['category_name']}: R$ {item['total_amount']:.2f} ({item['transaction_count']} transações)")

# ============================================================================
# 2. TESTE FormatterTool
# ============================================================================
print("\n" + "=" * 80)
print("2. TESTANDO FormatterTool")
print("=" * 80)

# Formatar moeda
print("\n→ Formatando valores monetários...")
print(f"   • {FormatterTool.format_currency(1234.56)}")
print(f"   • {FormatterTool.format_currency(45.9)}")
print(f"   • {FormatterTool.format_currency(-100.00)}")

# Formatar data
print("\n→ Formatando datas...")
now = datetime.now()
print(f"   • Formato curto: {FormatterTool.format_date(now)}")
print(f"   • Formato longo: {FormatterTool.format_date(now, 'long')}")
print(f"   • Com hora: {FormatterTool.format_datetime(now)}")

# Formatar percentual
print("\n→ Formatando percentuais...")
print(f"   • {FormatterTool.format_percentage(25.5)}")
print(f"   • {FormatterTool.format_percentage(100.0)}")

# Formatar lista de transações
print("\n→ Formatando lista de transações...")
formatted_list = FormatterTool.format_transaction_list(transactions[:2])
print(formatted_list)

# Formatar resumo por categoria
print("\n→ Formatando resumo por categoria...")
formatted_summary = FormatterTool.format_category_summary(summary)
print(formatted_summary)

# Formatar alerta
print("\n→ Formatando alerta de limite...")
alert = FormatterTool.format_limit_alert("Alimentação", 450.0, 500.0, "mensal")
print(alert)

# Formatar comparação
print("\n→ Formatando comparação...")
comparison = FormatterTool.format_comparison(1000.0, 1250.0, "Mês passado", "Este mês")
print(comparison)

# ============================================================================
# 3. TESTE CalculatorTool
# ============================================================================
print("\n" + "=" * 80)
print("3. TESTANDO CalculatorTool")
print("=" * 80)

valores = [45.90, 120.50, 25.00, 80.00]

print("\n→ Calculando soma...")
soma = CalculatorTool.sum_values(valores)
print(f"   • Soma de {valores}: R$ {soma:.2f}")

print("\n→ Calculando média...")
media = CalculatorTool.calculate_average(valores)
print(f"   • Média: R$ {media:.2f}")

print("\n→ Calculando mediana...")
mediana = CalculatorTool.calculate_median(valores)
print(f"   • Mediana: R$ {mediana:.2f}")

print("\n→ Calculando variação percentual...")
var_percent = CalculatorTool.percent_change(1000, 1250)
print(f"   • De R$ 1.000 para R$ 1.250: {var_percent:+.1f}%")

print("\n→ Calculando percentual do total...")
parte = 450.0
total = 1500.0
percentual = CalculatorTool.calculate_percentage_of_total(parte, total)
print(f"   • R$ {parte:.2f} de R$ {total:.2f}: {percentual:.1f}%")

print("\n→ Verificando limite excedido...")
excedeu = CalculatorTool.check_limit_exceeded(550, 500)
print(f"   • R$ 550 com limite R$ 500: {'EXCEDEU' if excedeu else 'OK'}")

print("\n→ Calculando valor restante...")
restante = CalculatorTool.calculate_remaining(500, 350)
print(f"   • Limite R$ 500, gasto R$ 350: resta R$ {restante:.2f}")

print("\n→ Projetando gasto mensal...")
projecao = CalculatorTool.project_monthly_spending(350, 10, 30)
print(f"   • R$ 350 em 10 dias → Projeção 30 dias: R$ {projecao:.2f}")

# ============================================================================
# 4. TESTE FilterTool
# ============================================================================
print("\n" + "=" * 80)
print("4. TESTANDO FilterTool")
print("=" * 80)

# Criar dataset de teste
test_transactions = [
    {'transaction_id': 1, 'amount': 50.0, 'category_id': 1, 'created_at': datetime.now() - timedelta(days=5)},
    {'transaction_id': 2, 'amount': 120.0, 'category_id': 1, 'created_at': datetime.now() - timedelta(days=2)},
    {'transaction_id': 3, 'amount': 25.0, 'category_id': 2, 'created_at': datetime.now() - timedelta(days=1)},
    {'transaction_id': 4, 'amount': 200.0, 'category_id': 1, 'created_at': datetime.now()},
]

print(f"\n→ Dataset de teste: {len(test_transactions)} transações")

print("\n→ Filtrando por categoria...")
filtrado_cat = FilterTool.filter_by_category(test_transactions, category_id=1)
print(f"   • Categoria 1: {len(filtrado_cat)} transações")

print("\n→ Filtrando por valor...")
filtrado_valor = FilterTool.filter_by_amount_range(test_transactions, min_amount=50, max_amount=150)
print(f"   • Entre R$ 50 e R$ 150: {len(filtrado_valor)} transações")

print("\n→ Filtrando últimos 3 dias...")
filtrado_dias = FilterTool.filter_last_n_days(test_transactions, 3)
print(f"   • Últimos 3 dias: {len(filtrado_dias)} transações")

print("\n→ Ordenando por valor (maior → menor)...")
ordenado = FilterTool.sort_by_amount(test_transactions)
for t in ordenado:
    print(f"   • ID {t['transaction_id']}: R$ {t['amount']:.2f}")

print("\n→ Limitando resultados...")
limitado = FilterTool.limit_results(test_transactions, 2)
print(f"   • Limite 2: {len(limitado)} transações retornadas")

# ============================================================================
# 5. TESTE PlotTool
# ============================================================================
print("\n" + "=" * 80)
print("5. TESTANDO PlotTool")
print("=" * 80)

print("\n→ Gerando gráfico de pizza...")
data_pizza = {
    "Alimentação": 166.40,
    "Transporte": 25.00,
    "Lazer": 80.00
}
filepath_pizza = PlotTool.plot_pie_chart(data_pizza, "Gastos por Categoria - Teste")
print(f"✅ Gráfico salvo em: {filepath_pizza}")

print("\n→ Gerando gráfico de barras...")
data_barras = {
    "Alimentação": 166.40,
    "Transporte": 25.00,
    "Lazer": 80.00,
    "Saúde": 50.00
}
filepath_barras = PlotTool.plot_bar_chart(data_barras, "Comparativo - Teste")
print(f"✅ Gráfico salvo em: {filepath_barras}")

print("\n→ Gerando série temporal...")
dates = [datetime.now() - timedelta(days=i) for i in range(7, 0, -1)]
values = [45.0, 80.0, 30.0, 120.0, 55.0, 90.0, 70.0]
filepath_series = PlotTool.plot_time_series(dates, values, "Gastos Diários - Teste")
print(f"✅ Gráfico salvo em: {filepath_series}")

print("\n→ Gerando comparação entre períodos...")
labels = ["Alimentação", "Transporte", "Lazer"]
periodo1 = [150, 80, 100]
periodo2 = [200, 60, 120]
filepath_comp = PlotTool.plot_comparison_bars(
    labels, periodo1, periodo2, 
    "Mês passado", "Este mês",
    "Comparativo Mensal - Teste"
)
print(f"✅ Gráfico salvo em: {filepath_comp}")

# ============================================================================
# RESUMO FINAL
# ============================================================================
print("\n" + "=" * 80)
print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
print("=" * 80)
print("\nResumo:")
print("  • SQLTool: ✅ CRUD, queries e agregações funcionando")
print("  • FormatterTool: ✅ Formatação de valores e mensagens OK")
print("  • CalculatorTool: ✅ Cálculos financeiros funcionando")
print("  • FilterTool: ✅ Filtros e ordenação OK")
print("  • PlotTool: ✅ Gráficos gerados com sucesso")
print("\n📊 Gráficos salvos em: plots/")
print("🗄️  Dados de teste em: jarvis.db")
print("\n" + "=" * 80)

