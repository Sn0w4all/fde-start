def get_config(interests):
    if isinstance(interests, dict):
        interests = [interests]

    configs = []
    for item in interests:
        configs.append({
            "tickers": [item["ticker"]],
            "endpoints": {
                "struct": f"https://iss.moex.com/iss/securities/{item["ticker"]}.json?iss.meta=off",
                "marketdata": f"https://iss.moex.com/iss/engines/{item["engine"]}/markets/{item["market"]}/securities/{item["ticker"]}.json?iss.meta=off&iss.only=marketdata"
            }
        })
    return configs
