#импорт модулей проекта

from .config import saved_format as sf, saved_type as st, get_config
from .loaders import data_loader
from .transformers import normalize
from .storage import repository
from .analytics import report_stats
from .reports import report_builder
from .retry import with_backoff
import anthropic
import requests
import asyncio

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

#Ошибки которые ретраим
_RETRY_EXC = (
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.APITimeoutError,
    anthropic.APIError,
    anthropic.PermissionDeniedError,
    requests.exceptions.RequestException,
)

logger = logging.getLogger(__name__)

#То что нам интересно
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




async def main():
    logger.info("Starting the application")

    if interests == []:
        logger.info("Nothing interesting. Finished the application")
        raise SystemExit(0)
    
    
    try:
        # Шаг 1. Получаем конфиги для каждого тикера который нас интересует
        config_list = get_config(interests) 

        # Шаг 2. Получаем сырые данные из ISS MOEX для каждого интересующего тикера
        raw_data = {}
        for config_iis in config_list:
            loaded = await with_backoff(lambda: data_loader.load_data(config_iis), exc_types=_RETRY_EXC)
            if loaded:
                raw_data.update(loaded)
        if raw_data == {}:
            logger.error("Raw data is Empty")
            logger.info("Finished the application")
            raise SystemExit(1)
        # Шаг 2.5. Сырые данные складываем в data
        repository.save_data(raw_data, st.RAW, sf.JSON) 

        # Шаг 3. Трансформируем данные в краткую форму
        normalized_data = normalize.normalize_data(raw_data, interests) 
        # Шаг 3.5. Готовые данные складываем в data
        repository.save_data(normalized_data, st.NORMALIZE, sf.JSON) 

        # Шаг 4. Готовим анализ через LLM     
        text_reports = await with_backoff(
            lambda: report_stats.get_analysis(normalized_data),
            exc_types=_RETRY_EXC
        )
        # Шаг 4.5. Сохраняем отчет в data
        repository.save_data(text_reports, st.TEXT_REPORT, sf.JSON) 

        # Шаг 5. Преобразовываем тестовый отчет в HTML через LLM   
        html_reports =  await with_backoff(
            lambda: report_builder.get_html_report(text_reports), 
            exc_types=_RETRY_EXC
        )
        
        # Шаг 5. Сохраняем html в data
        repository.save_data(html_reports, st.HTML, sf.HTML) 
        logger.info("Finished the application")

    except KeyError as exc:
        logger.error("Missing key in interest item: %s", exc)
    except requests.exceptions.RequestException as e:
        logger.error("Network error %s", e)
    except anthropic.BadRequestError as e:
        logger.error("API Error: %s", e)
    except Exception as e:
        logger.exception("Unexpected error")


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())