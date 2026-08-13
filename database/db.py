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
COOLDOWN_HOURS = 24
FLAT_THRESHOLD_PERCENT = 0.1


def get_client():
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise RuntimeError("TURSO_DATABASE_URL et TURSO_AUTH_TOKEN doivent etre definis (fichier .env ou variables d'environnement).")
    return libsql_client.create_client_sync(url=TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)


SQL_CREATE_SCANS = "CREATE TABLE IF NOT EXISTS scans (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, symbol TEXT NOT NULL, score INTEGER NOT NULL, quality INTEGER NOT NULL, combined_score REAL NOT NULL, classification TEXT NOT NULL, volume_ratio REAL, momentum REAL, acceleration REAL, breakout REAL, entry_price REAL, risk_percent REAL)"

SQL_CREATE_PAPER_TRADES = "CREATE TABLE IF NOT EXISTS paper_trades (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL, classification TEXT NOT NULL, score INTEGER NOT NULL, entry_timestamp TEXT NOT NULL, entry_price REAL NOT NULL, stop_loss REAL NOT NULL, take_profit_1 REAL NOT NULL, take_profit_2 REAL NOT NULL, status TEXT NOT NULL, result TEXT, closed_price REAL, closed_timestamp TEXT, return_percent REAL)"

SQL_INSERT_SCAN = "INSERT INTO scans (timestamp, symbol, score, quality, combined_score, classification, volume_ratio, momentum, acceleration, breakout, entry_price, risk_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

SQL_COUNT_SCANS = "SELECT COUNT(DISTINCT timestamp) FROM scans"

SQL_CHECK_EXISTING_TRADE = "SELECT id FROM paper_trades WHERE symbol = ? AND entry_timestamp >= ?"

SQL_INSERT_PAPER_TRADE = "INSERT INTO paper_trades (symbol, classification, score, entry_timestamp, entry_price, stop_loss, take_profit_1, take_profit_2, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')"

SQL_SELECT_OPEN_TRADES = "SELECT id, symbol, entry_timestamp, entry_price, stop_loss, take_profit_1, take_profit_2 FROM paper_trades WHERE status = 'OPEN'"

SQL_UPDATE_CLOSE_TRADE = "UPDATE paper_trades SET status = 'CLOSED', result = ?, closed_price = ?, closed_timestamp = ?, return_percent = ? WHERE id = ?"

SQL_SELECT_OPEN_TRADES_FULL = "SELECT id, symbol, classification, score, entry_timestamp, entry_price, stop_loss, take_profit_1, take_profit_2 FROM paper_trades WHERE status = 'OPEN' ORDER BY entry_timestamp DESC"

SQL_SELECT_CLOSED_TRADES = "SELECT result, return_percent FROM paper_trades WHERE status = 'CLOSED'"


def init_db():
    client = get_client()
    client.execute(SQL_CREATE_SCANS)
    client.execute(SQL_CREATE_PAPER_TRADES)
    client.close()


def save_scan_results(results):
    if not results:
        return

    init_db()
    timestamp = datetime.now().isoformat()
    client = get_client()

    for r in results:
        trade_plan = r.get("trade_plan") or {}
        client.execute(SQL_INSERT_SCAN, [
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
        ])

    client.close()
    print(f"Scan sauvegarde en base : {len(results)} marches ({timestamp})")


def get_scan_count():
    init_db()
    client = get_client()
    result_set = client.execute(SQL_COUNT_SCANS)
    count = result_set.rows[0][0]
    client.close()
    return count


def open_paper_trades(results):
    init_db()

    candidates = [r for r in results if r["classification"] in ("STRONG", "ENTRY")]

    if not candidates:
        return 0

    client = get_client()
    now = datetime.now()
    cooldown_limit = (now - timedelta(hours=COOLDOWN_HOURS)).isoformat()
    opened = 0

    for r in candidates:
        symbol = r["symbol"]
        trade_plan = r.get("trade_plan") or {}

        existing = client.execute(SQL_CHECK_EXISTING_TRADE, [symbol, cooldown_limit])

        if existing.rows:
            continue

        client.execute(SQL_INSERT_PAPER_TRADE, [
            symbol,
            r["classification"],
            r["score"],
            now.isoformat(),
            trade_plan.get("entry"),
            trade_plan.get("stop_loss"),
            trade_plan.get("take_profit_1"),
            trade_plan.get("take_profit_2")
        ])

        opened += 1

    client.close()

    if opened:
        print(f"Paper trading : {opened} nouvelle(s) position(s) fictive(s) ouverte(s)")

    return opened


def _resolve_trade(entry_price, stop_loss, tp1, tp2, candles_since_entry):
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
    init_db()
    client = get_client()

    open_trades = client.execute(SQL_SELECT_OPEN_TRADES)

    if not open_trades.rows:
        client.close()
        return 0

    closed_count = 0
    now = datetime.now()

    for row in open_trades.rows:
        trade_id, symbol, entry_ts_str, entry_price, stop_loss, tp1, tp2 = row

        entry_ts = datetime.fromisoformat(entry_ts_str)
        elapsed_hours = (now - entry_ts).total_seconds() / 3600

        limit = min(int(elapsed_hours) + 2, 100)

        try:
            candles = get_ohlcv(symbol, timeframe="1h", limit=limit)
        except Exception:
            continue

        if not candles:
            continue

        candles_since_entry = [c for c in candles if c[0] >= int(entry_ts.timestamp() * 1000)]

        result, closed_price = _resolve_trade(entry_price, stop_loss, tp1, tp2, candles_since_entry)

        timeout = elapsed_hours >= MAX_HOLDING_HOURS

        if result is None and not timeout:
            continue

        if result is None and timeout:
            result = "TIMEOUT"
            closed_price = candles[-1][4]

        return_percent = ((closed_price - entry_price) / entry_price) * 100

        client.execute(SQL_UPDATE_CLOSE_TRADE, [result, closed_price, now.isoformat(), return_percent, trade_id])

        closed_count += 1

    client.close()

    if closed_count:
        print(f"Paper trading : {closed_count} position(s) cloturee(s)")

    return closed_count


def get_open_paper_trades_with_current_price():
    init_db()
    client = get_client()

    open_trades = client.execute(SQL_SELECT_OPEN_TRADES_FULL)

    client.close()

    if not open_trades.rows:
        return []

    now = datetime.now()
    positions = []

    for row in open_trades.rows:
        trade_id, symbol, classification, score, entry_ts_str, entry_price, stop_loss, tp1, tp2 = row

        entry_ts = datetime.fromisoformat(entry_ts_str)
        elapsed_hours = (now - entry_ts).total_seconds() / 3600

        try:
            candles = get_ohlcv(symbol, timeframe="1h", limit=1)
            current_price = candles[-1][4] if candles else None
        except Exception:
            current_price = None

        if current_price is None:
            trend = "inconnu"
            change_percent = None
        else:
            change_percent = ((current_price - entry_price) / entry_price) * 100

            if change_percent > FLAT_THRESHOLD_PERCENT:
                trend = "hausse"
            elif change_percent < -FLAT_THRESHOLD_PERCENT:
                trend = "baisse"
            else:
                trend = "stagne"

        positions.append({
            "symbol": symbol,
            "classification": classification,
            "score": score,
            "entry_price": entry_price,
            "current_price": current_price,
            "change_percent": change_percent,
            "trend": trend,
            "stop_loss": stop_loss,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "elapsed_hours": elapsed_hours
        })

    return positions


def get_paper_trading_stats():
    init_db()
    client = get_client()

    result_set = client.execute(SQL_SELECT_CLOSED_TRADES)

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
    profit_factor = sum(positive) / sum(negative) if negative else 999

    return {
        "trades": len(rows),
        "win_rate": win_rate,
        "average": average,
        "total": total,
        "profit_factor": profit_factor
    }