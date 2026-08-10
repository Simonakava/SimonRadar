import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from data.markets import get_eur_markets
from data.kraken import get_all_tickers
from data.ohlcv import get_ohlcv

from scoring.volume import calculate_volume_ratio
from scoring.acceleration import calculate_volume_acceleration
from scoring.breakout import calculate_breakout
from scoring.momentum import calculate_price_change
from scoring.score import calculate_score
from scoring.risk import calculate_atr


# ============================================================
# CONFIGURATION
# ============================================================

MIN_SCORE = 75

MAX_RESULTS = 10

# Nombre de cryptos envoyées à l'analyse OHLCV
MAX_CANDIDATES = 100

# Nombre de requêtes simultanées
MAX_WORKERS = 40


# ============================================================
# PRÉ-SÉLECTION
# ============================================================

def get_candidates(markets):

    print("Récupération des tickers...")

    tickers = get_all_tickers()

    candidates = []

    for symbol in markets:

        ticker = tickers.get(symbol)

        if not ticker:
            continue

        percentage = ticker.get("percentage")
        quote_volume = ticker.get("quoteVolume")
        last = ticker.get("last")

        if percentage is None:
            continue

        if quote_volume is None:
            continue

        if last is None:
            continue

        if quote_volume <= 0:
            continue

        # ----------------------------------------------------
        # PRÉ-SCORE VOLONTAIREMENT LARGE
        # ----------------------------------------------------

        momentum_score = max(
            0,
            min(
                percentage * 2,
                40
            )
        )

        volume_score = min(
            quote_volume / 250000,
            30
        )

        activity_score = min(
            abs(percentage),
            30
        )

        quick_score = (
            momentum_score
            + volume_score
            + activity_score
        )

        candidates.append({
            "symbol": symbol,
            "quick_score": quick_score,
            "percentage": percentage,
            "volume": quote_volume
        })

    candidates.sort(
        key=lambda x: x["quick_score"],
        reverse=True
    )

    return candidates[:MAX_CANDIDATES]


# ============================================================
# ANALYSE COMPLÈTE
# ============================================================

def analyse_market(candidate):

    symbol = candidate["symbol"]

    try:

        candles = get_ohlcv(
            symbol,
            timeframe="1h",
            limit=100
        )

        if candles is None:
            return None

        if len(candles) < 50:
            return None

        volume = calculate_volume_ratio(
            candles
        )

        acceleration = calculate_volume_acceleration(
            candles
        )

        momentum = calculate_price_change(
            candles,
            periods=24
        )

        breakout = calculate_breakout(
            candles,
            periods=20
        )

        atr = calculate_atr(
            candles
        )

        values = [
            volume,
            acceleration,
            momentum,
            breakout,
            atr
        ]

        if any(
            value is None
            for value in values
        ):
            return None

        if volume <= 0:
            return None

        if acceleration <= 0:
            return None

        score = calculate_score(
            volume,
            momentum,
            acceleration,
            breakout
        )

        if score is None:
            return None

        if score < MIN_SCORE:
            return None

        price = candles[-1][4]

        stop_distance = atr * 0.8

        if stop_distance <= 0:
            return None

        stop = price - stop_distance

        tp1 = price + (
            stop_distance * 1.33
        )

        tp2 = price + (
            stop_distance * 2.33
        )

        risk_percent = (
            (price - stop)
            / price
        ) * 100

        return {
            "symbol": symbol,
            "score": score,
            "volume": volume,
            "acceleration": acceleration,
            "momentum": momentum,
            "breakout": breakout,
            "price": price,
            "stop": stop,
            "tp1": tp1,
            "tp2": tp2,
            "risk": risk_percent
        }

    except Exception:

        return None


# ============================================================
# SCAN
# ============================================================

def scan():

    start = time.time()

    markets = get_eur_markets()

    print(
        f"Marchés disponibles : "
        f"{len(markets)}"
    )

    candidates = get_candidates(
        markets
    )

    print(
        f"Pré-sélection : "
        f"{len(candidates)} candidats "
        f"sur {len(markets)} marchés"
    )

    if not candidates:

        return []

    print(
        "Analyse approfondie..."
    )

    opportunities = []

    completed = 0

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                analyse_market,
                candidate
            )
            for candidate in candidates
        ]

        for future in as_completed(
            futures
        ):

            completed += 1

            try:

                result = future.result()

                if result is not None:
                    opportunities.append(
                        result
                    )

            except Exception:

                pass

            print(
                f"\rAnalyse : "
                f"{completed}/"
                f"{len(candidates)}",
                end="",
                flush=True
            )

    print()

    opportunities.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    elapsed = (
        time.time() - start
    )

    print(
        f"Scan terminé en "
        f"{elapsed:.2f} secondes"
    )

    return opportunities[:MAX_RESULTS]


# ============================================================
# AFFICHAGE
# ============================================================

def display(opportunities):

    print()

    print(
        "=" * 80
    )

    print(
        "SIMON RADAR — OPPORTUNITÉS"
    )

    print(
        "=" * 80
    )

    print(
        datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )

    print()

    if not opportunities:

        print(
            "Aucune opportunité actuellement."
        )

        return

    for i, x in enumerate(
        opportunities,
        1
    ):

        if x["score"] >= 90:
            label = "🔥 ALERTE FORTE"

        elif x["score"] >= 85:
            label = "🟢 OPPORTUNITÉ FORTE"

        else:
            label = "🟡 SURVEILLANCE"

        print(
            f"{i}. {x['symbol']} — "
            f"SCORE {x['score']}/100 "
            f"{label}"
        )

        print(
            f"   Volume        : "
            f"x{x['volume']:.2f}"
        )

        print(
            f"   Accélération  : "
            f"x{x['acceleration']:.2f}"
        )

        print(
            f"   Momentum 24h  : "
            f"{x['momentum']:+.2f}%"
        )

        print(
            f"   Breakout      : "
            f"{x['breakout']:+.2f}%"
        )

        print(
            f"   Entrée        : "
            f"{x['price']:.8f}"
        )

        print(
            f"   Stop-loss     : "
            f"{x['stop']:.8f}"
        )

        print(
            f"   TP1           : "
            f"{x['tp1']:.8f}"
        )

        print(
            f"   TP2           : "
            f"{x['tp2']:.8f}"
        )

        print(
            f"   Risque        : "
            f"{x['risk']:.2f}%"
        )

        print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "# SIMON RADAR — SCAN UNIQUE"
    )

    print()

    try:

        opportunities = scan()

        display(
            opportunities
        )

    except KeyboardInterrupt:

        print(
            "\nRadar arrêté."
        )

    except Exception as e:

        print(
            f"\nErreur radar : {e}"
        )

    print()

    print(
        "=" * 80
    )

    print(
        "SCAN TERMINÉ"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":

    main()