class CurrencyNotFoundError(Exception):
    """валюта не найдена."""
    def __init__(self, code: str):
        super().__init__(f"Неизвестная валюта '{code}'")
        self.code = code


class InsufficientFundsError(Exception):
    """недостаточно средств."""
    def __init__(self, available: float, required: float, code: str):
        msg = (
            f"Недостаточно средств: доступно {available} {code}, "
            f"требуется {required} {code}"
        )
        super().__init__(msg)
        self.available = available
        self.required = required
        self.code = code


class ApiRequestError(Exception):
    """ошибка запроса к API"""
    def __init__(self, reason: str):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
        self.reason = reason
