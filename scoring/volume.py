import statistics


def calculate_volume_ratio(candles, periods=20):

    if len(candles) < periods + 1:
        return None

    historical_volumes = [
        candle[5]
        for candle in candles[-(periods + 1):-1]
        if candle[5] > 0
    ]

    current_volume = candles[-1][5]

    # Aucun volume actuellement
    if current_volume <= 0:
        return None

    # Pas assez de données réellement actives
    if len(historical_volumes) < 5:
        return None

    median_volume = statistics.median(
        historical_volumes
    )

    if median_volume <= 0:
        return None

    return current_volume / median_volume