#импорт общих бибилиотек
import anthropic
from typing import Optional
import os
from pydantic import BaseModel
import argparse
from pathlib import Path
import json 
from dotenv import load_dotenv
import argparse
from pathlib import Path
import httpx
import os
from bs4 import BeautifulSoup


#импорт модулей проекта
import config as config
import loaders.data_loader as data_loader
import transformers.normalize as normalize
import storage.repository as repository
import analytics.report_stats as report_stats



tickers = ["GLDRUB_TOM", "CNYRUB_TOM"] ##не забыть найти где находятся тикеры "SiZ6, "GDZ6"


def main():
    config_iis = config.get_config(tickers) # Получаем конфиг
    raw_data = data_loader.load_data(config_iis) # Подключаемся к IIS MOEX и забираем данные.
    repository.save_data(raw_data, "raw") # Сырые данные складываем в data
    normalized_data = normalize.normalize_data(raw_data) # Трансформируем данные
    repository.save_data(normalized_data, "normalized") # Готовые данные складываем в data
    reports = []
    for position, data in normalized_data.items():
        report = report_stats.get_analysis(data, position) # Анализируем данные 
        reports.append(report)
    repository.save_data(reports, "reports") # Сохраняем отчеты в data


# Пишем лог файл

if __name__ == "__main__":
    main()