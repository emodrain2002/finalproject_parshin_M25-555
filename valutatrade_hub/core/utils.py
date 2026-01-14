import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from .models import Portfolio, User, Wallet

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")


# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ РАБОТЫ С JSON =============

def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ======================= ПОЛЬЗОВАТЕЛИ ========================

def load_users() -> List[User]:
    data = _load_json(USERS_FILE, default=[])
    users: List[User] = []

    for item in data:
        users.append(
            User(
                user_id=item["user_id"],
                username=item["username"],
                hashed_password=item["hashed_password"],
                salt=item["salt"],
                registration_date=datetime.fromisoformat(item["registration_date"]),
            )
        )
    return users


def save_users(users: List[User]) -> None:
    data = []
    for u in users:
        data.append(
            {
                "user_id": u.user_id,
                "username": u.username,
                "hashed_password": u.hashed_password,
                "salt": u.salt,
                "registration_date": u.registration_date.isoformat(),
            }
        )
    _save_json(USERS_FILE, data)


def generate_user_id(users: List[User]) -> int:
    if not users:
        return 1
    return max(u.user_id for u in users) + 1


def find_user_by_username(username: str) -> Optional[User]:
    users = load_users()
    for u in users:
        if u.username == username:
            return u
    return None


# =============== ПОРТФЕЛИ =================

def load_portfolios() -> Dict[int, Portfolio]:
    """
    Возвращает портфолио
    """
    data = _load_json(PORTFOLIOS_FILE, default={})
    portfolios: Dict[int, Portfolio] = {}

    for item in data:
        user_id = item["user_id"]
        wallets_raw = item.get("wallets", {})

        wallets: Dict[str, Wallet] = {}
        for code, w in wallets_raw.items():
            wallets[code] = Wallet(
                currency_code=w["currency_code"],
                balance=w["balance"],
            )

        portfolios[user_id] = Portfolio(
            user_id=user_id,
            wallets=wallets,
        )

    return portfolios


def save_portfolios(portfolios: Dict[int, Portfolio]) -> None:
    data = []

    for user_id, portfolio in portfolios.items():
        wallet_dict = {}
        for code, w in portfolio.wallets.items():
            wallet_dict[code] = {
                "currency_code": w.currency_code,
                "balance": w.balance,
            }

        data.append(
            {
                "user_id": user_id,
                "wallets": wallet_dict,
            }
        )

    _save_json(PORTFOLIOS_FILE, data)


def get_portfolio_by_user_id(user_id: int) -> Portfolio:
    portfolios = load_portfolios()
    if user_id not in portfolios:
        portfolios[user_id] = Portfolio(user_id=user_id, wallets={})
        save_portfolios(portfolios)
    return portfolios[user_id]


def update_portfolio(portfolio: Portfolio) -> None:
    """Сохраняет изменения портфеля"""
    portfolios = load_portfolios()
    portfolios[portfolio.user_id] = portfolio
    save_portfolios(portfolios)


# ===================== КУРСЫ =====================

def load_rates() -> dict:
    """
    Возвращает словарь пар курсов.
    """
    data = _load_json(RATES_FILE, default={})
    if isinstance(data, dict) and "pairs" in data:
        return data["pairs"]
    return data


def save_rates(pairs: dict, last_refresh: str | None = None) -> None:
    """
    Сохраняет пары курсов
    """
    data = {"pairs": pairs}
    if last_refresh is not None:
        data["last_refresh"] = last_refresh
    _save_json(RATES_FILE, data)