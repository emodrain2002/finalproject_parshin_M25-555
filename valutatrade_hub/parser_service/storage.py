from __future__ import annotations

import json
import os
from typing import List, Dict, Any

from .config import ParserConfig


class RatesStorage:
    """
    Отвечает за чтение/запись
    """

    def __init__(self, config: ParserConfig):
        self.config = config
        os.makedirs(os.path.dirname(self.config.RATES_FILE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(self.config.HISTORY_FILE_PATH), exist_ok=True)

    # ---------- Вспомогательные методы ----------
    @staticmethod
    def _atomic_write(path: str, data: Any) -> None:
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp_path, path)

    @staticmethod
    def _load_json(path: str, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return default

    # ---------- Кэш текущих курсов ----------
    def load_cache(self) -> Dict:
        """
        Читаем data/rates.json
        """
        data = self._load_json(self.config.RATES_FILE_PATH, default={})
        return data

    def save_cache(self, pairs: Dict[str, Dict], last_refresh: str) -> None:
        data = {
            "pairs": pairs,
            "last_refresh": last_refresh,
        }
        self._atomic_write(self.config.RATES_FILE_PATH, data)

    # ---------- История измерений ----------
    def load_history(self) -> List[Dict]:
        data = self._load_json(self.config.HISTORY_FILE_PATH, default=[])
        if isinstance(data, list):
            return data
        return []

    def append_history(self, records: List[Dict]) -> None:
        """
        Добавляет записи истории курсов
        """
        history = self.load_history()

        existing_ids = {r.get("id") for r in history if "id" in r}
        new_records = [r for r in records if r.get("id") not in existing_ids]

        history.extend(new_records)
        self._atomic_write(self.config.HISTORY_FILE_PATH, history)
