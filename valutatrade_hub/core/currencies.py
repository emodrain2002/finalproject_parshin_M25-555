from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from .exceptions import CurrencyNotFoundError

# Базовый абстрактный класс валюты
class Currency(ABC):
    """
    Абстрактная валюта.
    Публичные атрибуты:
        name: str
        code: str
    """

    def __init__(self, name: str, code: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name не может быть пустым")

        if not isinstance(code, str):
            raise ValueError("code должен быть строкой")

        code = code.strip().upper()
        if not (2 <= len(code) <= 5) or " " in code:
            raise ValueError("code должен быть 2–5 символов, верхний регистр, без пробелов")

        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Вернуть строковое описание валюты."""
        pass


# фиат валюта
class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name, code)
        if not isinstance(issuing_country, str) or not issuing_country.strip():
            raise ValueError("issuing_country не может быть пустым")
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


# криптовалюта
class CryptoCurrency(Currency):
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float) -> None:
        super().__init__(name, code)

        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("algorithm не может быть пустым")

        if not isinstance(market_cap, (int, float)) or market_cap < 0:
            raise ValueError("market_cap должен быть числом ≥ 0")

        self.algorithm = algorithm
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# Реестр валют
_CURRENCY_REGISTRY: Dict[str, Currency] = {}


def register_currency(currency: Currency) -> None:
    """Регистрирует валюту в реестре."""
    _CURRENCY_REGISTRY[currency.code] = currency


def get_currency(code: str) -> Currency:
    """Возвращает объект валюты по коду"""
    if not isinstance(code, str) or not code.strip():
        raise CurrencyNotFoundError(code)

    code = code.upper()

    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)

    return _CURRENCY_REGISTRY[code]


# Предзагрузка базовых валют в реестр
def _load_default_currencies():
    register_currency(FiatCurrency("US Dollar", "USD", "United States"))
    register_currency(FiatCurrency("Euro", "EUR", "Eurozone"))
    register_currency(FiatCurrency("Russian Ruble", "RUB", "Russia"))

    register_currency(CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12))
    register_currency(CryptoCurrency("Ethereum", "ETH", "Ethash", 4.50e11))


_load_default_currencies()
