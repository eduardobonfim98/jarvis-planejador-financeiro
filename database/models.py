"""Gerenciamento do banco de dados SQLite para o Jarvis."""

import sqlite3
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os

# Garantir que variáveis de ambiente estejam carregadas (útil em scripts isolados)
load_dotenv()

# Caminho padrão do banco
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "jarvis.db"))


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Retorna uma conexão com o banco de dados SQLite.

    Parameters
    ----------
    db_path: Optional[Path]
        Caminho alternativo para o arquivo SQLite. Se não for informado,
        utiliza o caminho padrão definido em `DATABASE_PATH`.
    """
    target = Path(db_path) if db_path else DATABASE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    return connection


def init_database(db_path: Optional[Path] = None) -> None:
    """
    Cria as tabelas necessárias para o funcionamento do Jarvis.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_phone TEXT PRIMARY KEY,
                user_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_message_at DATETIME,
                days_inactive INTEGER DEFAULT 0,
                notify_opt_in INTEGER DEFAULT 1,
                notify_hour INTEGER DEFAULT 22
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT,
                category_name TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_phone) REFERENCES users(user_phone)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT,
                category_id INTEGER,
                amount REAL,
                expense_description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_phone) REFERENCES users(user_phone),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT,
                category_id INTEGER,
                period_type TEXT DEFAULT 'mensal',
                period_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                period_end DATETIME,
                limit_value REAL,
                current_total REAL DEFAULT 0,
                last_updated DATETIME,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (user_phone) REFERENCES users(user_phone),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
            """
        )

        conn.commit()


def save_message(user_phone: str, message_text: str, db_path: Optional[Path] = None) -> None:
    """
    Exemplo de uso do banco: salva uma interação simples do usuário.

    - Garante que o usuário exista na tabela `users`.
    - Atualiza o campo `last_message_at`.
    - Registra a mensagem como uma transação com valor 0 (placeholder).
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users (user_phone, user_name, last_message_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_phone) DO UPDATE SET last_message_at=CURRENT_TIMESTAMP
            """,
            (user_phone, None),
        )

        cursor.execute(
            """
            INSERT INTO transactions (user_phone, category_id, amount, expense_description)
            VALUES (?, NULL, ?, ?)
            """,
            (user_phone, 0.0, message_text),
        )

        conn.commit()
