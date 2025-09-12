"""Интеграционные тесты для ордеров.

ВАЖНО: В песочнице Tinkoff все инструменты имеют статус
SECURITY_TRADING_STATUS_NOT_AVAILABLE_FOR_TRADING (вне торгового времени
или из-за ограничений песочницы). Создание ордеров вызывает ошибку 30079.

Тесты проверяют правильную обработку ошибок API и структуру ответов.
Для полноценного тестирования торговых алгоритмов используйте:
- Торговое время (если доступно в песочнице)
- Моки/заглушки для имитации успешных ответов
- Продакшен с минимальными суммами
"""

import pytest

from .conftest import parse_mcp_result


@pytest.mark.asyncio
async def test_get_orders(mcp_client):
    """Тест получения списка ордеров."""
    result = await mcp_client.call_tool("get_orders", {})
    orders_data = parse_mcp_result(result)

    assert isinstance(orders_data, list)
    # В песочнице может не быть ордеров - это нормально


@pytest.mark.asyncio
async def test_create_limit_order_error_handling(mcp_client, test_instrument):
    """Тест обработки ошибок при создании лимитного ордера."""
    instrument_uid = test_instrument["uid"]

    # В песочнице инструмент недоступен для торговли - ожидаем ошибку
    with pytest.raises(Exception) as exc_info:
        await mcp_client.call_tool(
            "create_order",
            {
                "instrument_id": instrument_uid,
                "quantity": 1,
                "direction": "BUY",
                "order_type": "LIMIT",
                "price": 100.0,
            },
        )

    # В песочнице может быть разные ошибки - проверяем общие случаи
    error_msg = str(exc_info.value)
    # Может быть ошибка торговли (30079) или другие sandbox ошибки
    is_trading_error = (
        "30079" in error_msg or "not available for trading" in error_msg.lower()
    )
    is_other_expected_error = any(
        err in error_msg.lower()
        for err in ["instrument not found", "validation error", "invalid"]
    )
    assert is_trading_error or is_other_expected_error, f"Unexpected error: {error_msg}"


@pytest.mark.asyncio
async def test_create_market_order_error_handling(mcp_client, test_instrument):
    """Тест обработки ошибок при создании рыночного ордера."""
    instrument_uid = test_instrument["uid"]

    # В песочнице инструмент недоступен для торговли - ожидаем ошибку
    with pytest.raises(Exception) as exc_info:
        await mcp_client.call_tool(
            "create_order",
            {
                "instrument_id": instrument_uid,
                "quantity": 1,
                "direction": "BUY",
                "order_type": "MARKET",
            },
        )

    # В песочнице может быть разные ошибки - проверяем общие случаи
    error_msg = str(exc_info.value)
    # Может быть ошибка торговли (30079) или другие sandbox ошибки
    is_trading_error = (
        "30079" in error_msg or "not available for trading" in error_msg.lower()
    )
    is_other_expected_error = any(
        err in error_msg.lower()
        for err in ["instrument not found", "validation error", "invalid"]
    )
    assert is_trading_error or is_other_expected_error, f"Unexpected error: {error_msg}"


@pytest.mark.asyncio
async def test_get_orders_structure(mcp_client):
    """Тест структуры ответа для получения ордеров."""
    orders_result = await mcp_client.call_tool("get_orders", {})
    orders = parse_mcp_result(orders_result)

    assert isinstance(orders, list)

    # Если есть заявки, проверяем структуру комиссий
    if orders:
        first_order = orders[0]
        # Проверяем наличие всех полей комиссий
        assert "initial_commission" in first_order, "Отсутствует initial_commission"
        assert "executed_commission" in first_order, "Отсутствует executed_commission"
        assert "service_commission" in first_order, "Отсутствует service_commission"
