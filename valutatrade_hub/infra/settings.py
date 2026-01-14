from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class SettingsLoader:
    """
    Singleton для загрузки и хранения конфигурации проекта.
    """

    _instance: Optional["SettingsLoader"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Чтобы init не выполнялся повторно при каждом вызове SettingsLoader()
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True

        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

        data_dir = os.path.join(project_root, "data")
        log_dir = os.path.join(project_root, "logs")

        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        # Значения по умолчанию
        self._config: Dict[str, Any] = {
            "DATA_DIR": data_dir,
            "USERS_FILE": os.path.join(data_dir, "users.json"),
            "PORTFOLIOS_FILE": os.path.join(data_dir, "portfolios.json"),
            "RATES_FILE": os.path.join(data_dir, "rates.json"),

            "LOG_DIR": log_dir,
            "LOG_FILE": os.path.join(log_dir, "actions.log"),

            "RATES_TTL_SECONDS": 300,

            "DEFAULT_BASE_CURRENCY": "USD",

            "LOG_FORMAT": "[{timestamp}] {level} {action} {message}",
        }

        external_config = os.path.join(project_root, "config.json")
        if os.path.isfile(external_config):
            try:
                with open(external_config, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config.update(data)
            except Exception:
                pass

    # ПУБЛИЧНЫЕ МЕТОДЫ
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить параметр конфигурации
        """
        return self._config.get(key, default)

    def reload(self) -> None:
        """
        Перезагрузка конфигурации
        """
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        external_config = os.path.join(project_root, "config.json")

        if os.path.isfile(external_config):
            try:
                with open(external_config, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config.update(data)
            except Exception:
                pass
