import requests
import logging
logger = logging.getLogger(__name__)


async def load_data(config):
    raw_data = {}
    for base_ticker in config["ticker"]:
        url = config["endpoints"]["marketdata"]
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as exc:
            logger.error("Network error while loading ticker %s from %s: %s", base_ticker, url, exc)
            # Re-raise so caller (and retry logic) can handle it
            raise
        if response.status_code == 200:
            raw_data[base_ticker] = response.json()
            logger.info("Successfully loaded data for ticker %s", base_ticker)
        else:
            logger.error("Error occurred while loading data for ticker %s: status code %s", base_ticker, response.status_code)
            raise Exception(f"Failed to load data from {url}. Status code: {response.status_code}")
    return raw_data
    