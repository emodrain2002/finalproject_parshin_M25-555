import os
from dataclasses import dataclass
import os.path as path


@dataclass
class ParserConfig:
    # Ключ загружается из переменной окружения
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Списки валют
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP: dict = None

    # Пути к файлам
    RATES_FILE_PATH: str = ""
    HISTORY_FILE_PATH: str = ""

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10

    def __post_init__(self):
        if self.CRYPTO_ID_MAP is None:
            self.CRYPTO_ID_MAP = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
            }

        project_root = path.abspath(path.join(path.dirname(__file__), "..", ".."))
        data_dir = path.join(project_root, "data")

        os.makedirs(data_dir, exist_ok=True)

        if not self.RATES_FILE_PATH:
            self.RATES_FILE_PATH = path.join(data_dir, "rates.json")
        if not self.HISTORY_FILE_PATH:
            self.HISTORY_FILE_PATH = path.join(data_dir, "exchange_rates.json")
