"""CLI для создания и управления sandbox аккаунтами Tinkoff Invest."""

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from tinkoff.invest import AsyncClient, MoneyValue
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX


def load_env_files() -> None:
    """Загрузить .env.test файл."""
    env_test = Path(".env.test")
    if env_test.exists():
        print(f"📄 Загружаю {env_test}")
        load_dotenv(env_test, override=True)


def get_env_var(name: str, required: bool = True) -> str | None:
    """Получить переменную окружения."""
    value = os.environ.get(name)
    if required and not value:
        raise ValueError(f"❌ Не найдена обязательная переменная окружения: {name}")
    return value


def money_value_to_float(money_value: MoneyValue) -> float:
    """Конвертировать MoneyValue в float."""
    return money_value.units + money_value.nano / 1_000_000_000


async def list_accounts_with_balances(client: AsyncClient) -> None:
    """Показать список аккаунтов с балансами."""
    print("📋 Аккаунты и балансы:")
    try:
        accounts_response = await client.users.get_accounts()
        if not accounts_response.accounts:
            print("   Нет аккаунтов")
            return

        for account in accounts_response.accounts:
            print(f"   💳 {account.id}")
            try:
                portfolio = await client.operations.get_portfolio(account_id=account.id)
                total_amount = portfolio.total_amount_portfolio
                if total_amount:
                    amount = money_value_to_float(total_amount)
                    print(f"      💰 {amount:.2f} {total_amount.currency.upper()}")
                else:
                    print("      💰 Баланс недоступен")
            except Exception as e:
                print(f"      ❌ Ошибка баланса: {e}")

    except Exception as e:
        print(f"   ❌ Ошибка получения аккаунтов: {e}")


async def create_sandbox_account(client: AsyncClient) -> str:
    """Создать новый sandbox аккаунт."""
    print("\n🏦 Создаю новый sandbox аккаунт...")
    response = await client.sandbox.open_sandbox_account()
    account_id = response.account_id
    print(f"✅ Аккаунт создан: {account_id}")

    print("💰 Пополняю аккаунт на 100,000 RUB...")
    await client.sandbox.sandbox_pay_in(
        account_id=account_id,
        amount=MoneyValue(currency="rub", units=100_000, nano=0),
    )
    print("✅ Аккаунт пополнен на 100,000 RUB")

    return account_id


def print_account_info(account_id: str) -> None:
    """Показать информацию о созданном аккаунте."""
    print("\n" + "=" * 50)
    print("🎉 Sandbox аккаунт готов к использованию!")
    print("=" * 50)
    print(f"📝 Account ID: {account_id}")
    print("=" * 50)


async def main() -> None:
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description="Управление sandbox аккаунтами Tinkoff Invest"
    )
    parser.add_argument(
        "--create", "-c", action="store_true", help="Создать новый аккаунт"
    )
    args = parser.parse_args()

    try:
        print("🔧 Tinkoff Invest Sandbox Manager")
        print("=" * 35)

        load_env_files()
        token = get_env_var("TINKOFF_TOKEN", required=False)
        if not token:
            print("❌ Ошибка: не найден TINKOFF_TOKEN в .env.test")
            return

        print(f"🔑 Токен найден: {token[:8]}***")

        async with AsyncClient(token, target=INVEST_GRPC_API_SANDBOX) as client:
            await list_accounts_with_balances(client)

            if args.create:
                account_id = await create_sandbox_account(client)
                print_account_info(account_id)

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def cli_main() -> None:
    """Entry point для CLI команды."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
