import shlex

from ..core.usecases import (
    buy,
    get_rate,
    login,
    register,
    sell,
    show_portfolio,
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
    """Парсер аргументов"""
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
            raw = input("> ").strip()
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

        elif cmd == "show-portfolio":
            if current_user is None:
                print("Сначала выполните login")
                continue

            base = args.get("base", "USD").upper()

            try:
                data = show_portfolio(current_user, base_currency=base)

                username = data["username"]
                print(f"Портфель пользователя '{username}' (база: {base}):")

                if not data["wallets"]:
                    print("Портфель пуст.")
                    continue

                for w in data["wallets"]:
                    code = w["currency_code"]
                    bal = w["balance"]
                    conv = w["converted"]
                    print(f"- {code}: {bal:.4f} → {conv:.4f} {base}")

                print("-" * 35)
                print(f"ИТОГО: {data['total']:.4f} {base}")

            except Exception as e:
                print(e)

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

                print(f"Покупка выполнена: {result['amount']:.4f} {result['currency']}")
                print(f"- было: {result['before']:.4f}")
                print(f"- стало: {result['after']:.4f}")

                if result["rate"]:
                    print(f"Курс: {result['rate']} USD/{result['currency']}")
                    print(f"Оценочная стоимость: {result['estimated_value']:.4f} USD")

            except Exception as e:
                print(e)

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

                print(f"Продажа выполнена: {result['amount']:.4f} {result['currency']}")
                print(f"- было: {result['before']:.4f}")
                print(f"- стало: {result['after']:.4f}")

                if result["rate"]:
                    print(f"Курс: {result['rate']} USD/{result['currency']}")
                    print(f"Оценочная выручка: {result['estimated_income']:.4f} USD")

            except Exception as e:
                print(e)

        elif cmd == "get-rate":
            try:
                f = args.get("from")
                t = args.get("to")

                if not f or not t:
                    print("Используйте: get-rate --from <VAL> --to <VAL>")
                    continue

                data = get_rate(f, t)

                print(
                    f"Курс {f.upper()}→{t.upper()}: {data['rate']} "
                    f"(обновлено: {data['updated_at']})"
                )
                if data["reverse_rate"]:
                    print(
                        f"Обратный курс {t.upper()}→{f.upper()}: {data['reverse_rate']}"
                    )

            except Exception as e:
                print(e)

        elif cmd == "help":
            print_help()

        elif cmd == "exit":
            print("Выход.")
            break

        else:
            print("Неизвестная команда. Введите help.")
