from __future__ import annotations

from functools import wraps
from typing import Callable

from .logging_config import LOGGER


def log_action(action: str, verbose: bool = False):
    """
    Декоратор логирования доменных операций.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = None
            if args:
                if hasattr(args[0], "username"):
                    user = args[0].username
                elif len(args) > 1 and hasattr(args[1], "username"):
                    user = args[1].username

            currency = kwargs.get("currency") or (args[2] if len(args) > 2 else None)
            amount = kwargs.get("amount")

            try:
                result = func(*args, **kwargs)

                msg = (
                    f"{action} user='{user}' "
                    f"currency='{currency}' amount='{amount}' "
                    f"result=OK"
                )

                if verbose and isinstance(result, dict):
                    if "before" in result and "after" in result:
                        msg += (
                            f" before={result['before']} "
                            f"after={result['after']}"
                        )

                LOGGER.info(msg)
                return result

            except Exception as e:
                error_msg = (
                    f"{action} user='{user}' "
                    f"currency='{currency}' amount='{amount}' "
                    f"result=ERROR "
                    f"error_type={type(e).__name__} "
                    f"error=\"{str(e)}\""
                )
                LOGGER.error(error_msg)

                raise

        return wrapper

    return decorator
