import os
from datetime import datetime, timedelta
from pathlib import Path

import libsql_client
from dotenv import load_dotenv

from data.ohlcv import get_ohlcv


load_dotenv(Path(__file__).parent.parent / ".env")

TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

MAX_HOLDING_HOURS = 24
COOLDOWN_HOURS = 24  # pas de nouvelle position fictive sur le même marché avant 24h


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

    client.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            classification TEXT NOT NULL,
            score INTEGER NOT NULL,
            entry_timestamp TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            take_profit_1 REAL NOT NULL,
            take_profit_2 REAL NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            closed_price REAL,
            closed_timestamp TEXT,
            return_percent REAL
        )
    """)

    client.close()


# =========================================================
# SCANS — historique brut
# =========================================================

def save_scan_results(results):

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


# =========================================================
# PAPER TRADING — simulation sur 24h max
# =========================================================

def open_paper_trades(results):
    """
    Ouvre une position fictive pour chaque résultat STRONG/ENTRY,
    sauf si une position existe déjà sur ce symbole dans les
    dernières COOLDOWN_HOURS heures (ouverte ou clôturée).
    """

    init_db()

    candidates = [
        r for r in results
        if r["classification"] in ("STRONG", "ENTRY")
    ]

    if not candidates:
        return 0

    client = get_client()

    now = datetime.now()
    cooldown_limit = (now - timedelta(hours=COOLDOWN_HOURS)).isoformat()

    opened = 0

    for r in candidates:

        symbol = r["symbol"]
        trade_plan = r.get("trade_plan") or {}

        # Vérifie qu'aucune position (ouverte ou récente) n'existe déjà
        existing = client.execute(
            """
            SELECT id FROM paper_trades
            WHERE symbol = ?
              AND entry_timestamp >= ?
            """,
            [symbol, cooldown_limit]
        )

        if existing.rows:
            continue

        client.execute(
            """
            INSERT INTO paper_trades (
                symbol, classification, score, entry_timestamp,
                entry_price, stop_loss, take_profit_1, take_profit_2,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """,
            [
                symbol,
                r["classification"],
                r["score"],
                now.isoformat(),
                trade_plan.get("entry"),
                trade_plan.get("stop_loss"),
                trade_plan.get("take_profit_1"),
                trade_plan.get("take_profit_2")
            ]
        )

        opened += 1

    client.close()

    if opened:
        print(f"Paper trading : {opened} nouvelle(s) position(s) fictive(s) ouverte(s)")

    return opened


def _resolve_trade(entry_price, stop_loss, tp1, tp2, candles_since_entry):
    """
    Parcourt les bougies depuis l'entrée et détermine si TP1/TP2/stop
    ont été touchés, dans cet ordre chronologique.
    Retourne (result, closed_price) ou (None, None) si rien touché encore.
    """

    tp1_hit = False

    for candle in candles_since_entry:

        high = candle[2]
        low = candle[3]

        if not tp1_hit and high >= tp1:
            tp1_hit = True

        if high >= tp2:
            return "TP2", tp2

        if low <= stop_loss:
            if tp1_hit:
                return "TP1_STOP", stop_loss
            return "STOP", stop_loss

    return None, None


def update_paper_trades():
    """
    Vérifie toutes les positions OPEN : clôture celles qui ont touché
    TP1/TP2/stop, ou qui dépassent MAX_HOLDING_HOURS (timeout).
    """

    init_db()

    client = get_client()

    open_trades = client.execute(
        """
        SELECT id, symbol, entry_timestamp, entry_price,
               stop_loss, take_profit_1, take_profit_2
        FROM paper_trades
        WHERE status = 'OPEN'
        """
    )

    if not open_trades.rows:
        client.close()
        return 0

    closed_count = 0
    now = datetime.now()

    for row in open_trades.rows:

        trade_id, symbol, entry_ts_str, entry_price, stop_loss, tp1, tp2 = row

        entry_ts = datetime.fromisoformat(entry_ts_str)
        elapsed_hours = (now - entry_ts).total_seconds() / 3600

        # Récupère les bougies depuis l'entrée (+ marge de 2h)
        limit = min(int(elapsed_hours) + 2, 100)

        try:
            candles = get_ohlcv(symbol, timeframe="1h", limit=limit)
        except Exception:
            continue

        if not candles:
            continue

        # Ne garde que les bougies postérieures à l'entrée
        candles_since_entry = [
            c for c in candles
            if c[0] >= int(entry_ts.timestamp() * 1000)
        ]

        result, closed_price = _resolve_trade(
            entry_price, stop_loss, tp1, tp2, candles_since_entry
        )

        timeout = elapsed_hours >= MAX_HOLDING_HOURS

        if result is None and not timeout:
            continue  # toujours en cours, rien à faire

        if result is None and timeout:
            result = "TIMEOUT"
            closed_price = candles[-1][4]  # dernier prix de clôture connu

        return_percent = (
            (closed_price - entry_price) / entry_price
        ) * 100

        client.execute(
            """
            UPDATE paper_trades
            SET status = 'CLOSED',
                result = ?,
                closed_price = ?,
                closed_timestamp = ?,
                return_percent = ?
            WHERE id = ?
            """,
            [result, closed_price, now.isoformat(), return_percent, trade_id]
        )

        closed_count += 1

    client.close()

    if closed_count:
        print(f"Paper trading : {closed_count} position(s) clôturée(s)")

    return closed_count


def get_paper_trading_stats():
    """
    Statistiques sur les positions fictives clôturées.
    """

    init_db()

    client = get_client()

    result_set = client.execute(
        """
        SELECT result, return_percent
        FROM paper_trades
        WHERE status = 'CLOSED'
        """
    )

    client.close()

    rows = result_set.rows

    if not rows:
        return None

    returns = [r[1] for r in rows]

    wins = [r for r in rows if r[0] in ("TP2", "TP1_STOP", "TP1_TIMEOUT")]

    positive = [r for r in returns if r > 0]
    negative = [abs(r) for r in returns if r < 0]

    total = sum(returns)
    average = total / len(returns)

    win_rate = (len(wins) / len(rows)) * 100

    profit_factor = (
        sum(positive) / sum(negative)
        if negative
        else 999
    )

    return {
        "trades": len(rows),
        "win_rate": win_rate,
        "average": average,
        "total": total,
        "profit_factor": profit_factor
    }