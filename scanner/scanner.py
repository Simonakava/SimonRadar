from concurrent.futures import ThreadPoolExecutor, as_completed

from data.markets import get_eur_markets
from data.ohlcv import get_ohlcv

from scoring.volume import calculate_volume_ratio
from scoring.momentum import calculate_price_change
from scoring.score import calculate_score
from scoring.acceleration import calculate_volume_acceleration
from scoring.breakout import calculate_breakout
from scoring.risk import calculate_trade_plan
from scoring.quality import calculate_quality


# =========================================================
# CONFIGURATION
# =========================================================

MAX_WORKERS = 60

TIMEFRAME = "1h"

OHLCV_LIMIT = 100

# -----------------------------------------------------
# SEUILS VALIDÉS PAR BACKTEST (backtest/validation.py)
# Basés sur le SCORE BRUT (calculate_score), testés sur
# 341 trades hors échantillon :
#   score >= 70 -> PF 1.92, 93 trades, +37% cumulé
#   score >= 80 -> PF 2.48, 49 trades
#   score >= 85 -> PF 2.77, 34 trades (échantillon plus fragile)
# À re-valider périodiquement en relançant le backtest
# avec plus d'historique.
# -----------------------------------------------------

ENTRY_SCORE_THRESHOLD = 85
STRONG_SCORE_THRESHOLD = 80
WATCH_SCORE_THRESHOLD = 70

MAX_RISK_ENTRY = 3.0
MAX_RISK_STRONG = 4.0


# =========================================================
# ANALYSE D'UN MARCHÉ
# =========================================================

def analyze_symbol(symbol):

    try:

        candles = get_ohlcv(
            symbol,
            timeframe=TIMEFRAME,
            limit=OHLCV_LIMIT
        )

        if candles is None:
            return None

        if len(candles) < 50:
            return None

        volume_ratio = calculate_volume_ratio(candles)

        if volume_ratio is None:
            return None

        momentum = calculate_price_change(
            candles,
            periods=24
        )

        if momentum is None:
            return None

        acceleration = calculate_volume_acceleration(candles)

        if acceleration is None:
            return None

        breakout = calculate_breakout(
            candles,
            periods=20
        )

        if breakout is None:
            return None

        score = calculate_score(
            volume_ratio,
            momentum,
            acceleration,
            breakout
        )

        trade_plan = calculate_trade_plan(candles)

        if trade_plan is None:
            return None

        risk_percent = trade_plan.get("risk_percent")

        if risk_percent is None:
            return None

        quality = calculate_quality(
            volume_ratio,
            momentum,
            acceleration,
            breakout,
            risk_percent
        )

        combined_score = (
            score * 0.65
            + quality * 0.35
        )

        # -------------------------------------------------
        # CLASSIFICATION — basée sur le score brut validé
        # par backtest, pas sur le combined_score.
        # -------------------------------------------------

        if (
            score >= ENTRY_SCORE_THRESHOLD
            and risk_percent <= MAX_RISK_ENTRY
        ):
            classification = "ENTRY"

        elif (
            score >= STRONG_SCORE_THRESHOLD
            and risk_percent <= MAX_RISK_STRONG
        ):
            classification = "STRONG"

        elif score >= WATCH_SCORE_THRESHOLD:
            classification = "WATCH"

        else:
            classification = "WEAK"

        return {
            "symbol": symbol,
            "score": score,
            "quality": quality,
            "combined_score": round(combined_score, 2),
            "classification": classification,
            "volume_ratio": volume_ratio,
            "momentum": momentum,
            "acceleration": acceleration,
            "breakout": breakout,
            "trade_plan": trade_plan
        }

    except Exception:
        return None


# =========================================================
# SCAN DE TOUS LES MARCHÉS
# =========================================================

def scan_market():

    markets = get_eur_markets()

    total = len(markets)

    results = []

    completed = 0

    print()
    print("=" * 70)
    print("SIMON RADAR — SCAN COMPLET")
    print("=" * 70)
    print()

    print(f"Marchés disponibles : {total}")
    print(f"Analyse parallèle   : {MAX_WORKERS} workers")
    print(
        f"Seuils (validés backtest) : "
        f"ENTRY score>={ENTRY_SCORE_THRESHOLD} | "
        f"STRONG score>={STRONG_SCORE_THRESHOLD} | "
        f"WATCH score>={WATCH_SCORE_THRESHOLD}"
    )
    print()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = {
            executor.submit(analyze_symbol, symbol): symbol
            for symbol in markets
        }

        for future in as_completed(futures):

            completed += 1

            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception:
                pass

            percentage = completed / total * 100 if total else 100

            print(
                f"\rAnalyse : {completed}/{total} ({percentage:.1f}%)",
                end="",
                flush=True
            )

    print()
    print()

    # -----------------------------------------------------
    # TRI PRINCIPAL
    # -----------------------------------------------------

    results.sort(
        key=lambda r: (
            -r["score"],
            -r["quality"],
            -r["combined_score"],
            -r["volume_ratio"]
        )
    )

    print(f"Résultats exploitables : {len(results)}/{total}")
    print()

    return results