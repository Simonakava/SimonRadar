import itertools
import statistics

from backtest.all_markets import run_all_markets


def analyse(trades, minimum_score):

    selected = [
        t for t in trades
        if t["score"] >= minimum_score
    ]

    if len(selected) < 20:
        return None

    returns = [
        t["return_percent"]
        for t in selected
    ]

    wins = [
        t for t in selected
        if t["result"] == "TP2"
    ]

    tp1 = [
        t for t in selected
        if t["tp1_hit"]
    ]

    total = sum(returns)

    average = total / len(selected)

    win_rate = (
        len(wins) /
        len(selected)
    ) * 100

    tp1_rate = (
        len(tp1) /
        len(selected)
    ) * 100

    positive = [
        r for r in returns
        if r > 0
    ]

    negative = [
        abs(r)
        for r in returns
        if r < 0
    ]

    gross_profit = sum(positive)
    gross_loss = sum(negative)

    if gross_loss > 0:
        profit_factor = (
            gross_profit /
            gross_loss
        )
    else:
        profit_factor = 999

    median = statistics.median(
        returns
    )

    return {
        "score": minimum_score,
        "trades": len(selected),
        "win_rate": win_rate,
        "tp1_rate": tp1_rate,
        "average": average,
        "median": median,
        "total": total,
        "profit_factor": profit_factor
    }


def main():

    print()
    print("=" * 70)
    print("SIMON RADAR — OPTIMISEUR")
    print("=" * 70)
    print()

    trades = run_all_markets()

    print()
    print(
        f"Trades disponibles : {len(trades)}"
    )
    print()

    results = []

    for score in range(50, 101):

        result = analyse(
            trades,
            score
        )

        if result is not None:
            results.append(result)

    results.sort(
        key=lambda x: (
            x["average"],
            x["profit_factor"],
            x["trades"]
        ),
        reverse=True
    )

    print()
    print("=" * 70)
    print("TOP SEUILS DE SCORE")
    print("=" * 70)
    print()

    for i, result in enumerate(
        results[:10],
        start=1
    ):

        print(
            f"{i}. SCORE >= "
            f"{result['score']}"
        )

        print(
            f"   Trades        : "
            f"{result['trades']}"
        )

        print(
            f"   Win rate      : "
            f"{result['win_rate']:.2f}%"
        )

        print(
            f"   TP1 rate      : "
            f"{result['tp1_rate']:.2f}%"
        )

        print(
            f"   Gain moyen    : "
            f"{result['average']:+.3f}%"
        )

        print(
            f"   Médiane       : "
            f"{result['median']:+.3f}%"
        )

        print(
            f"   Profit factor : "
            f"{result['profit_factor']:.2f}"
        )

        print(
            f"   Performance    : "
            f"{result['total']:+.2f}%"
        )

        print()


    print("=" * 70)
    print("SEUILS COMPARÉS")
    print("=" * 70)
    print()

    for score in [
        50,
        60,
        70,
        80,
        85,
        90,
        92,
        94,
        95
    ]:

        result = analyse(
            trades,
            score
        )

        if result is None:
            continue

        print(
            f">= {score} | "
            f"{result['trades']} trades | "
            f"Win {result['win_rate']:.1f}% | "
            f"TP1 {result['tp1_rate']:.1f}% | "
            f"Avg {result['average']:+.3f}% | "
            f"PF {result['profit_factor']:.2f}"
        )


if __name__ == "__main__":
    main()