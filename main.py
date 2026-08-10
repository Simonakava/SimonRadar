from datetime import datetime

from scanner.scanner import scan_market
from database.db import save_scan_results


MAX_RESULTS = 15


def print_signal(
    result,
    position
):

    plan = result["trade_plan"]

    classification = result["classification"]

    labels = {
        "ENTRY": "🚀 ENTRÉE",
        "STRONG": "🔥 FORT",
        "WATCH": "🟡 WATCH",
        "WEAK": "⚪ FAIBLE"
    }

    label = labels.get(
        classification,
        ""
    )

    print(
        f"{position}. "
        f"{result['symbol']} — "
        f"SCORE {result['score']}/100 — "
        f"QUALITÉ {result['quality']}/100 "
        f"{label}"
    )

    print(
        f"   Score global  : "
        f"{result['combined_score']:.1f}/100"
    )

    print(
        f"   Volume        : "
        f"x{result['volume_ratio']:.2f}"
    )

    print(
        f"   Accélération  : "
        f"x{result['acceleration']:.2f}"
    )

    print(
        f"   Momentum 24h  : "
        f"{result['momentum']:+.2f}%"
    )

    print(
        f"   Breakout      : "
        f"{result['breakout']:+.2f}%"
    )

    print(
        f"   Entrée        : "
        f"{plan['entry']:.8f}"
    )

    print(
        f"   Stop-loss     : "
        f"{plan['stop_loss']:.8f}"
    )

    print(
        f"   TP1           : "
        f"{plan['take_profit_1']:.8f}"
    )

    print(
        f"   TP2           : "
        f"{plan['take_profit_2']:.8f}"
    )

    print(
        f"   Risque        : "
        f"{plan['risk_percent']:.2f}%"
    )

    print(
        f"   R/R TP1       : "
        f"{plan['rr_1']:.2f}"
    )

    print(
        f"   R/R TP2       : "
        f"{plan['rr_2']:.2f}"
    )

    print(
        f"   Capital suggéré : "
        f"{plan['position_size']:.2f} €"
    )

    print(
        f"   Risque réel     : "
        f"{plan['actual_risk_money']:.2f} €"
    )

    print()


def main():

    start = datetime.now()

    results = scan_market()

    # =====================================================
    # SAUVEGARDE EN BASE — pour re-validation future du seuil
    # =====================================================

    save_scan_results(results)

    # =====================================================
    # CATÉGORIES
    # =====================================================

    entries = [
        r for r in results
        if r["classification"] == "ENTRY"
    ]

    strong = [
        r for r in results
        if r["classification"] == "STRONG"
    ]

    watch = [
        r for r in results
        if r["classification"] == "WATCH"
    ]

    # =====================================================
    # ENTRÉES
    # =====================================================

    print("=" * 70)
    print("🚀 ENTRÉES POTENTIELLES")
    print("=" * 70)
    print()

    if entries:

        for i, result in enumerate(
            entries[:MAX_RESULTS],
            start=1
        ):
            print_signal(
                result,
                i
            )

    else:

        print(
            "Aucune entrée exceptionnelle."
        )
        print()

    # =====================================================
    # FORTS
    # =====================================================

    print("=" * 70)
    print("🔥 SIGNAUX FORTS")
    print("=" * 70)
    print()

    if strong:

        for i, result in enumerate(
            strong[:MAX_RESULTS],
            start=1
        ):
            print_signal(
                result,
                i
            )

    else:

        print(
            "Aucun signal fort."
        )
        print()

    # =====================================================
    # WATCH
    # =====================================================

    print("=" * 70)
    print("🟡 SURVEILLANCE")
    print("=" * 70)
    print()

    if watch:

        for i, result in enumerate(
            watch[:MAX_RESULTS],
            start=1
        ):
            print_signal(
                result,
                i
            )

    else:

        print(
            "Aucune configuration à surveiller."
        )
        print()

    # =====================================================
    # TOP GLOBAL
    # =====================================================

    print("=" * 70)
    print("🏆 TOP POTENTIELS DU SCAN")
    print("=" * 70)
    print()

    for i, result in enumerate(
        results[:10],
        start=1
    ):

        print(
            f"{i}. "
            f"{result['symbol']} — "
            f"Global {result['combined_score']:.1f} "
            f"| Score {result['score']} "
            f"| Qualité {result['quality']} "
            f"| "
            f"{result['classification']}"
        )

    print()

    # =====================================================
    # RÉSUMÉ
    # =====================================================

    elapsed = (
        datetime.now() - start
    ).total_seconds()

    print("=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print()

    print(
        f"Marchés analysés : "
        f"{len(results)}"
    )

    print(
        f"Entrées potentielles : "
        f"{len(entries)}"
    )

    print(
        f"Signaux forts : "
        f"{len(strong)}"
    )

    print(
        f"Surveillance : "
        f"{len(watch)}"
    )

    print(
        f"Temps total : "
        f"{elapsed:.2f} secondes"
    )

    print()

    print("=" * 70)
    print("SCAN TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    main()