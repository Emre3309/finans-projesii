import sqlite3
from contextlib import closing
from typing import Optional, List, Tuple, Dict

DB_PATH = "data.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,          -- ISO YYYY-MM-DD
                shop TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('gelir', 'gider')),
                amount REAL NOT NULL,
                note TEXT
            );
            """
        )
        # Hız için indeksler
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);")

def add_transaction(date_iso: str, shop: str, ttype: str, amount: float, note: str = "") -> int:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO transactions(date, shop, type, amount, note) VALUES (?, ?, ?, ?, ?);",
            (date_iso, shop, ttype, amount, note),
        )
        return cur.lastrowid

def delete_transaction(tx_id: int) -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM transactions WHERE id = ?;", (tx_id,))

def fetch_transactions(
    start: Optional[str] = None,
    end: Optional[str] = None,
    ttype: Optional[str] = None,
) -> List[Tuple]:
    sql = "SELECT id, date, shop, type, amount, note FROM transactions WHERE 1=1"
    params: List = []
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    if ttype in ("gelir", "gider"):
        sql += " AND type = ?"
        params.append(ttype)
    sql += " ORDER BY date ASC, id ASC"
    with closing(get_conn()) as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()

def summarize(start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, float]:
    sql = "SELECT type, SUM(amount) FROM transactions WHERE 1=1"
    params: List = []
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    sql += " GROUP BY type"
    income = 0.0
    expense = 0.0
    with closing(get_conn()) as conn:
        for ttype, total in conn.execute(sql, params).fetchall():
            if ttype == "gelir":
                income = total or 0.0
            elif ttype == "gider":
                expense = total or 0.0
    return {"gelir": income, "gider": expense, "kar": income - expense}

def group_by(period: str, start: Optional[str] = None, end: Optional[str] = None):
    """
    period: 'ay' veya 'hafta'
    returns: list of (label, gelir, gider, kar)
    """
    if period not in ("ay", "hafta"):
        raise ValueError("period 'ay' veya 'hafta' olmalı")
    # SQLite strftime: %Y-%m (ay), %Y-%W (hafta numarası)
    fmt = "%Y-%m" if period == "ay" else "%Y-W%W"
    sql = f"""
        SELECT strftime('{fmt}', date) AS bucket,
               SUM(CASE WHEN type='gelir' THEN amount ELSE 0 END) AS gelir,
               SUM(CASE WHEN type='gider' THEN amount ELSE 0 END) AS gider
        FROM transactions
        WHERE 1=1
    """
    params: list = []
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    sql += " GROUP BY bucket ORDER BY bucket ASC;"
    rows = []
    with closing(get_conn()) as conn:
        for bucket, gelir, gider in conn.execute(sql, params).fetchall():
            gelir = gelir or 0.0
            gider = gider or 0.0
            rows.append((bucket, gelir, gider, gelir - gider))
    return rows