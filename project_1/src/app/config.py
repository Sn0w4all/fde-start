def get_config(tickers):
    return {
        "tickers": tickers,
        "endpoints": {
            "struct": "https://iss.moex.com/iss/securities/{ticker}.json?iss.meta=off",
            "marketdata": "https://iss.moex.com/iss/engines/currency/markets/selt/securities/{ticker}.json?iss.meta=off&iss.only=marketdata"    
        }
    }