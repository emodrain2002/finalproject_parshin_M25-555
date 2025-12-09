from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Tuple

from .models import Portfolio, User
from .utils import (
    find_user_by_username,
    generate_user_id,
    get_portfolio_by_user_id,
    load_portfolios,
    load_rates,
    load_users,
    save_portfolios,
    save_rates,
    save_users,
    update_portfolio,
)

# ================ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ================


def _validate_currency(code: str) -> str:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Некорректный код валюты")
    return code.upper()


def _validate_amount(amount: float) -> float:
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть числом")
    if float(amount) <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return float(amount)


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


# ================ ПОЛЬЗОВАТЕЛЬ ================


def register(username: str, password: str) -> str:
    username = username.strip()
    if not username:
        raise ValueError("Имя пользователя не может быть пустым")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    if find_user_by_username(username) is not None:
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    users = load_users()
    user_id = generate_user_id(users)

    salt = secrets.token_hex(8)
    hashed = _hash_password(password, salt)

    new_user = User(
        user_id=user_id,
        username=username,
        hashed_password=hashed,
        salt=salt,
        registration_date=datetime.utcnow(),
    )

    users.append(new_user)
    save_users(users)

    portfolios = load_portfolios()
    portfolios[user_id] = Portfolio(user_id=user_id, wallets={})
    save_portfolios(portfolios)

    return f"Пользователь '{username}' зарегистрирован (id={user_id})."


def login(username: str, password: str) -> Tuple[User, str]:
    user = find_user_by_username(username)

    if user is None:
        raise ValueError(f"Пользователь '{username}' не найден")

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    return user, f"Вы вошли как '{username}'"


def show_portfolio(user: User, base_currency: str = "USD") -> dict:
    if user is None:
        raise ValueError("Сначала выполните login")

    base_currency = base_currency.upper()

    portfolio = get_portfolio_by_user_id(user.user_id)
    wallets = portfolio.wallets

    if not wallets:
        return {
            "username": user.username,
            "base": base_currency,
            "wallets": [],
            "total": 0.0,
        }

    rates = load_rates()

    result = {
        "username": user.username,
        "base": base_currency,
        "wallets": [],
        "total": 0.0,
    }

    exchange_rates = {}

    for key, data in rates.items():
        if "_" in key:
            try:
                exchange_rates[key] = float(data["rate"])
            except Exception:
                pass

    for w in wallets.values():
        code = w.currency_code
        balance = w.balance

        if code == base_currency:
            converted = balance
        else:
            pair = f"{code}_{base_currency}"
            if pair not in exchange_rates:
                raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")
            converted = balance * exchange_rates[pair]

        result["wallets"].append(
            {
                "currency_code": code,
                "balance": balance,
                "converted": converted,
            }
        )

        result["total"] += converted

    return result


# ================== ОПЕРАЦИИ =======================


def buy(user: User, currency: str, amount: float) -> dict:
    if user is None:
        raise ValueError("Сначала выполните login")

    currency = _validate_currency(currency)
    amount = _validate_amount(amount)

    portfolio = get_portfolio_by_user_id(user.user_id)

    wallet = portfolio.get_wallet(currency)
    if wallet is None:
        wallet = portfolio.add_currency(currency)

    before = wallet.balance
    wallet.deposit(amount)
    after = wallet.balance

    rates = load_rates()
    pair = f"{currency}_USD"
    rate = None
    if pair in rates:
        rate = rates[pair]["rate"]

    update_portfolio(portfolio)

    return {
        "currency": currency,
        "before": before,
        "after": after,
        "amount": amount,
        "rate": rate,
        "estimated_value": amount * rate if rate else None,
    }


def sell(user: User, currency: str, amount: float) -> dict:
    if user is None:
        raise ValueError("Сначала выполните login")

    currency = _validate_currency(currency)
    amount = _validate_amount(amount)

    portfolio = get_portfolio_by_user_id(user.user_id)
    wallet = portfolio.get_wallet(currency)

    if wallet is None:
        raise ValueError(f"У вас нет кошелька '{currency}'")

    before = wallet.balance
    wallet.withdraw(amount)
    after = wallet.balance

    rates = load_rates()
    pair = f"{currency}_USD"
    rate = None
    if pair in rates:
        rate = rates[pair]["rate"]

    update_portfolio(portfolio)

    return {
        "currency": currency,
        "before": before,
        "after": after,
        "amount": amount,
        "rate": rate,
        "estimated_income": amount * rate if rate else None,
    }


def get_rate(currency_from: str, currency_to: str) -> dict:
    currency_from = _validate_currency(currency_from)
    currency_to = _validate_currency(currency_to)

    if currency_from == currency_to:
        now = datetime.utcnow().isoformat()
        return {
            "rate": 1.0,
            "updated_at": now,
            "reverse_rate": 1.0,
        }

    key = f"{currency_from}_{currency_to}"
    reverse = f"{currency_to}_{currency_from}"

    rates = load_rates()

    if key in rates:
        data = rates[key]
        return {
            "rate": data["rate"],
            "updated_at": data["updated_at"],
            "reverse_rate": rates.get(reverse, {}).get("rate"),
        }

    stub_rate = 1.0
    now = datetime.now().isoformat()

    rates[key] = {"rate": stub_rate, "updated_at": now}
    rates[reverse] = {"rate": 1 / stub_rate, "updated_at": now}

    save_rates(rates)

    return {
        "rate": stub_rate,
        "updated_at": now,
        "reverse_rate": 1 / stub_rate,
    }
