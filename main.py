from datetime import datetime

from scanner.scanner import scan_market
from database.db import (
    save_scan_results,
    open_paper_trades,
    update_paper_trades,
    get_open_paper_trades_with_current_price,
    get_paper_trading_stats
)


MAX_RESULTS = 15

TREND_LABELS = {
    "hausse": "📈 hausse",
    "baisse": "📉 baisse",
    "stagne": "➖ stagne",
    "inconnu": "❓ inconnu"
}


def print_signal(result, position):

    plan = result["trade_plan"]
    classification = result["classification"]

    labels = {
        "ENTRY": "🚀 ENTRÉE",
        "STRONG": "🔥 FORT",
        "WATCH": "🟡 WATCH",
        "WEAK": "⚪ FAIBLE"
    }

    label = labels.get(classification, "")

    print(
        f"{position}. "
        f"{result['symbol']} — "
        f"SCORE {result['score']}/100 — "
        f"QUALITÉ {result['quality']}/100 "
        f"{label}"
    )

    print(f"   Score global  : {result['combined_score']:.1f}/100")
    print(f"   Volume        : x{result['volume_ratio']:.2f}")
    print(f"   Accélération  : x{result['acceleration']:.2f}")
    print(f"   Momentum 24h  : {result['momentum']:+.2f}%")
    print(f"   Breakout      : {result['breakout']:+.2f}%")
    print(f"   Entrée        : {plan['entry']:.8f}")
    print(f"   Stop-loss     : {plan['stop_loss']:.8f}")
    print(f"   TP1           : {plan['take_profit_1']:.8f}")
    print(f"   TP2           : {plan['take_profit_2']:.8f}")
    print(f"   Risque        : {plan['risk_percent']:.2f}%")
    print(f"   R/R TP1       : {plan['rr_1']:.2f}")
    print(f"   R/R TP2       : {plan['rr_2']:.2f}")
    print(f"   Capital suggéré : {plan['position_size']:.2f} €")
    print(f"   Risque réel     : {plan['actual_risk_money']:.2f} €")
    print()


def print_open_positions():

    positions = get_open_paper_trades_with_current_price()

    print("=" * 70)
    print("📡 POSITIONS FICTIVES EN COURS (max 24h)")
    print("=" * 70)
    print()

    if not positions:
        print("Aucune position fictive en cours.")
        print()
        return

    for p in positions:

        trend_label = TREND_LABELS.get(p["trend"], p["trend"])

        print(
            f"{p['symbol']} — {p['classification']} "
            f"(score {p['score']}) — {trend_label}"
        )

        print(f"   Entrée        : {p['entry_price']:.8f}")

        if p["current_price"] is not None:
            print(f"   Prix actuel   : {p['current_price']:.8f}")
            print(f"   Évolution     : {p['change_percent']:+.2f}%")
        else:
            print("   Prix actuel   : indisponible")

        print(f"   Stop-loss     : {p['stop_loss']:.8f}")
        print(f"   TP1           : {p['take_profit_1']:.8f}")
        print(f"   TP2           : {p['take_profit_2']:.8f}")
        print(f"   Temps écoulé  : {p['elapsed_hours']:.1f}h / 24h")
        print()


def print_paper_trading_stats():

    stats = get_paper_trading_stats()

    print("=" * 70)
    print("📊 PAPER TRADING — PERFORMANCE SUR SIGNAUX CLÔTURÉS (24H MAX)")
    print("=" * 70)
    print()

    if stats is None:
        print("Aucune position fictive clôturée pour l'instant.")
        print()
        return

    print(f"Positions clôturées : {stats['trades']}")
    print(f"Win rate            : {stats['win_rate']:.2f}%")
    print(f"Gain moyen/trade    : {stats['average']:+.3f}%")
    print(f"Profit factor       : {stats['profit_factor']:.2f}")
    print(f"Performance cumulée : {stats['total']:+.2f}%")
    print()


def main():

    start = datetime.now()

    results = scan_market()

    save_scan_results(results)

    update_paper_trades()
    open_paper_trades(results)

    entries = [r for r in results if r["classification"] == "ENTRY"]
    strong = [r for r in results if r["classification"] == "STRONG"]
    watch = [r for r in results if r["classification"] == "WATCH"]

    print("=" * 70)
    print("🚀 ENTRÉES POTENTIELLES")
    print("=" * 70)
    print()

    if entries:
        for i, result in enumerate(entries[:MAX_RESULTS], start=1):
            print_signal(result, i)
    else:
        print("Aucune entrée exceptionnelle.")
        print()

    print("=" * 70)
    print("🔥 SIGNAUX FORTS")
    print("=" * 70)
    print()

    if strong:
        for i, result in enumerate(strong[:MAX_RESULTS], start=1):
            print_signal(result, i)
    else:
        print("Aucun signal fort.")
        print()

    print("=" * 70)
    print("🟡 SURVEILLANCE")
    print("=" * 70)
    print()

    if watch:
        for i, result in enumerate(watch[:MAX_RESULTS], start=1):
            print_signal(result, i)
    else:
        print("Aucune configuration à surveiller.")
        print()

    print("=" * 70)
    print("🏆 TOP POTENTIELS DU SCAN")
    print("=" * 70)
    print()

    for i, result in enumerate(results[:10], start=1):
        print(
            f"{i}. {result['symbol']} — "
            f"Global {result['combined_score']:.1f} "
            f"| Score {result['score']} "
            f"| Qualité {result['quality']} "
            f"| {result['classification']}"
        )

    print()

    print_open_positions()
    print_paper_trading_stats()

    elapsed = (datetime.now() - start).total_seconds()

    print("=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print()
    print(f"Marchés analysés : {len(results)}")
    print(f"Entrées potentielles : {len(entries)}")
    print(f"Signaux forts : {len(strong)}")
    print(f"Surveillance : {len(watch)}")
    print(f"Temps total : {elapsed:.2f} secondes")
    print()
    print("=" * 70)
    print("SCAN TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    main()