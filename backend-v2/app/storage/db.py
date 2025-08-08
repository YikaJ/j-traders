from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DATA_DIR / "app.db"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS factors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            desc TEXT,
            code_text TEXT NOT NULL,
            fields_used TEXT NOT NULL,
            normalization TEXT,
            tags TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            normalization TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS strategy_factors (
            strategy_id INTEGER NOT NULL,
            factor_id INTEGER NOT NULL,
            weight REAL NOT NULL,
            PRIMARY KEY (strategy_id, factor_id),
            FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE,
            FOREIGN KEY (factor_id) REFERENCES factors(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def from_json(text: Optional[str]) -> Any:
    if text is None:
        return None
    return json.loads(text)
