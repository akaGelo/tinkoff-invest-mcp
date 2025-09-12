"""Интеграционные тесты для портфеля и денежных балансов.

ВАЖНО: Тесты работают с реальным sandbox API Tinkoff.
Результаты зависят от состояния песочного аккаунта.
"""

import pytest

from .conftest import parse_mcp_result


@pytest.mark.asyncio
async def test_get_cash_balance(mcp_client):
    """Тест получения позиций (денежных балансов и инструментов)."""
    result = await mcp_client.call_tool("get_cash_balance", {})
    positions_data = parse_mcp_result(result)

    # Проверяем структуру ответа CashBalanceResponse
    assert isinstance(positions_data, dict)
    assert "money" in positions_data
    assert "blocked" in positions_data

    # Проверяем что money это список MoneyValue
    money = positions_data["money"]
    assert isinstance(money, list)

    # Проверяем что blocked это список MoneyValue
    blocked = positions_data["blocked"]
    assert isinstance(blocked, list)

    # Если есть денежные средства, проверяем их структуру
    if money:
        money_value = money[0]
        expected_fields = ["currency", "units", "nano"]

        for field_name in expected_fields:
            assert field_name in money_value, f"Missing field {field_name} in money"

        # Проверяем типы данных
        assert isinstance(money_value["currency"], str)
        assert len(money_value["currency"]) == 3, "Currency should be 3-letter code"
        assert isinstance(money_value["units"], int | str)
        assert isinstance(money_value["nano"], int | str)

    # Если есть заблокированные средства, проверяем их структуру
    if blocked:
        blocked_value = blocked[0]
        expected_fields = ["currency", "units", "nano"]

        for field_name in expected_fields:
            assert field_name in blocked_value, f"Missing field {field_name} in blocked"

        # Проверяем типы данных
        assert isinstance(blocked_value["currency"], str)
        assert len(blocked_value["currency"]) == 3, "Currency should be 3-letter code"
        assert isinstance(blocked_value["units"], int | str)
        assert isinstance(blocked_value["nano"], int | str)


@pytest.mark.asyncio
async def test_get_portfolio(mcp_client):
    """Тест получения состава портфеля."""
    result = await mcp_client.call_tool("get_portfolio", {})
    portfolio_data = parse_mcp_result(result)

    # Проверяем структуру ответа PortfolioResponse
    assert isinstance(portfolio_data, dict)
    assert "positions" in portfolio_data
    assert "total_yield_percentage" in portfolio_data
    assert "account_id" in portfolio_data
    assert "total_portfolio_value" in portfolio_data
    assert "daily_yield" in portfolio_data
    assert "daily_yield_percentage" in portfolio_data

    # Проверяем что positions это список
    positions = portfolio_data["positions"]
    assert isinstance(positions, list)

    # Проверяем что yield поля являются числами
    float(portfolio_data["total_yield_percentage"])  # Может быть отрицательным
    float(portfolio_data["total_portfolio_value"])  # Общая стоимость
    float(portfolio_data["daily_yield"])  # Дневная доходность
    float(portfolio_data["daily_yield_percentage"])  # Может быть отрицательным

    # Если есть позиции, проверяем их структуру
    if positions:
        position = positions[0]
        expected_fields = [
            "instrument_id",
            "instrument_name",
            "instrument_ticker",
            "instrument_type",
            "quantity",
            "average_price",
            "current_price",
            "expected_yield",
            "currency",
            "blocked",
            "accrued_interest",
        ]

        for field_name in expected_fields:
            assert field_name in position, f"Missing field {field_name} in position"

        # Проверяем типы данных
        assert isinstance(position["instrument_id"], str)
        assert isinstance(position["instrument_name"], str)
        assert isinstance(position["instrument_ticker"], str)
        assert isinstance(position["instrument_type"], str)
        assert isinstance(position["currency"], str)
        assert isinstance(position["blocked"], bool)

        # Проверяем что количества и цены являются числами
        for amount_field in [
            "quantity",
            "average_price",
            "current_price",
            "expected_yield",
        ]:
            float(position[amount_field])  # Должно конвертироваться без ошибок


@pytest.mark.asyncio
async def test_positions_includes_blocked(mcp_client):
    """Тест что позиции включают заблокированные средства."""
    result = await mcp_client.call_tool("get_cash_balance", {})
    positions_data = parse_mcp_result(result)

    blocked = positions_data["blocked"]

    # Проверяем что заблокированные средства корректно возвращаются
    assert isinstance(blocked, list), "Blocked should be a list"

    # Если есть заблокированные средства, проверяем их структуру
    for blocked_item in blocked:
        # blocked_item должно быть MoneyValue объектом с полями currency, units, nano
        if hasattr(blocked_item, "__dict__"):
            blocked_dict = blocked_item.__dict__
        else:
            blocked_dict = blocked_item

        if isinstance(blocked_dict, dict):
            assert "currency" in blocked_dict or hasattr(blocked_item, "currency")
            assert "units" in blocked_dict or hasattr(blocked_item, "units")
            assert "nano" in blocked_dict or hasattr(blocked_item, "nano")


@pytest.mark.asyncio
async def test_positions_currency_codes(mcp_client):
    """Тест валидности кодов валют в позициях."""
    result = await mcp_client.call_tool("get_cash_balance", {})
    positions_data = parse_mcp_result(result)

    money = positions_data["money"]
    blocked = positions_data["blocked"]

    # Проверяем коды валют
    valid_currencies = {"RUB", "USD", "EUR", "CNY", "GBP", "JPY", "CHF", "TRY"}

    # Проверяем валюты в доступных средствах
    for money_item in money:
        currency = money_item["currency"]
        assert currency in valid_currencies or len(currency) == 3, (
            f"Invalid currency code: {currency}"
        )

    # Проверяем валюты в заблокированных средствах
    for blocked_item in blocked:
        currency = blocked_item["currency"]
        assert currency in valid_currencies or len(currency) == 3, (
            f"Invalid currency code: {currency}"
        )


@pytest.mark.asyncio
async def test_portfolio_and_positions_consistency(mcp_client):
    """Тест согласованности данных портфеля и позиций."""
    # Получаем портфель и позиции
    portfolio_result = await mcp_client.call_tool("get_portfolio", {})
    positions_result = await mcp_client.call_tool("get_cash_balance", {})

    portfolio_data = parse_mcp_result(portfolio_result)
    positions_data = parse_mcp_result(positions_result)

    # Оба запроса должны успешно выполниться
    assert isinstance(portfolio_data, dict)
    assert isinstance(positions_data, dict)

    # Проверяем новую структуру PortfolioResponse
    assert "positions" in portfolio_data
    assert "total_yield_percentage" in portfolio_data
    assert "account_id" in portfolio_data
    assert "total_portfolio_value" in portfolio_data
    assert "daily_yield" in portfolio_data
    assert "daily_yield_percentage" in portfolio_data

    # Проверяем упрощённую структуру CashBalanceResponse
    assert "money" in positions_data
    assert "blocked" in positions_data
