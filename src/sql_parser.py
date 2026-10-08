import sqlite3
from typing import List, Tuple, Any
from pathlib import Path

class SQLiteParser:

    def __init__(self, db_path: Path|str = "demo_sqlite.db"):
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        # Skapar en enkel tabell för demonstration
        cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            name TEXT PRIMARY KEY,
            quantity REAL,
            unit TEXT
        )
        """)
        self.conn.commit()

    def execute(self, query: str) -> List[Tuple[Any]]:
        """executear ett SQL-kommando och returnerar resultatet."""
        query = query.strip()
        cur = self.conn.cursor()
        try:
            cur.execute(query)
            if query.lower().startswith("select"):
                result = cur.fetchall()
            else:
                self.conn.commit()
                result = [("OK",)]
        except sqlite3.Error as e:
            result = [(f"Fel: {e}",)]
        return result

    # Hjälpfunktioner för att efterlikna pickle-metoder
    def insert(self, name: str, quantity: float, unit: str):
        with self.conn:
            self.conn.execute("""
                INSERT INTO inventory (name, quantity, unit)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    quantity = excluded.quantity,
                    unit = excluded.unit
            """, (name, quantity, unit))

    def list_items(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name, quantity, unit FROM inventory ORDER BY name")
        return cur.fetchall()

    def remove(self, name: str):
        with self.conn:
            self.conn.execute("DELETE FROM inventory WHERE name=?", (name,))
