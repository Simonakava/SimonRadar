def simulate_trade(
    candles,
    entry_index,
    atr,
    max_holding_periods=24
):

    entry = candles[entry_index][4]

    if entry <= 0 or atr is None or atr <= 0:
        return None

    stop_distance = atr * 0.8

    stop = entry - stop_distance

    tp1 = entry + stop_distance * 1.33

    tp2 = entry + stop_distance * 2.33

    tp1_hit = False
    tp2_hit = False

    for i in range(
        entry_index + 1,
        min(
            entry_index + 1 + max_holding_periods,
            len(candles)
        )
    ):

        high = candles[i][2]
        low = candles[i][3]

        if not tp1_hit and high >= tp1:
            tp1_hit = True

        if high >= tp2:

            return {
                "result": "TP2",
                "return_percent": 2.33,
                "tp1_hit": True
            }

        if low <= stop:

            if tp1_hit:

                return {
                    "result": "TP1_STOP",
                    "return_percent": 0.5 * 1.33 - 0.5 * 0.8,
                    "tp1_hit": True
                }

            return {
                "result": "LOSS",
                "return_percent": -0.8,
                "tp1_hit": False
            }

    if tp1_hit:

        return {
            "result": "TP1_TIMEOUT",
            "return_percent": 0.5 * 1.33,
            "tp1_hit": True
        }

    return {
        "result": "TIMEOUT",
        "return_percent": 0,
        "tp1_hit": False
    }