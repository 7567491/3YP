import sqlite3
import json
from pathlib import Path
from typing import Dict, Any

class DataStorage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS financial_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    indicator_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_json(self, data: Dict[str, Any], json_path: Path):
        """保存JSON数据"""
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_to_db(self, data: Dict[str, Any], year: int):
        """保存数据到SQLite数据库"""
        with sqlite3.connect(self.db_path) as conn:
            for indicator, value in data.items():
                if isinstance(value, (int, float)):
                    conn.execute(
                        "INSERT INTO financial_data (year, indicator_name, value) VALUES (?, ?, ?)",
                        (year, indicator, value)
                    ) 