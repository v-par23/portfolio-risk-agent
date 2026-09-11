"""Local persistence for the user's risk profile, watchlist, and holdings across sessions."""
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", ".data", "memory.db")


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            risk_tolerance TEXT,
            notes TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY,
            added_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            ticker TEXT PRIMARY KEY,
            shares REAL,
            cost_basis REAL,
            updated_at TEXT
        )
    """)
    return conn


def save_profile(risk_tolerance: str, notes: str = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO profile (id, risk_tolerance, notes, updated_at) VALUES (1, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET risk_tolerance = excluded.risk_tolerance, "
            "notes = excluded.notes, updated_at = excluded.updated_at",
            (risk_tolerance, notes, now),
        )
    return {"risk_tolerance": risk_tolerance, "notes": notes, "updated_at": now}


def get_profile() -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT risk_tolerance, notes, updated_at FROM profile WHERE id = 1"
        ).fetchone()
    if not row:
        return {"risk_tolerance": None, "notes": None, "updated_at": None}
    return {"risk_tolerance": row[0], "notes": row[1], "updated_at": row[2]}


def add_watchlist_ticker(ticker: str) -> list:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (ticker, added_at) VALUES (?, ?)",
            (ticker.upper(), now),
        )
    return get_watchlist()


def get_watchlist() -> list:
    with _connect() as conn:
        rows = conn.execute("SELECT ticker FROM watchlist ORDER BY added_at").fetchall()
    return [r[0] for r in rows]


def upsert_holding(ticker: str, shares: float, cost_basis: float) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO holdings (ticker, shares, cost_basis, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(ticker) DO UPDATE SET shares = excluded.shares, "
            "cost_basis = excluded.cost_basis, updated_at = excluded.updated_at",
            (ticker.upper(), shares, cost_basis, now),
        )
    return {"ticker": ticker.upper(), "shares": shares, "cost_basis": cost_basis}


def get_holdings() -> list:
    with _connect() as conn:
        rows = conn.execute("SELECT ticker, shares, cost_basis FROM holdings").fetchall()
    return [{"ticker": r[0], "shares": r[1], "cost_basis": r[2]} for r in rows]
