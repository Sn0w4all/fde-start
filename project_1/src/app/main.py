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
import reports.report_builder as report_builder 


SCRIPT_DIR = Path(__file__).resolve().parent

load_dotenv(SCRIPT_DIR / "claude_api.env")
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)
tickers = ["GLDRUB_TOM", "CNYRUB_P"] ##не забыть найти где находятся тикеры "SiZ6, "GDZ6"


def main():
    config_iis = config.get_config(tickers) # Получаем конфиг
    raw_data = data_loader.load_data(config_iis) # Подключаемся к IIS MOEX и забираем данные.
    repository.save_raw_data(raw_data) # Сырые данные складываем в data


# Трансформируем данные и сохраняем в storage

# Анализируем данные 

# Строим отчет и сохраняем его в data

# Пишем лог файл

if __name__ == "__main__":
    main()