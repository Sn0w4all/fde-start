import logging
logger = logging.getLogger(__name__)

def normalize_data(raw_data):

    normalized_data = {}
    for ticker, ticker_data in raw_data.items():
        columns = ticker_data["marketdata"]["columns"]
        data = ticker_data["marketdata"]["data"]
        if not data:  # Пропускаем пустые данные
            normalized_data[ticker] = []
            logger.info("No data available for ticker %s", ticker)
            continue
        normalized_data[ticker] = []
        high_index = columns.index("HIGH")  # найти индекс колонки HIGH
        low_index = columns.index("LOW")  # найти индекс колонки LOW
        now_index = columns.index("LAST")  # найти индекс колонки CLOSE
        systime_index = columns.index("SYSTIME")  # найти индекс колонки SYSTIME
        boardid_index = columns.index("BOARDID")
        for entry in data:
            if entry[boardid_index] != "CETS":
                continue
            normalized_data[ticker].append({
                "date": entry[systime_index],
                "low": entry[low_index],
                "high": entry[high_index],
                "now": entry[now_index],
            })
            logger.info("Added normalized entry for ticker %s", ticker)
            break  # берём первую актуальную строку CETS и выходим
                
    return normalized_data


