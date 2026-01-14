from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict

from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.decorators import log_action

from .models import User, Wallet, Portfolio
from .exceptions import (
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError,
)
from .currencies import get_currency
from .utils import (
    load_users,
    save_users,
    generate_user_id,
    find_user_by_username,
    load_portfolios,
    save_portfolios,
    get_portfolio_by_user_id,
    update_portfolio,
    load_rates,
    save_rates,
)

import secrets
import hashlib


# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def _validate_amount(amount: float) -> float:
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть числом")
    if float(amount) <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return float(amount)


# REGISTER
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


# LOGIN
def login(username: str, password: str) -> Tuple[User, str]:
    user = find_user_by_username(username)
    if user is None:
        raise ValueError(f"Пользователь '{username}' не найден")

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    return user, f"Вы вошли как '{username}'"


# ПОЛУЧЕНИЕ КУРСА С УЧЁТОМ TTL
def _get_rate_internal(code_from: str, code_to: str) -> Dict:
    """
    Получение курса валюты из локального кэша Parser Service.
    """

    base_currency = get_currency(code_from)
    target_currency = get_currency(code_to)

    settings = SettingsLoader()
    ttl_seconds = settings.get("RATES_TTL_SECONDS", 300)

    rates = load_rates()
    pairs = rates

    pair_key = f"{base_currency.code}_{target_currency.code}"
    reverse_key = f"{target_currency.code}_{base_currency.code}"

    if pair_key in pairs:
        raw_updated_at = pairs[pair_key]["updated_at"]

        updated_at_str = raw_updated_at.replace("Z", "+00:00")
        updated_at = datetime.fromisoformat(updated_at_str)

        now = datetime.now(timezone.utc)

        # Проверяем, не устарели ли данные
        if now - updated_at < timedelta(seconds=ttl_seconds):
            return {
                "rate": float(pairs[pair_key]["rate"]),
                "updated_at": raw_updated_at,
                "reverse_rate": float(pairs.get(reverse_key, {}).get("rate", 0.0)),
            }

    # Если пары нет или данные устарели
    raise ApiRequestError("Parser Service временно недоступен или данные устарели")


def get_rate(code_from: str, code_to: str) -> Dict:
    """
    Обёртка над _get_rate_internal.
    Выполняет финальную валидацию валют, обрабатывает случай одинаковых кодов
    """

    code_from = code_from.upper()
    code_to = code_to.upper()

    get_currency(code_from)
    get_currency(code_to)

    if code_from == code_to:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "rate": 1.0,
            "reverse_rate": 1.0,
            "updated_at": now,
        }

    # Получаем курс из локального кэша ParserService
    return _get_rate_internal(code_from, code_to)


# ПОКУПКА ВАЛЮТЫ
@log_action("BUY", verbose=True)
def buy(user: User, currency_code: str, amount: float) -> Dict:
    amount = _validate_amount(amount)

    currency = get_currency(currency_code)

    portfolio = get_portfolio_by_user_id(user.user_id)
    wallet = portfolio.get_wallet(currency.code)

    if wallet is None:
        wallet = portfolio.add_currency(currency.code)

    before = wallet.balance
    wallet.deposit(amount)
    after = wallet.balance

    estimate_usd = None
    try:
        rate_info = get_rate(currency.code, "USD")
        estimate_usd = amount * rate_info["rate"]
    except Exception:
        pass

    update_portfolio(portfolio)

    return {
        "currency": currency.code,
        "before": before,
        "after": after,
        "amount": amount,
        "estimated_value_usd": estimate_usd,
    }

# ПРОДАЖА ВАЛЮТЫ
@log_action("SELL", verbose=True)
def sell(user: User, currency_code: str, amount: float) -> Dict:
    amount = _validate_amount(amount)

    currency = get_currency(currency_code)

    portfolio = get_portfolio_by_user_id(user.user_id)
    wallet = portfolio.get_wallet(currency.code)

    if wallet is None:
        raise CurrencyNotFoundError(currency.code)

    if wallet.balance < amount:
        raise InsufficientFundsError(wallet.balance, amount, currency.code)

    before = wallet.balance
    wallet.withdraw(amount)
    after = wallet.balance

    est_usd = None
    try:
        rate_info = get_rate(currency.code, "USD")
        est_usd = amount * rate_info["rate"]
    except Exception:
        pass

    update_portfolio(portfolio)

    return {
        "currency": currency.code,
        "before": before,
        "after": after,
        "amount": amount,
        "estimated_income_usd": est_usd,
    }


# ПОКАЗ ПОРТФЕЛЯ
def show_portfolio(user: User, base_currency: str = None) -> Dict:
    if user is None:
        raise ValueError("Сначала выполните login")

    settings = SettingsLoader()
    base_currency = base_currency or settings.get("DEFAULT_BASE_CURRENCY", "USD")
    base_currency = base_currency.upper()

    get_currency(base_currency)

    portfolio = get_portfolio_by_user_id(user.user_id)
    wallets = portfolio.wallets

    result = {
        "username": user.username,
        "base": base_currency,
        "wallets": [],
        "total": 0.0,
    }

    for w in wallets.values():
        code = w.currency_code

        if code == base_currency:
            converted = w.balance
        else:
            try:
                rate_info = get_rate(code, base_currency)
                converted = w.balance * rate_info["rate"]
            except Exception:
                converted = None

        result["wallets"].append({
            "currency_code": code,
            "balance": w.balance,
            "converted": converted,
        })

        if converted is not None:
            result["total"] += converted

    return result
