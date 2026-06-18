#импорт модулей проекта

from . import config
from .loaders import data_loader
from .transformers import normalize
from .storage import repository
from .analytics import report_stats
from .reports import report_builder
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
interests = [
    {
        'ticker': 'GLDRUB_TOM',
        'description': 'Бессрочный фьючерс - золото в рублях',
        'engine': 'currency',
        'market': 'selt'
    }, 
    {
        'ticker': 'CNYRUB_TOM',
        'description': 'Бессрочный фьючерс - валютная пара: Юань / Рубль',
        'engine': 'currency',
        'market': 'selt'
    },
    {
        'ticker': 'SiZ6',
        'description': 'Фьючерс со сроком экспирации в декабре - валютная пара: Доллар США / Рубль',
        'engine': 'futures',
        'market': 'forts'

    },   
    {
        'ticker': 'GDZ6',
        'description': 'Фьючерс со сроком экспирации в декабре - золото в долларах США',
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
    config_list = config.get_config(interests) # Получаем конфиги для каждого интереса
    raw_data = {}
    for config_iis in config_list:
        raw_data.update(data_loader.load_data(config_iis))
    repository.save_data(raw_data, "raw", ".json") # Сырые данные складываем в data
    normalized_data = normalize.normalize_data(raw_data, interests) # Трансформируем данные
    repository.save_data(normalized_data, "normalized", ".json") # Готовые данные складываем в data
    text_reports = report_stats.get_analysis(normalized_data) # Анализируем данные 
    repository.save_data(text_reports, "reports", ".json") # Сохраняем отчеты в data
    html_reports = report_builder.get_html_report(text_reports) # Преобразовываем тестовый отчет в HTML
    repository.save_data(html_reports, "html_reports",".html") # Сохраняем html в data
    logger.info("Finished the application")

# Пишем лог файл

if __name__ == "__main__":
    setup_logging()
    main()