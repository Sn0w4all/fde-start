from ..storage.repository import load_latest_data
from datetime import datetime
from ..config import saved_type as st

import logging
logger = logging.getLogger(__name__)

def normalize_data(raw_data, interests):
    normalized_data = load_latest_data(st.NORMALIZE)
    if normalized_data is None:
        normalized_data = {}
    for ticker, ticker_data in raw_data.items():
        # Получаем description для этого тикера
        description = None
        for interest in interests:
            if interest["ticker"] == ticker:
                description = interest.get("description", "")
                break
        
        # Инициализируем структуру со словарём, содержащим description и data
        if ticker not in normalized_data:
            normalized_data[ticker] = {
                'description': description,
                'data': []
            }
        # Если уже есть более менее свежие данные - оставляем их
   
        current_dt = datetime.now()
        last_entry = normalized_data[ticker]["data"][-1]
        last_dt = datetime.strptime(last_entry["date"], "%Y-%m-%d %H:%M:%S")
        delta = current_dt - last_dt
        hours = 1 + int(delta.total_seconds() // 3600)
        if (hours < 4):
            logger.info("По тикеру %s уже есть свежие данные не позднее %d часов", ticker, hours)
            break

        columns = ticker_data["marketdata"]["columns"]
        data = ticker_data["marketdata"]["data"]
        if not data:  # Пропускаем пустые данные
            logger.info("No data available for ticker %s", ticker)
            continue

        high_index = columns.index("HIGH")  # найти индекс колонки HIGH
        low_index = columns.index("LOW")  # найти индекс колонки LOW
        now_index = columns.index("LAST")  # найти индекс колонки CLOSE
        systime_index = columns.index("SYSTIME")  # найти индекс колонки SYSTIME
        boardid_index = columns.index("BOARDID")
        for entry in data:
            if entry[boardid_index] != "CETS" and entry[boardid_index] != "RFUD":
                continue

            new_normalized_data = {
                "date": entry[systime_index],
                "low": entry[low_index],
                "high": entry[high_index],
                "now": entry[now_index],
            }

            if new_normalized_data not in normalized_data[ticker]["data"]:
                normalized_data[ticker]["data"].append(new_normalized_data)
            logger.info("Added normalized entry for ticker %s", ticker)
            break  # берём первую актуальную строку CETS и выходим

    return normalized_data


