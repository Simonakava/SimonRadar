from scoring.volume import calculate_volume_ratio
from scoring.acceleration import calculate_volume_acceleration
from scoring.breakout import calculate_breakout
from scoring.momentum import calculate_price_change
from scoring.score import calculate_score
from scoring.risk import calculate_atr


def calculate_historical_signal(candles, index):

    if index < 50:
        return None

    history = candles[:index + 1]

    volume_ratio = calculate_volume_ratio(history)
    momentum = calculate_price_change(history, periods=24)
    acceleration = calculate_volume_acceleration(history)
    breakout = calculate_breakout(history, periods=20)
    atr = calculate_atr(history)

    values = [
        volume_ratio,
        momentum,
        acceleration,
        breakout,
        atr
    ]

    if any(v is None for v in values):
        return None

    if volume_ratio <= 0:
        return None

    if acceleration <= 0:
        return None

    if momentum <= 0:
        return None

    if breakout <= 0:
        return None

    score = calculate_score(
        volume_ratio,
        momentum,
        acceleration,
        breakout
    )

    return {
        "score": score,
        "volume_ratio": volume_ratio,
        "momentum": momentum,
        "acceleration": acceleration,
        "breakout": breakout,
        "atr": atr
    }