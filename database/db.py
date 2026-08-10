import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent / "simon_radar.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            score INTEGER NOT NULL,
            quality INTEGER NOT NULL,
            combined_score REAL NOT NULL,
            classification TEXT NOT NULL,
            volume_ratio REAL,
            momentum REAL,
            acceleration REAL,
            breakout REAL,
            entry_price REAL,
            risk_percent REAL
        )
    """)

    conn.commit()
    conn.close()


def save_scan_results(results):
    """
    Sauvegarde tous les résultats d'un scan avec un timestamp commun.
    Appelée après chaque scan_market() dans main.py.
    """

    if not results:
        return

    init_db()

    timestamp = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    for r in results:

        trade_plan = r.get("trade_plan") or {}

        cursor.execute("""
            INSERT INTO scans (
                timestamp, symbol, score, quality, combined_score,
                classification, volume_ratio, momentum, acceleration,
                breakout, entry_price, risk_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            r["symbol"],
            r["score"],
            r["quality"],
            r["combined_score"],
            r["classification"],
            r.get("volume_ratio"),
            r.get("momentum"),
            r.get("acceleration"),
            r.get("breakout"),
            trade_plan.get("entry"),
            trade_plan.get("risk_percent")
        ))

    conn.commit()
    conn.close()

    print(f"Scan sauvegardé en base : {len(results)} marchés ({timestamp})")


def get_scan_count():

    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT timestamp) FROM scans")
    count = cursor.fetchone()[0]

    conn.close()

    return count