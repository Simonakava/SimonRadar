from concurrent.futures import ThreadPoolExecutor, as_completed

from data.markets import get_eur_markets
from backtest.data import get_historical_ohlcv
from backtest.scanner import calculate_historical_signal
from backtest.engine import simulate_trade


MAX_WORKERS = 8
TIMEFRAME = "1h"
LIMIT = 720


def backtest_market(symbol):

    candles = get_historical_ohlcv(
        symbol,
        timeframe=TIMEFRAME,
        limit=LIMIT
    )

    if len(candles) < 100:
        return symbol, []

    trades = []
    last_trade_index = -6

    for index in range(50, len(candles) - 24):

        if index - last_trade_index < 6:
            continue

        signal = calculate_historical_signal(
            candles,
            index
        )

        if signal is None:
            continue

        if signal["score"] < 50:
            continue

        trade = simulate_trade(
            candles,
            index,
            signal["atr"],
            max_holding_periods=24
        )

        if trade is None:
            continue

        trade["symbol"] = symbol
        trade["score"] = signal["score"]
        trade["volume_ratio"] = signal["volume_ratio"]
        trade["acceleration"] = signal["acceleration"]
        trade["momentum"] = signal["momentum"]
        trade["breakout"] = signal["breakout"]
        trade["entry_timestamp"] = candles[index][0]
        trade["entry_price"] = candles[index][4]

        trades.append(trade)

        last_trade_index = index

    return symbol, trades


def run_all_markets():

    markets = get_eur_markets()

    print()
    print("=" * 70)
    print("SIMON RADAR — BACKTEST GLOBAL")
    print("=" * 70)
    print()
    print(f"Marchés : {len(markets)}")
    print(f"Workers : {MAX_WORKERS}")
    print()

    all_trades = []
    completed = 0

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                backtest_market,
                symbol
            ): symbol
            for symbol in markets
        }

        for future in as_completed(futures):

            symbol = futures[future]

            try:
                symbol, trades = future.result()
                all_trades.extend(trades)

            except Exception as e:
                print(f"\nErreur {symbol}: {e}")

            completed += 1

            print(
                f"\rProgression : "
                f"{completed}/{len(markets)} "
                f"({completed / len(markets) * 100:.1f}%)",
                end="",
                flush=True
            )

    print()
    print()

    return all_trades


def analyse_results(trades):

    print()
    print("=" * 70)
    print("ANALYSE GLOBALE")
    print("=" * 70)
    print()

    if not trades:
        print("Aucun trade trouvé.")
        return

    print(f"Trades totaux : {len(trades)}")
    print()

    ranges = [
        (50, 59),
        (60, 69),
        (70, 79),
        (80, 89),
        (90, 100)
    ]

    for minimum, maximum in ranges:

        selected = [
            trade
            for trade in trades
            if minimum <= trade["score"] <= maximum
        ]

        print(f"## SCORE {minimum}-{maximum}")
        print()

        if not selected:
            print("Aucun trade")
            print()
            continue

        wins = [
            trade
            for trade in selected
            if trade["result"] == "TP2"
        ]

        losses = [
            trade
            for trade in selected
            if trade["result"] == "LOSS"
        ]

        tp1_hits = [
            trade
            for trade in selected
            if trade["tp1_hit"]
        ]

        total_return = sum(
            trade["return_percent"]
            for trade in selected
        )

        average_return = total_return / len(selected)

        win_rate = (
            len(wins) / len(selected)
        ) * 100

        tp1_rate = (
            len(tp1_hits) / len(selected)
        ) * 100

        positive = [
            trade["return_percent"]
            for trade in selected
            if trade["return_percent"] > 0
        ]

        negative = [
            abs(trade["return_percent"])
            for trade in selected
            if trade["return_percent"] < 0
        ]

        profit_factor = (
            sum(positive) / sum(negative)
            if negative
            else 999
        )

        print(f"Trades       : {len(selected)}")
        print(f"TP2          : {len(wins)}")
        print(f"Stops        : {len(losses)}")
        print(f"TP1          : {len(tp1_hits)}")
        print(f"Win rate     : {win_rate:.2f}%")
        print(f"TP1 rate     : {tp1_rate:.2f}%")
        print(f"Gain moyen   : {average_return:+.3f}%")
        print(f"Profit factor: {profit_factor:.2f}")
        print(f"Performance  : {total_return:+.2f}%")
        print()


if __name__ == "__main__":

    trades = run_all_markets()

    analyse_results(trades)