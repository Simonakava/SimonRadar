def calculate_atr(candles, period=14):
    """
    Average True Range — valeur absolue (même unité que le prix).
    Utilisée par le backtest pour placer stop/TP de façon cohérente
    avec calculate_trade_plan.
    """
    if candles is None or len(candles) < 10:
        return None

    try:
        ranges = []
        start = max(1, len(candles) - period)

        for i in range(start, len(candles)):
            high = float(candles[i][2])
            low = float(candles[i][3])
            previous_close = float(candles[i - 1][4])

            tr = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close)
            )

            if tr > 0:
                ranges.append(tr)

        if not ranges:
            return None

        return sum(ranges) / len(ranges)

    except Exception:
        return None


def calculate_trade_plan(
    candles,
    capital=200.0,
    risk_target=1.0
):
    """
    Plan de trade standardisé.
    Le risque monétaire cible est basé sur le capital.
    """
    if candles is None or len(candles) < 10:
        return None
    try:
        closes = [
            float(c[4])
            for c in candles
            if c[4] is not None
        ]
        highs = [
            float(c[2])
            for c in candles
            if c[2] is not None
        ]
        lows = [
            float(c[3])
            for c in candles
            if c[3] is not None
        ]
        if len(closes) < 10:
            return None
        entry = closes[-1]
        if entry <= 0:
            return None
        # =================================================
        # VOLATILITÉ
        # =================================================
        ranges = []
        start = max(1, len(candles) - 14)
        for i in range(start, len(candles)):
            high = float(candles[i][2])
            low = float(candles[i][3])
            previous_close = float(candles[i - 1][4])
            tr = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close)
            )
            if tr > 0:
                ranges.append(tr)
        if not ranges:
            return None
        atr = sum(ranges) / len(ranges)
        atr_percent = (
            atr / entry
        ) * 100
        # =================================================
        # STOP ADAPTATIF
        # =================================================
        stop_percent = max(
            1.0,
            min(
                5.0,
                atr_percent * 1.25
            )
        )
        stop_loss = entry * (
            1 - stop_percent / 100
        )
        risk_percent = (
            (entry - stop_loss)
            / entry
        ) * 100
        # =================================================
        # TAKE PROFITS
        # =================================================
        reward_1 = risk_percent * 1.33
        reward_2 = risk_percent * 2.33
        take_profit_1 = entry * (
            1 + reward_1 / 100
        )
        take_profit_2 = entry * (
            1 + reward_2 / 100
        )
        # =================================================
        # TAILLE DE POSITION
        # =================================================
        max_risk_money = (
            capital
            * risk_target
            / 100
        )
        risk_per_unit = (
            entry - stop_loss
        )
        if risk_per_unit <= 0:
            return None
        position_size = (
            max_risk_money
            / risk_per_unit
        )
        position_value = (
            position_size * entry
        )
        # On ne dépasse jamais le capital disponible.
        position_value = min(
            position_value,
            capital
        )
        actual_risk_money = (
            position_value
            * risk_percent
            / 100
        )
        return {
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "risk_percent": risk_percent,
            "rr_1": 1.33,
            "rr_2": 2.33,
            "position_size": position_value,
            "actual_risk_money": actual_risk_money,
        }
    except Exception:
        return None