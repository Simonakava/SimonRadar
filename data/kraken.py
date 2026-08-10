import ccxt


_exchange = None


def get_exchange():

    global _exchange

    if _exchange is None:

        _exchange = ccxt.kraken({
            "enableRateLimit": True,
            "timeout": 10000,
        })

        _exchange.load_markets()

    return _exchange


def get_all_tickers():

    exchange = get_exchange()

    return exchange.fetch_tickers()