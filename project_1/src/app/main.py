#импорт общих бибилиотек
import anthropic
from typing import Optional
import os
from pydantic import BaseModel
import argparse
from pathlib import Path
import json 
import requests
from dotenv import load_dotenv
import argparse
from pathlib import Path
import httpx
import requests
import os
from bs4 import BeautifulSoup

#импорт модулей проекта
import app.config as config
import app.loaders.data_loader as data_loader
import app.transformers.normalize as normalize
import app.storage.repository as repository
import app.reports.report_builder as report_builder 


SCRIPT_DIR = Path(__file__).resolve().parent

load_dotenv(SCRIPT_DIR / "claude_api.env")
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)


# Подключаемся к IIS MOEX и забираем данные.


# Сырые данные складываем в storage

# Трансформируем данные и сохраняем в storage

# Анализируем данные 

# Строим отчет и сохраняем его в data

# Пишем лог файл