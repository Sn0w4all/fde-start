from enum import Enum
class saved_type(str, Enum):
    RAW = "raw"
    NORMALIZE = "normalized"
    TEXT_REPORT = "report"
    HTML = "html_report"

class saved_format(str, Enum):
    JSON = ".json"
    HTML = ".html"


def get_config(interests):
    try:
        if isinstance(interests, dict):
            interests = [interests]

        configs = []
        for item in interests:
            configs.append({
                "ticker": [item['ticker']],
                "description": [item['description']],
                "endpoints": {
                    "struct": f"https://iss.moex.com/iss/securities/{item["ticker"]}.json?iss.meta=off",
                    "marketdata": f"https://iss.moex.com/iss/engines/{item["engine"]}/markets/{item["market"]}/securities/{item["ticker"]}.json?iss.meta=off&iss.only=marketdata"
                }
            })
        return configs
    except KeyError as exc:
        raise KeyError(f"В элементе interests нет обязательного поля {exc}") from exc
