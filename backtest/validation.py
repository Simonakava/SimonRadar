from backtest.all_markets import run_all_markets


MIN_TRADES = 15
MIN_TRADES_FOR_SELECTION = 50  # seuil minimum pour être candidat au "meilleur score"


def analyse(trades, minimum_score):

    selected = [
        t for t in trades
        if t["score"] >= minimum_score
    ]

    if len(selected) < MIN_TRADES:
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

    positive = [
        r for r in returns
        if r > 0
    ]

    negative = [
        abs(r)
        for r in returns
        if r < 0
    ]

    total = sum(returns)

    average = total / len(returns)

    profit_factor = (
        sum(positive) / sum(negative)
        if negative
        else 999
    )

    return {
        "trades": len(selected),
        "win_rate": len(wins) / len(selected) * 100,
        "tp1_rate": len(tp1) / len(selected) * 100,
        "average": average,
        "profit_factor": profit_factor,
        "total": total
    }


def main():

    print()
    print("=" * 70)
    print("SIMON RADAR — VALIDATION HORS ÉCHANTILLON")
    print("=" * 70)
    print()

    trades = run_all_markets()

    if not trades:
        print("Aucun trade.")
        return

    trades.sort(
        key=lambda x: x["entry_timestamp"]
    )

    split = int(len(trades) * 0.70)

    training = trades[:split]
    validation = trades[split:]

    print()
    print("=" * 70)
    print("DATASET")
    print("=" * 70)
    print()

    print(
        f"Entraînement : {len(training)} trades"
    )

    print(
        f"Validation   : {len(validation)} trades"
    )

    print()

    print("=" * 70)
    print("ENTRAÎNEMENT")
    print("=" * 70)
    print()

    training_results = []

    for score in range(50, 101):

        result = analyse(
            training,
            score
        )

        if result is None:
            continue

        training_results.append(
            (score, result)
        )

    training_results.sort(
        key=lambda x: (
            x[1]["average"],
            x[1]["profit_factor"]
        ),
        reverse=True
    )

    print(
        "TOP SEUILS TROUVÉS SUR L'ENTRAÎNEMENT"
    )
    print()

    for score, result in training_results[:10]:

        print(
            f"SCORE >= {score} | "
            f"{result['trades']} trades | "
            f"Win {result['win_rate']:.1f}% | "
            f"TP1 {result['tp1_rate']:.1f}% | "
            f"Avg {result['average']:+.3f}% | "
            f"PF {result['profit_factor']:.2f}"
        )

    print()

    print("=" * 70)
    print("VALIDATION — DONNÉES JAMAIS UTILISÉES POUR CHOISIR LE SEUIL")
    print("=" * 70)
    print()

    for score in [70, 75, 80, 85, 87, 90, 92, 95, 98]:

        result = analyse(
            validation,
            score
        )

        if result is None:
            print(
                f"SCORE >= {score} : "
                f"pas assez de trades"
            )
            continue

        print(
            f"SCORE >= {score} | "
            f"{result['trades']} trades | "
            f"Win {result['win_rate']:.1f}% | "
            f"TP1 {result['tp1_rate']:.1f}% | "
            f"Avg {result['average']:+.3f}% | "
            f"PF {result['profit_factor']:.2f} | "
            f"Total {result['total']:+.2f}%"
        )

    print()

    # ---------------------------------------------------------
    # SÉLECTION DU MEILLEUR SEUIL — avec garde-fou anti-surapprentissage
    # On ne retient comme candidat que les seuils ayant un
    # échantillon suffisant (MIN_TRADES_FOR_SELECTION), pour
    # éviter qu'un seuil basé sur 16 trades ne soit choisi
    # "meilleur" simplement par chance statistique.
    # ---------------------------------------------------------

    reliable_candidates = [
        (score, result)
        for score, result in training_results
        if result["trades"] >= MIN_TRADES_FOR_SELECTION
    ]

    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    print()

    if not reliable_candidates:

        print(
            f"Aucun seuil n'atteint {MIN_TRADES_FOR_SELECTION} "
            f"trades sur l'entraînement — échantillon trop "
            f"faible pour choisir un seuil fiable."
        )

        return

    best_score, _ = reliable_candidates[0]

    result = analyse(
        validation,
        best_score
    )

    print(
        f"Seuil choisi sur entraînement : "
        f"{best_score} "
        f"(retenu parmi les seuils avec >= "
        f"{MIN_TRADES_FOR_SELECTION} trades)"
    )

    if result is None:

        print(
            "Pas assez de trades en validation."
        )

        return

    print(
        f"Validation : {result['trades']} trades"
    )

    print(
        f"Win rate   : {result['win_rate']:.2f}%"
    )

    print(
        f"TP1 rate   : {result['tp1_rate']:.2f}%"
    )

    print(
        f"Gain moyen : {result['average']:+.3f}%"
    )

    print(
        f"Profit factor : "
        f"{result['profit_factor']:.2f}"
    )

    print(
        f"Performance : "
        f"{result['total']:+.2f}%"
    )

    print()

    if (
        result["average"] > 0
        and result["profit_factor"] > 1
    ):

        print(
            "✅ SIGNAL ENCOURAGEANT"
        )

        print(
            "Le seuil reste positif sur des données "
            "non utilisées pour l'optimisation."
        )

    else:

        print(
            "❌ SIGNAL NON VALIDÉ"
        )

        print(
            "Il faut modifier la stratégie."
        )


if __name__ == "__main__":
    main()