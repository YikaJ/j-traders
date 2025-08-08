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


def _has_column(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols


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
            selection TEXT,
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

    # Universe securities table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS securities (
            ts_code TEXT PRIMARY KEY,
            sec_type TEXT NOT NULL,
            symbol TEXT,
            name TEXT,
            area TEXT,
            industry TEXT,
            market TEXT,
            exchange TEXT,
            list_status TEXT,
            list_date TEXT,
            delist_date TEXT,
            is_hs TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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


# Factors/Strategies CRUD helpers (existing)

def insert_factor(name: str, desc: Optional[str], code_text: str, fields_used: List[str], normalization: Optional[Dict[str, Any]], tags: Optional[List[str]], selection: Optional[Dict[str, Any]] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO factors (name, desc, code_text, fields_used, normalization, tags, selection) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, desc, code_text, to_json(fields_used), to_json(normalization), to_json(tags), to_json(selection)),
    )
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return int(last_id)


def get_factor(factor_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM factors WHERE id = ?", (factor_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "desc": row["desc"],
        "code_text": row["code_text"],
        "fields_used": from_json(row["fields_used"]),
        "normalization": from_json(row["normalization"]),
        "tags": from_json(row["tags"]),
        "selection": from_json(row["selection"]),
        "created_at": row["created_at"],
    }


def list_factors() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM factors ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "desc": r["desc"],
            "code_text": r["code_text"],
            "fields_used": from_json(r["fields_used"]),
            "normalization": from_json(r["normalization"]),
            "tags": from_json(r["tags"]),
            "selection": from_json(r["selection"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def insert_strategy(name: str, normalization: Optional[Dict[str, Any]]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO strategies (name, normalization) VALUES (?, ?)",
        (name, to_json(normalization)),
    )
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return int(last_id)


def get_strategy(strategy_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    # weights
    cur.execute("SELECT factor_id, weight FROM strategy_factors WHERE strategy_id = ?", (strategy_id,))
    weights = [{"factor_id": r[0], "weight": float(r[1])} for r in cur.fetchall()]
    conn.close()
    return {
        "id": row["id"],
        "name": row["name"],
        "normalization": from_json(row["normalization"]),
        "created_at": row["created_at"],
        "weights": weights,
    }


def upsert_strategy_weights(strategy_id: int, weights: List[Tuple[int, float]]) -> None:
    conn = get_conn()
    cur = conn.cursor()
    for fid, w in weights:
        cur.execute(
            "INSERT INTO strategy_factors (strategy_id, factor_id, weight) VALUES (?, ?, ?) ON CONFLICT(strategy_id, factor_id) DO UPDATE SET weight=excluded.weight",
            (strategy_id, fid, w),
        )
    conn.commit()
    conn.close()


def update_strategy_normalization(strategy_id: int, normalization: Dict[str, Any]) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE strategies SET normalization=? WHERE id=?", (to_json(normalization), strategy_id))
    conn.commit()
    conn.close()


# Universe helpers

def bulk_upsert_securities(rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0
    conn = get_conn()
    cur = conn.cursor()
    for r in rows:
        cur.execute(
            """
            INSERT INTO securities (ts_code, sec_type, symbol, name, area, industry, market, exchange, list_status, list_date, delist_date, is_hs, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(ts_code) DO UPDATE SET
              sec_type=excluded.sec_type,
              symbol=excluded.symbol,
              name=excluded.name,
              area=excluded.area,
              industry=excluded.industry,
              market=excluded.market,
              exchange=excluded.exchange,
              list_status=excluded.list_status,
              list_date=excluded.list_date,
              delist_date=excluded.delist_date,
              is_hs=excluded.is_hs,
              updated_at=CURRENT_TIMESTAMP
            """,
            (
                r.get("ts_code"),
                r.get("sec_type", "stock"),
                r.get("symbol"),
                r.get("name"),
                r.get("area"),
                r.get("industry"),
                r.get("market"),
                r.get("exchange"),
                r.get("list_status"),
                r.get("list_date"),
                r.get("delist_date"),
                r.get("is_hs"),
            ),
        )
    conn.commit()
    n = conn.total_changes
    conn.close()
    return n


def query_stocks(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    clauses = []
    params: List[Any] = []
    if (v := filters.get("industry")):
        clauses.append("industry = ?")
        params.append(v)
    if (v := filters.get("market")):
        clauses.append("market = ?")
        params.append(v)
    if (v := filters.get("list_status")):
        clauses.append("list_status = ?")
        params.append(v)
    if (v := filters.get("exchange")):
        clauses.append("exchange = ?")
        params.append(v)
    if (v := filters.get("is_hs")):
        clauses.append("is_hs = ?")
        params.append(v)
    if (v := filters.get("q")):
        clauses.append("(ts_code LIKE ? OR name LIKE ? OR symbol LIKE ?)")
        like = f"%{v}%"
        params.extend([like, like, like])
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM securities {where} ORDER BY ts_code"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stock(ts_code: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM securities WHERE ts_code = ?", (ts_code,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
