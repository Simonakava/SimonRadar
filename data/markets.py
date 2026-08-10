from data.kraken import get_exchange


def get_eur_markets():

    exchange = get_exchange()

    markets = exchange.load_markets()

    symbols = []

    for symbol, market in markets.items():

        if (
            market.get("spot")
            and market.get("quote") == "EUR"
            and market.get("active", True)
        ):
            symbols.append(symbol)

    return symbols