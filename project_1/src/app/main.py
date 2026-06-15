#импорт модулей проекта

from . import config
from .loaders import data_loader
from .transformers import normalize
from .storage import repository
from .analytics import report_stats
# запуск: 
# cd /Users/antonzotov/dev/fde-start/project_1/src
# python -m app.main


#экспеиментируем с логированием
import logging
#вариант по времени
from logging.handlers import TimedRotatingFileHandler
handler = TimedRotatingFileHandler(
    "app.log",
    when="midnight", #каждый день
    backupCount=3,               # храним 3 старых файла, остальное удаляется
    encoding="utf-8",
)

#вариант по размеру
# from logging.handlers import RotatingFileHandler
# handler = RotatingFileHandler(
#     "app.log",
#     maxBytes=1 * 1024 * 1024,   # 1 МБ — порог, после которого ротируем
#     backupCount=3,               # храним 3 старых файла, остальное удаляется
#     encoding="utf-8",
# )

logger = logging.getLogger(__name__)
interest = [
    {
        'ticker': 'GLDRUB_TOM',
        'engine': 'currency',
        'market': 'selt'
    }, 
    {
        'ticker': 'CNYRUB_TOM',
        'engine': 'currency',
        'market': 'selt'
    },
    {
        'ticker': 'SiZ6',
        'engine': 'futures',
        'market': 'forts'

    },   
    {
        'ticker': 'GDZ6',
        'engine': 'futures',
        'market': 'forts'
    }
] 

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            handler,
            logging.StreamHandler(),
        ],
    )


def main():
    logger.info("Starting the application")
    config_list = config.get_config(interest) # Получаем конфиги для каждого интереса
    raw_data = {}
    for config_iis in config_list:
        raw_data.update(data_loader.load_data(config_iis))
    repository.save_data(raw_data, "raw") # Сырые данные складываем в data
"""  normalized_data = normalize.normalize_data(raw_data) # Трансформируем данные
    repository.save_data(normalized_data, "normalized") # Готовые данные складываем в data
    reports = []
    for position, data in normalized_data.items():
        report = report_stats.get_analysis(data, position) # Анализируем данные 
        reports.append(report)
    repository.save_data(reports, "reports") # Сохраняем отчеты в data
    logger.info("Finished the application")
"""
# Пишем лог файл

if __name__ == "__main__":
    setup_logging()
    main()