import shlex

from valutatrade_hub.parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater

from ..core.usecases import (
    register,
    login,
    show_portfolio,
    buy,
    sell,
    get_rate,
)

from ..core.exceptions import (
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError,
)


def print_help():
    print("\nДоступные команды:")
    print("  register --username <str> --password <str>")
    print("  login --username <str> --password <str>")
    print("  show-portfolio [--base <VAL>]")
    print("  buy --currency <VAL> --amount <FLOAT>")
    print("  sell --currency <VAL> --amount <FLOAT>")
    print("  get-rate --from <VAL> --to <VAL>")
    print("  help")
    print("  exit\n")


def parse_args(args: list) -> dict:
    """Простейший парсер аргументов"""
    result = {}
    skip = False
    for i, token in enumerate(args):
        if skip:
            skip = False
            continue

        if token.startswith("--"):
            key = token[2:]
            if i + 1 < len(args):
                result[key] = args[i + 1]
                skip = True
            else:
                result[key] = None
    return result


def run_cli():
    print("\n*** Виртуальный валютный кошелёк ***")
    print_help()

    current_user = None

    while True:
        try:
            raw = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not raw:
            continue

        try:
            parts = shlex.split(raw)
        except ValueError:
            print("Ошибка парсинга команды")
            continue

        cmd = parts[0]
        args = parse_args(parts[1:])

        # REGISTER
        if cmd == "register":
            try:
                username = args.get("username")
                password = args.get("password")

                if not username or not password:
                    print("Используйте: register --username <str> --password <str>")
                    continue

                msg = register(username, password)
                print(msg)
                print("Теперь войдите командой login.")
            except Exception as e:
                print(e)

        # LOGIN
        elif cmd == "login":
            try:
                username = args.get("username")
                password = args.get("password")

                if not username or not password:
                    print("Используйте: login --username <str> --password <str>")
                    continue

                current_user, msg = login(username, password)
                print(msg)

            except Exception as e:
                print(e)

        # SHOW PORTFOLIO
        elif cmd == "show-portfolio":
            if current_user is None:
                print("Сначала выполните login")
                continue

            base = args.get("base")

            try:
                data = show_portfolio(current_user, base_currency=base)

                print(f"\nПортфель пользователя '{data['username']}' (база: {data['base']}):")

                wallets = data["wallets"]

                if not wallets:
                    print("Портфель пуст.")
                    continue

                for w in wallets:
                    code = w["currency_code"]
                    bal = w["balance"]
                    conv = w["converted"]

                    if conv is None:
                        print(f"- {code}: {bal:.4f} → курс недоступен")
                    else:
                        print(f"- {code}: {bal:.4f} → {conv:.4f} {data['base']}")

                print("-" * 35)
                print(f"ИТОГО: {data['total']:.4f} {data['base']}\n")

            except CurrencyNotFoundError as e:
                print(e)
                print("Проверьте код валюты или используйте команду get-rate.")

            except ApiRequestError as e:
                print(e)
                print("Не удалось обновить курсы. Повторите позже.")

            except Exception as e:
                print(e)

        # BUY
        elif cmd == "buy":
            if current_user is None:
                print("Сначала выполните login")
                continue

            try:
                currency = args.get("currency")
                amount = args.get("amount")

                if not currency or amount is None:
                    print("Используйте: buy --currency <VAL> --amount <FLOAT>")
                    continue

                amount = float(amount)

                result = buy(current_user, currency, amount)

                print("\nПокупка выполнена:")
                print(f"- Валюта: {result['currency']}")
                print(f"- Было: {result['before']:.4f}")
                print(f"- Стало: {result['after']:.4f}")

                if result["estimated_value_usd"] is not None:
                    print(f"- Оценочная стоимость: {result['estimated_value_usd']:.4f} USD")
                else:
                    print("- Оценочная стоимость недоступна (нет курса).")

                print("")

            except CurrencyNotFoundError as e:
                print(e)
                print("Проверьте поддерживаемые валюты через get-rate.")

            except ValueError as e:
                print(e)

            except ApiRequestError as e:
                print(e)
                print("Курс недоступен — повторите попытку позже.")

            except Exception as e:
                print(e)

        # SELL
        elif cmd == "sell":
            if current_user is None:
                print("Сначала выполните login")
                continue

            try:
                currency = args.get("currency")
                amount = args.get("amount")

                if not currency or amount is None:
                    print("Используйте: sell --currency <VAL> --amount <FLOAT>")
                    continue

                amount = float(amount)

                result = sell(current_user, currency, amount)

                print("\nПродажа выполнена:")
                print(f"- Валюта: {result['currency']}")
                print(f"- Было: {result['before']:.4f}")
                print(f"- Стало: {result['after']:.4f}")

                if result["estimated_income_usd"] is not None:
                    print(f"- Оценочная выручка: {result['estimated_income_usd']:.4f} USD")
                else:
                    print("- Курс недоступен — оценка невозможна.")

                print("")

            except InsufficientFundsError as e:
                print(e)

            except CurrencyNotFoundError as e:
                print(e)
                print("Проверьте код валюты или выполните get-rate.")

            except ApiRequestError as e:
                print(e)
                print("Курс недоступен — повторите позже.")

            except ValueError as e:
                print(e)

            except Exception as e:
                print(e)

        # GET-RATE
        elif cmd == "get-rate":
            try:
                f = args.get("from")
                t = args.get("to")

                if not f or not t:
                    print("Используйте: get-rate --from <VAL> --to <VAL>")
                    continue

                data = get_rate(f, t)

                print(f"\nКурс {f.upper()} → {t.upper()}: {data['rate']} (обновлено: {data['updated_at']})")
                print(f"Обратный курс {t.upper()} → {f.upper()}: {data['reverse_rate']}\n")

            except CurrencyNotFoundError as e:
                print(e)
                print("Проверьте код валюты. Доступные валюты: USD, EUR, RUB, BTC, ETH")

            except ApiRequestError as e:
                print(e)
                print("Загрузка курса невозможна — Parser Service недоступен.")

            except Exception as e:
                print(e)


        # UPDATE-RATES
        elif cmd == "update-rates":
            source = args.get("source")

            config = ParserConfig()
            storage = RatesStorage(config)
            clients = []

            if source is None:
                clients = [
                    CoinGeckoClient(config),
                    ExchangeRateApiClient(config),
                ]
            else:
                source = source.lower()
                if source == "coingecko":
                    clients = [CoinGeckoClient(config)]
                elif source in ("exchangerate", "exchangerate-api"):
                    clients = [ExchangeRateApiClient(config)]
                else:
                    print("Неизвестный источник. Используйте coingecko или exchangerate.")
                    continue

            updater = RatesUpdater(config, storage, clients)

            print("INFO: Starting rates update...")
            result = updater.run_update()

            total = result["total_rates"]
            last_refresh = result["last_refresh"]
            errors = result["errors"]

            if errors:
                for src, msg in errors:
                    print(f"ERROR: Failed to fetch from {src}: {msg}")
                print(
                    f"Update completed with errors. "
                    f"Успешно обновлено {total} курсов."
                )
            else:
                print(
                    f"Update successful. Total rates updated: {total}. "
                    f"Last refresh: {last_refresh}"
                )

        # SHOW-RATES
        elif cmd == "show-rates":
            config = ParserConfig()
            storage = RatesStorage(config)

            data = storage.load_cache()
            if not data or "pairs" not in data:
                print("Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")
                continue

            pairs = data["pairs"]
            last_refresh = data.get("last_refresh", "unknown")

            currency_filter = args.get("currency")
            top_n = args.get("top")
            base = args.get("base")

            # Базовая валюта по умолчанию — та же, что в конфиге
            base_currency = (base or config.BASE_CURRENCY).upper()

            usd_rates = {}
            for pair_key, payload in pairs.items():
                from_code, to_code = pair_key.split("_", 1)
                if to_code != config.BASE_CURRENCY:
                    continue
                usd_rates[from_code] = float(payload["rate"])

            if base_currency != config.BASE_CURRENCY:
                if base_currency not in usd_rates:
                    print(f"Базовая валюта '{base_currency}' не найдена в кеше.")
                    continue
                base_usd = usd_rates[base_currency]
                if base_usd == 0:
                    print(f"Невозможно пересчитать в базу '{base_currency}'.")
                    continue

                # пересчёт в base_currency
                converted_pairs = {}
                for code, rate_usd in usd_rates.items():
                    rate_base = rate_usd / base_usd
                    key = f"{code}_{base_currency}"
                    converted_pairs[key] = rate_base

                # из converted_pairs строим список для вывода
                display_pairs = {
                    key: rate for key, rate in converted_pairs.items()
                }
            else:
                # база = USD
                display_pairs = {}
                for pair_key, payload in pairs.items():
                    display_pairs[pair_key] = float(payload["rate"])

            # Фильтрация по валюте
            if currency_filter:
                code = currency_filter.upper()
                display_pairs = {
                    k: v for k, v in display_pairs.items()
                    if k.startswith(code + "_")
                }
                if not display_pairs:
                    print(f"Курс для '{code}' не найден в кеше.")
                    continue

            # Фильтрация по top N
            if top_n is not None:
                try:
                    n = int(top_n)
                except ValueError:
                    print("--top должен быть числом")
                    continue

                crypto_set = set(config.CRYPTO_CURRENCIES)
                filtered = {
                    k: v for k, v in display_pairs.items()
                    if k.split("_", 1)[0] in crypto_set
                }
                display_pairs = dict(
                    sorted(filtered.items(), key=lambda item: item[1], reverse=True)[:n]
                )

            print(f"Rates from cache (updated at {last_refresh}):")
            for pair_key, rate in sorted(display_pairs.items()):
                print(f"- {pair_key}: {rate}")

        elif cmd == "help":
            print_help()

        elif cmd == "exit":
            print("Выход.")
            break
        
        else:
            print("Неизвестная команда. Введите help.")
