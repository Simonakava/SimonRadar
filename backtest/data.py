from data.kraken import get_exchange


def get_historical_ohlcv(
    symbol,
    timeframe="1h",
    limit=720
):

    exchange = get_exchange()

    try:

        candles = exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            limit=limit
        )

        return candles

    except Exception as e:

        print(
            f"Erreur {symbol}: {e}"
        )

        return []