from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any
from time import perf_counter

import requests

from .config import ParserConfig
from ..core.exceptions import ApiRequestError
from ..logging_config import LOGGER


class BaseApiClient(ABC):
    """
    Базовый клиент внешнего API
    """

    def __init__(self, config: ParserConfig):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        ...


class CoinGeckoClient(BaseApiClient):
    @property
    def name(self) -> str:
        return "CoinGecko"

    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        ids = [self.config.CRYPTO_ID_MAP[code] for code in self.config.CRYPTO_CURRENCIES]
        params = {
            "ids": ",".join(ids),
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }

        start = perf_counter()
        try:
            resp = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
        except requests.RequestException as e:
            raise ApiRequestError(f"{self.name}: {e}")

        elapsed_ms = int((perf_counter() - start) * 1000)

        if resp.status_code != 200:
            raise ApiRequestError(
                f"{self.name}: статус {resp.status_code}, тело={resp.text[:200]}"
            )

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiRequestError(f"{self.name}: некорректный JSON: {e}")

        result: Dict[str, Dict[str, Any]] = {}
        for code in self.config.CRYPTO_CURRENCIES:
            coin_id = self.config.CRYPTO_ID_MAP.get(code)
            if not coin_id or coin_id not in data:
                continue
            vs_map = data[coin_id]
            vs_key = self.config.BASE_CURRENCY.lower()
            if vs_key not in vs_map:
                continue

            rate = float(vs_map[vs_key])
            pair_key = f"{code}_{self.config.BASE_CURRENCY}"

            meta = {
                "raw_id": coin_id,
                "request_ms": elapsed_ms,
                "status_code": resp.status_code,
                "etag": resp.headers.get("ETag", ""),
            }

            result[pair_key] = {
                "rate": rate,
                "source": self.name,
                "meta": meta,
            }

        LOGGER.info(f"{self.name}: получено {len(result)} курсов")
        return result


class ExchangeRateApiClient(BaseApiClient):
    @property
    def name(self) -> str:
        return "ExchangeRate-API"

    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError(
                f"{self.name}: ключ API не задан (переменная EXCHANGERATE_API_KEY)"
            )

        url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"

        start = perf_counter()
        try:
            resp = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            raise ApiRequestError(f"{self.name}: {e}")

        elapsed_ms = int((perf_counter() - start) * 1000)

        if resp.status_code != 200:
            raise ApiRequestError(
                f"{self.name}: статус {resp.status_code}, тело={resp.text[:200]}"
            )

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiRequestError(f"{self.name}: некорректный JSON: {e}")

        if data.get("result") != "success":
            raise ApiRequestError(
                f"{self.name}: результат={data.get('result')}, ошибка={data.get('error-type')}"
            )

        rates = data.get("conversion_rates", {})
        base_code = data.get("base_code", self.config.BASE_CURRENCY)

        result: Dict[str, Dict[str, Any]] = {}

        for code in self.config.FIAT_CURRENCIES:
            if code not in rates:
                continue

            api_rate = float(rates[code])
            if api_rate == 0:
                continue

            pair_key = f"{code}_{base_code}"
            real_rate = 1.0 / api_rate

            meta = {
                "raw_id": base_code,
                "request_ms": elapsed_ms,
                "status_code": resp.status_code,
                "etag": resp.headers.get("ETag", ""),
            }

            result[pair_key] = {
                "rate": real_rate,
                "source": self.name,
                "meta": meta,
            }

        LOGGER.info(f"{self.name}: получено {len(result)} курсов")
        return result
