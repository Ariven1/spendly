import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spendly.db"
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (
                "Demo User",
                "demo@spendly.com",
                generate_password_hash("demo123", method="pbkdf2:sha256"),
            ),
        )
        user_id = cur.lastrowid

        today = date.today()

        def day(n):
            return today.replace(day=n).strftime("%Y-%m-%d")

        expenses = [
            (user_id, 45.50, "Food", day(1), "Groceries"),
            (user_id, 12.00, "Transport", day(3), "Metro pass top-up"),
            (user_id, 120.00, "Bills", day(5), "Electricity bill"),
            (user_id, 30.00, "Health", day(8), "Pharmacy"),
            (user_id, 25.00, "Entertainment", day(11), "Movie night"),
            (user_id, 79.99, "Shopping", day(14), "New sneakers"),
            (user_id, 15.00, "Other", day(17), "Gift wrap and cards"),
            (user_id, 18.75, "Food", day(20), "Dinner out"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            expenses,
        )
        conn.commit()
    finally:
        conn.close()
