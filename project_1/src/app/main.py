#импорт модулей проекта
import config as config
import loaders.data_loader as data_loader
import transformers.normalize as normalize
import storage.repository as repository
import analytics.report_stats as report_stats

#экспеиментируем с логированием
import logging
logger = logging.getLogger(__name__)
tickers = ["GLDRUB_TOM", "CNYRUB_TOM"] ##не забыть найти где находятся тикеры "SiZ6, "GDZ6"

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )



def main():
    logger.info("Starting the application")
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
    logger.info("Finished the application")

# Пишем лог файл

if __name__ == "__main__":
    setup_logging()
    main()