from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Dict, Optional


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        self._user_id = user_id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    def _make_hash(self, password: str) -> str:
        """Создает хэш"""
        data = (password + self._salt).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def get_user_info(self) -> dict:
        """Информация о пользователе"""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя с хешированием нового пароля"""
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        self._salt = secrets.token_hex(8)
        self._hashed_password = self._make_hash(new_password)

    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль на совпадение с сохранённым хешем"""
        return self._make_hash(password) == self._hashed_password


class Wallet:
    """Кошелёк пользователя для конкретной валюты"""

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        self.currency_code = currency_code.upper()
        self._balance = 0.0
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """Пополнение баланса"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        """Снятие средств"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        amount = float(amount)
        if amount > self._balance:
            raise ValueError("Недостаточно средств на кошельке")

        self._balance -= amount

    def get_balance_info(self) -> dict:
        """Информация о текущем балансе"""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }


class Portfolio:
    def __init__(
        self,
        user_id: int,
        wallets: Optional[Dict[str, Wallet]] = None,
        user: Optional[User] = None,
    ) -> None:
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = wallets.copy() if wallets else {}
        self._user = user

    @property
    def user(self) -> Optional[User]:
        """Возвращает объект пользователя"""
        return self._user

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Возвращает копию словаря кошельков"""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавляет новый кошелёк в портфель
        """
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Кошелёк с валютой '{code}' уже существует")

        wallet = Wallet(currency_code=code)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """Возвращает объект wallet по коду валюты или None, если его нет."""
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")
        code = currency_code.upper()
        return self._wallets.get(code)

    def get_total_value(
        self,
        base_currency: str = "USD",
        exchange_rates: Optional[Dict[str, float]] = None,
    ) -> float:
        if not isinstance(base_currency, str) or not base_currency.strip():
            raise ValueError("Базовая валюта не может быть пустой")

        base = base_currency.upper()
        total = 0.0

        for wallet in self._wallets.values():
            code = wallet.currency_code

            if code == base:
                total += wallet.balance
                continue

            if exchange_rates is None:
                raise ValueError(
                    "Для конвертации требуется словарь exchange_rates",
                )

            pair_key = f"{code}_{base}"
            if pair_key not in exchange_rates:
                raise ValueError(
                    f"Неизвестный курс для пары {code}->{base}",
                )

            rate = exchange_rates[pair_key]
            total += wallet.balance * rate

        return total
