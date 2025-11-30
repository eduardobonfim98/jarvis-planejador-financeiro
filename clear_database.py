#!/usr/bin/env python3
"""
Script para limpar todas as tabelas do banco de dados.
Remove todos os dados mas mantém a estrutura das tabelas.

Uso:
    python clear_database.py          # Com confirmação
    python clear_database.py --yes    # Sem confirmação (automático)
"""

import sys
from pathlib import Path

from database.models import get_connection, DATABASE_PATH


def clear_database(verbose: bool = True):
    """Limpa todas as tabelas do banco de dados.
    
    Parameters
    ----------
    verbose: bool
        Se True, imprime mensagens de progresso.
    """
    if verbose:
        print(f"🧹 Limpando banco de dados: {DATABASE_PATH}")
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Ordem de deleção considerando foreign keys
            # Deletar na ordem inversa das dependências
            tables = [
                "conversation_history",
                "user_rules",
                "transactions",
                "categories",
                "users"
            ]
            
            total_deleted = 0
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                count = cursor.rowcount
                total_deleted += count
                if verbose:
                    print(f"  ✅ Limpou {count} registros da tabela '{table}'")
            
            # Resetar autoincrement dos IDs
            tables_with_autoincrement = ["categories", "transactions", "user_rules", "conversation_history"]
            for table in tables_with_autoincrement:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            
            conn.commit()
            
            if verbose:
                print(f"\n✅ Banco de dados limpo com sucesso!")
                print(f"   Total de registros deletados: {total_deleted}")
                print(f"   Arquivo: {DATABASE_PATH.absolute()}")
            
            return total_deleted
            
    except Exception as e:
        if verbose:
            print(f"\n❌ Erro ao limpar banco de dados: {e}")
        raise


if __name__ == "__main__":
    # Verificar se foi passado --yes para pular confirmação
    skip_confirmation = "--yes" in sys.argv or "-y" in sys.argv
    
    if not skip_confirmation:
        print("⚠️  ATENÇÃO: Isso irá deletar TODOS os dados do banco de dados!")
        print("   A estrutura das tabelas será mantida.\n")
        
        response = input("Tem certeza que deseja continuar? (sim/não): ").strip().lower()
        
        if response not in ["sim", "s", "yes", "y"]:
            print("❌ Operação cancelada.")
            sys.exit(0)
    
    clear_database()

