import time
from data.kraken import get_exchange


_CACHE = {}

CACHE_SECONDS = 300


def get_ohlcv(
    symbol,
    timeframe="1h",
    limit=100
):

    key = (
        symbol,
        timeframe,
        limit
    )

    now = time.time()

    if key in _CACHE:

        timestamp, candles = _CACHE[key]

        if now - timestamp < CACHE_SECONDS:

            return candles

    exchange = get_exchange()

    candles = exchange.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=limit
    )

    _CACHE[key] = (
        now,
        candles
    )

    return candles