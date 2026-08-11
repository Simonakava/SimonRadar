import os
from datetime import datetime
from pathlib import Path

import libsql_client
from dotenv import load_dotenv


# Charge les variables du fichier .env à la racine du projet
load_dotenv(Path(__file__).parent.parent / ".env")

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")


def get_client():

    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise RuntimeError(
            "TURSO_DATABASE_URL et TURSO_AUTH_TOKEN doivent être "
            "définis (fichier .env ou variables d'environnement)."
        )

    return libsql_client.create_client_sync(
        url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )


def init_db():

    client = get_client()

    client.execute("""
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

    client.close()


def save_scan_results(results):
    """
    Sauvegarde tous les résultats d'un scan avec un timestamp commun.
    Appelée après chaque scan_market() dans main.py.
    """

    if not results:
        return

    init_db()

    timestamp = datetime.now().isoformat()

    client = get_client()

    for r in results:

        trade_plan = r.get("trade_plan") or {}

        client.execute(
            """
            INSERT INTO scans (
                timestamp, symbol, score, quality, combined_score,
                classification, volume_ratio, momentum, acceleration,
                breakout, entry_price, risk_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
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
            ]
        )

    client.close()

    print(f"Scan sauvegardé en base : {len(results)} marchés ({timestamp})")


def get_scan_count():

    init_db()

    client = get_client()

    result_set = client.execute(
        "SELECT COUNT(DISTINCT timestamp) FROM scans"
    )

    count = result_set.rows[0][0]

    client.close()

    return count