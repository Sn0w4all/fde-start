from datetime import datetime

def normalize_data(raw_data):
    normalized_data = {}
    for ticker, ticker_data in raw_data.items():
        columns = ticker_data["marketdata"]["columns"]
        data = ticker_data["marketdata"]["data"]
        if not data:  # Пропускаем пустые данные
            normalized_data[ticker] = []
            print(f"No data available for ticker {ticker}")
            continue
        normalized_data[ticker] = []
        high_index = columns.index("HIGH")  # найти индекс колонки HIGH
        low_index = columns.index("LOW")  # найти индекс колонки LOW
        now_index = columns.index("LAST")  # найти индекс колонки CLOSE
        systime_index = columns.index("SYSTIME")  # найти индекс колонки SYSTIME
        
        for entry in data:
            if entry[columns.index("BOARDID")] != "CETS":
                continue
            normalized_entry = {
                "date": entry[systime_index],
                "low": entry[low_index],
                "high": entry[high_index],  #найти индекс колонки HIGH
                "now": entry[now_index],
            }
            if not normalized_data[ticker]:
                normalized_data[ticker].append(normalized_entry)
    return normalized_data


