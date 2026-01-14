from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Tuple

from .config import ParserConfig
from .storage import RatesStorage
from .api_clients import BaseApiClient
from ..logging_config import LOGGER
from ..core.exceptions import ApiRequestError


class RatesUpdater:
    """
    Оркестратор процесса обновления курсов:
    - опрашивает всех клиентов
    - объединяет результаты
    - пишет историю и кэш
    """

    def __init__(self, config: ParserConfig, storage: RatesStorage, clients: List[BaseApiClient]):
        self.config = config
        self.storage = storage
        self.clients = clients

    def run_update(self) -> Dict:
        LOGGER.info("RatesUpdater: starting rates update...")
        all_pairs: Dict[str, Dict] = {}
        history_records: List[Dict] = []
        errors: List[Tuple[str, str]] = []

        timestamp = datetime.utcnow().isoformat() + "Z"

        for client in self.clients:
            LOGGER.info(f"RatesUpdater: fetching from {client.name}...")
            try:
                rates = client.fetch_rates()
                LOGGER.info(f"RatesUpdater: {client.name} OK ({len(rates)} rates)")
            except ApiRequestError as e:
                LOGGER.error(f"RatesUpdater: {client.name} FAILED: {e}")
                errors.append((client.name, str(e)))
                raise

            # rates: pair_key -> {rate, source, meta}
            for pair_key, payload in rates.items():
                rate = float(payload["rate"])
                source = payload.get("source", client.name)
                meta = payload.get("meta", {})

                from_code, to_code = pair_key.split("_", 1)

                # Обновляем all_pairs (в кэше хранится только последний курс)
                all_pairs[pair_key] = {
                    "rate": rate,
                    "updated_at": timestamp,
                    "source": source,
                }

                # Формируем запись истории
                record_id = f"{from_code}_{to_code}_{timestamp}"
                history_records.append(
                    {
                        "id": record_id,
                        "from_currency": from_code,
                        "to_currency": to_code,
                        "rate": rate,
                        "timestamp": timestamp,
                        "source": source,
                        "meta": meta,
                    }
                )

        # Сохранение истории и кэша
        if history_records:
            self.storage.append_history(history_records)

        if all_pairs:
            self.storage.save_cache(all_pairs, last_refresh=timestamp)
            LOGGER.info(
                f"RatesUpdater: wrote {len(all_pairs)} rates to cache, last_refresh={timestamp}"
            )
        else:
            LOGGER.warning("RatesUpdater: no rates were fetched; cache not updated")

        result = {
            "total_rates": len(all_pairs),
            "last_refresh": timestamp if all_pairs else None,
            "errors": errors,
        }
        return result
