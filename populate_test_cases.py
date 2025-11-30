"""
Script para popular a base de dados com casos de teste que demonstram
todas as funcionalidades que o bot cobre.

Este script cria:
- 1 usuário de teste
- Categorias padrão e personalizadas
- Transações de exemplo em diferentes períodos
- Limites configurados para algumas categorias

Uso:
    uv run python populate_test_cases.py
"""

import sys
from datetime import datetime, timedelta
from database import init_database, get_connection
from tools import SQLTool


def populate_test_cases(user_id: str = "123456789"):
    """
    Popula a base de dados com casos de teste completos.
    
    Args:
        user_id: ID do usuário de teste (padrão: "123456789")
    """
    print("🔄 Inicializando banco de dados...")
    init_database()
    
    print(f"👤 Criando usuário de teste: {user_id}")
    user = SQLTool.get_or_create_user(user_id, "Usuário de Teste")
    
    # Categorias padrão
    print("📁 Criando categorias...")
    categories = {}
    
    default_categories = [
        {"name": "Alimentação", "description": "Mercado, supermercado, restaurantes"},
        {"name": "Transporte", "description": "Uber, ônibus, combustível"},
        {"name": "Lazer", "description": "Cinema, festas, diversão"},
        {"name": "Moradia", "description": "Aluguel, condomínio, contas"},
        {"name": "Saúde", "description": "Farmácia, consultas médicas"},
        {"name": "Delivery", "description": "iFood, Rappi, pedidos"},
    ]
    
    for cat in default_categories:
        # Verifica se já existe
        existing = SQLTool.get_category_by_name(user_id, cat["name"])
        if existing:
            categories[cat["name"]] = existing
            print(f"  ✓ Categoria '{cat['name']}' já existe")
        else:
            cat_id = SQLTool.create_category(user_id, cat["name"], cat["description"])
            categories[cat["name"]] = {"category_id": cat_id, "category_name": cat["name"]}
            print(f"  ✓ Categoria '{cat['name']}' criada (ID: {cat_id})")
    
    # Transações de exemplo - distribuídas em diferentes períodos
    print("\n💰 Criando transações de exemplo...")
    
    now = datetime.now()
    
    # Transações de hoje
    today_transactions = [
        {"category": "Alimentação", "amount": 45.50, "description": "Almoço no restaurante"},
        {"category": "Transporte", "amount": 15.00, "description": "Uber para o trabalho"},
    ]
    
    # Transações desta semana (últimos 7 dias)
    week_transactions = [
        {"category": "Delivery", "amount": 32.90, "description": "iFood - pizza", "days_ago": 2},
        {"category": "Lazer", "amount": 50.00, "description": "Cinema", "days_ago": 3},
        {"category": "Alimentação", "amount": 120.00, "description": "Supermercado", "days_ago": 5},
    ]
    
    # Transações deste mês
    month_transactions = [
        {"category": "Moradia", "amount": 1500.00, "description": "Aluguel", "days_ago": 10},
        {"category": "Saúde", "amount": 85.00, "description": "Farmácia", "days_ago": 12},
        {"category": "Transporte", "amount": 200.00, "description": "Combustível", "days_ago": 15},
        {"category": "Alimentação", "amount": 250.00, "description": "Supermercado mensal", "days_ago": 18},
        {"category": "Lazer", "amount": 80.00, "description": "Bar com amigos", "days_ago": 20},
        # Transação que vai exceder limite de Lazer (300) para testar alerta
        {"category": "Lazer", "amount": 150.00, "description": "Show de música", "days_ago": 22},
    ]
    
    # Transações antigas (mais de 1 mês)
    old_transactions = [
        {"category": "Alimentação", "amount": 180.00, "description": "Supermercado", "days_ago": 45},
        {"category": "Transporte", "amount": 150.00, "description": "Combustível", "days_ago": 50},
    ]
    
    all_transactions = (
        [(t, now.replace(hour=14, minute=30, second=0)) for t in today_transactions] +
        [(t, now - timedelta(days=t["days_ago"])) for t in week_transactions] +
        [(t, now - timedelta(days=t["days_ago"])) for t in month_transactions] +
        [(t, now - timedelta(days=t["days_ago"])) for t in old_transactions]
    )
    
    for trans, trans_date in all_transactions:
        category_name = trans["category"]
        if category_name in categories:
            cat_id = categories[category_name]["category_id"]
            # Insere com data específica
            with get_connection() as conn:
                conn.execute(
                    """INSERT INTO transactions 
                       (user_phone, category_id, amount, expense_description, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, cat_id, trans["amount"], trans["description"], trans_date)
                )
                conn.commit()
            print(f"  ✓ Transação: R$ {trans['amount']:.2f} em {category_name} ({trans_date.strftime('%d/%m/%Y')})")
    
    # Limites configurados
    print("\n📊 Configurando limites...")
    
    limits = [
        {"category": "Alimentação", "limit": 2000.00, "period": "mensal"},
        {"category": "Transporte", "limit": 500.00, "period": "mensal"},
        {"category": "Lazer", "limit": 300.00, "period": "mensal"},  # Limite que será excedido (280 já gasto)
    ]
    
    for limit_info in limits:
        category_name = limit_info["category"]
        if category_name in categories:
            cat_id = categories[category_name]["category_id"]
            
            # Verifica se já existe limite
            rules = SQLTool.get_active_rules(user_id)
            existing = any(r["category_id"] == cat_id for r in rules)
            
            if not existing:
                rule_id = SQLTool.create_limit_rule(
                    user_id,
                    cat_id,
                    limit_info["period"],
                    limit_info["limit"]
                )
                
                # Atualiza current_total baseado nas transações do mês
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                current_total = SQLTool.get_total_by_category(user_id, cat_id, start_date, now)
                SQLTool.update_rule_total(rule_id, current_total)
                
                print(f"  ✓ Limite de {category_name}: R$ {limit_info['limit']:.2f} ({limit_info['period']})")
    
    print("\n✅ Base de dados populada com sucesso!")
    print(f"\n📋 Resumo:")
    print(f"   • Usuário: {user_id}")
    print(f"   • Categorias: {len(categories)}")
    print(f"   • Transações: {len(all_transactions)}")
    print(f"   • Limites: {len(limits)}")
    print(f"\n💡 Agora você pode testar todas as funcionalidades do bot!")


if __name__ == "__main__":
    # Permite passar user_id como argumento
    user_id = sys.argv[1] if len(sys.argv) > 1 else "123456789"
    populate_test_cases(user_id)

