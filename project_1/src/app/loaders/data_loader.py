import requests
import logging
logger = logging.getLogger(__name__)


def load_data(config):
    raw_data = {}
    for base_ticker in config["tickers"]:
        url = config["endpoints"]["marketdata"].format(ticker=base_ticker)
        response = requests.get(url)
        if response.status_code == 200:
            raw_data[base_ticker] = response.json()
            logger.info("Successfully loaded data for ticker %s", base_ticker)
        else:
            logger.error("Error occurred while loading data for ticker %s: status code %s", base_ticker, response.status_code)
            raise Exception(f"Failed to load data from {url}. Status code: {response.status_code}")
    return raw_data
    