import time

from .config import ParserConfig
from .storage import RatesStorage
from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .updater import RatesUpdater
from ..logging_config import LOGGER


def run_scheduler(interval_seconds: int = 300):
    """
    Периодически запускает обновление курсов
    """
    config = ParserConfig()
    storage = RatesStorage(config)
    clients = [
        CoinGeckoClient(config),
        ExchangeRateApiClient(config),
    ]
    updater = RatesUpdater(config, storage, clients)

    while True:
        try:
            updater.run_update()
        except Exception as e:
            LOGGER.error(f"Scheduler: update failed: {e}")
        time.sleep(interval_seconds)
