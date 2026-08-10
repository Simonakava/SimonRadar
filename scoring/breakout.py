def calculate_breakout(candles, periods=20):

    if len(candles) < periods + 1:
        return None

    current_price = candles[-1][4]

    previous_highs = [
        candle[2]
        for candle in candles[-(periods + 1):-1]
    ]

    if not previous_highs:
        return None

    highest_price = max(previous_highs)

    if highest_price <= 0:
        return None

    return (
        (current_price / highest_price) - 1
    ) * 100