def calculate_price_change(candles, periods=24):

    if len(candles) < periods + 1:
        return None

    current_price = candles[-1][4]

    previous_price = candles[-(periods + 1)][4]

    if previous_price <= 0:
        return None

    return (
        (current_price / previous_price) - 1
    ) * 100