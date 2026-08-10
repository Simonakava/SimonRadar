from backtest.data import get_historical_ohlcv
from backtest.scanner import calculate_historical_signal
from backtest.engine import simulate_trade


def run_backtest(
    symbol,
    limit=720,
    minimum_score=70
):

    print()
    print("=" * 70)
    print(f"BACKTEST — {symbol}")
    print("=" * 70)
    print()

    candles = get_historical_ohlcv(
        symbol,
        timeframe="1h",
        limit=limit
    )

    print(
        f"Historique chargé : "
        f"{len(candles)} bougies"
    )

    trades = []

    start_index = 30

    cooldown_periods = 6

    last_trade_index = -cooldown_periods

    for index in range(
        start_index,
        len(candles) - 24
    ):

        if index - last_trade_index < cooldown_periods:
            continue

        signal = calculate_historical_signal(
            candles,
            index
        )

        if signal is None:
            continue

        if signal["score"] < minimum_score:
            continue

        trade = simulate_trade(
            candles,
            index,
            signal["atr"],
            max_holding_periods=24
        )

        trade["score"] = signal["score"]
        trade["volume_ratio"] = signal["volume_ratio"]
        trade["acceleration"] = signal["acceleration"]
        trade["momentum"] = signal["momentum"]
        trade["breakout"] = signal["breakout"]

        trades.append(trade)

        last_trade_index = index

    print()
    print(
        f"Signaux détectés : {len(trades)}"
    )

    if not trades:

        print()
        print("Aucun signal suffisamment fort.")

        return

    wins = [
        t for t in trades
        if t["result"] == "TP2"
    ]

    losses = [
        t for t in trades
        if t["result"] == "LOSS"
    ]

    timeouts = [
        t for t in trades
        if t["result"] == "TIMEOUT"
    ]

    tp1_hits = [
        t for t in trades
        if t["tp1_hit"]
    ]

    total_return = sum(
        t["return_percent"]
        for t in trades
    )

    win_rate = (
        len(wins) /
        len(trades)
    ) * 100

    tp1_rate = (
        len(tp1_hits) /
        len(trades)
    ) * 100

    average_return = (
        total_return /
        len(trades)
    )

    print()
    print("=" * 70)
    print("RÉSULTATS")
    print("=" * 70)

    print(
        f"Trades             : {len(trades)}"
    )

    print(
        f"TP2 atteints       : {len(wins)}"
    )

    print(
        f"Stops touchés      : {len(losses)}"
    )

    print(
        f"Timeouts           : {len(timeouts)}"
    )

    print(
        f"TP1 atteints       : {len(tp1_hits)}"
    )

    print(
        f"Taux TP2           : {win_rate:.2f}%"
    )

    print(
        f"Taux TP1           : {tp1_rate:.2f}%"
    )

    print(
        f"Gain moyen/trade   : "
        f"{average_return:+.2f}%"
    )

    print(
        f"Performance brute  : "
        f"{total_return:+.2f}%"
    )

    print()
    print("=" * 70)


if __name__ == "__main__":

    run_backtest(
        "XPL/EUR",
        limit=720,
        minimum_score=70
    )