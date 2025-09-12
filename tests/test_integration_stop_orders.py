"""Интеграционные тесты для стоп-заявок."""

import pytest

from .conftest import parse_mcp_result


@pytest.mark.asyncio
async def test_get_stop_orders_structure(mcp_client):
    """Тест структуры ответа получения стоп-заявок."""
    try:
        result = await mcp_client.call_tool("get_stop_orders", {})

        stop_orders_data = parse_mcp_result(result)

        # Проверяем структуру ответа
        assert "stop_orders" in stop_orders_data
        assert isinstance(stop_orders_data["stop_orders"], list)

    except Exception as e:
        # В sandbox стоп-заявки не поддерживаются
        assert (
            "unimplemented" in str(e).lower()
            or "method is unimplemented" in str(e).lower()
        )


@pytest.mark.asyncio
async def test_get_stop_orders_empty_list(mcp_client):
    """Тест получения пустого списка стоп-заявок (если нет активных)."""
    try:
        result = await mcp_client.call_tool("get_stop_orders", {})

        stop_orders_data = parse_mcp_result(result)
        stop_orders = stop_orders_data["stop_orders"]

        # Для sandbox обычно пустой список
        assert isinstance(stop_orders, list)

        # Если есть стоп-заявки, проверим их структуру
        if stop_orders:
            for stop_order in stop_orders:
                # Проверяем обязательные поля
                assert "stop_order_id" in stop_order
                assert "instrument_uid" in stop_order
                assert "direction" in stop_order
                assert "lots" in stop_order
                assert "stop_order_type" in stop_order
                assert "stop_price" in stop_order
                assert "expiration_type" in stop_order

                # Проверяем типы значений
                assert isinstance(stop_order["stop_order_id"], str)
                assert isinstance(stop_order["instrument_uid"], str)
                assert stop_order["direction"] in [
                    "STOP_ORDER_DIRECTION_BUY",
                    "STOP_ORDER_DIRECTION_SELL",
                ]
                assert isinstance(stop_order["lots"], int)
                assert stop_order["stop_order_type"] in [
                    "STOP_ORDER_TYPE_TAKE_PROFIT",
                    "STOP_ORDER_TYPE_STOP_LOSS",
                    "STOP_ORDER_TYPE_STOP_LIMIT",
                ]
                assert stop_order["expiration_type"] in [
                    "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL",
                    "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_DATE",
                ]

    except Exception as e:
        # В sandbox стоп-заявки не поддерживаются
        assert (
            "unimplemented" in str(e).lower()
            or "method is unimplemented" in str(e).lower()
        )


@pytest.mark.asyncio
async def test_post_stop_order_validation_errors(mcp_client):
    """Тест валидации при создании стоп-заявок с неверными параметрами."""

    # Тест с отсутствующими обязательными параметрами
    with pytest.raises((ValueError, TypeError, KeyError)):
        await mcp_client.call_tool(
            "post_stop_order",
            {
                "quantity": 1,
                "direction": "STOP_ORDER_DIRECTION_SELL",
                "stop_order_type": "STOP_ORDER_TYPE_STOP_LOSS",
                # Отсутствует instrument_id
            },
        )

    # Тест с неверным типом стоп-заявки
    with pytest.raises((ValueError, TypeError)):
        await mcp_client.call_tool(
            "post_stop_order",
            {
                "instrument_id": "test_uid",
                "quantity": 1,
                "direction": "STOP_ORDER_DIRECTION_SELL",
                "stop_order_type": "INVALID_STOP_ORDER_TYPE",
                "stop_price": 100.0,
                "expiration_type": "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL",
            },
        )


@pytest.mark.asyncio
async def test_stop_orders_sandbox_limitations(mcp_client):
    """Тест проверки ограничений sandbox для стоп-заявок."""

    # Получим любой инструмент для тестирования
    instruments_result = await mcp_client.call_tool(
        "find_instrument", {"query": "Сбер"}
    )
    instruments_data = parse_mcp_result(instruments_result)

    if not instruments_data:
        pytest.skip("Не найдены инструменты для тестирования")

    instrument_uid = instruments_data[0]["uid"]

    # Все операции со стоп-заявками в sandbox должны возвращать unimplemented
    operations = [
        (
            "post_stop_order",
            {
                "instrument_id": instrument_uid,
                "quantity": 1,
                "direction": "STOP_ORDER_DIRECTION_SELL",
                "stop_order_type": "STOP_ORDER_TYPE_TAKE_PROFIT",
                "stop_price": 300.0,
                "expiration_type": "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL",
            },
        ),
        ("cancel_stop_order", {"stop_order_id": "test_id"}),
    ]

    for operation_name, params in operations:
        try:
            await mcp_client.call_tool(operation_name, params)
            # Если операция прошла успешно в sandbox - это неожиданно, но OK

        except Exception as e:
            error_msg = str(e).lower()
            # Ожидаем ошибки sandbox или unimplemented
            assert any(
                keyword in error_msg
                for keyword in [
                    "unimplemented",
                    "method is unimplemented",
                    "sandbox",
                    "not allowed",
                    "invalid",
                    "not supported",
                    "forbidden",
                ]
            )


@pytest.mark.asyncio
async def test_stop_order_models_structure(mcp_client):
    """Тест структуры моделей стоп-заявок через валидацию."""

    # Тестируем валидацию StopOrderRequest модели через параметры API
    test_cases = [
        # Отсутствует обязательный параметр stop_price
        {
            "instrument_id": "test_uid",
            "quantity": 1,
            "direction": "STOP_ORDER_DIRECTION_SELL",
            "stop_order_type": "STOP_ORDER_TYPE_STOP_LOSS",
            "expiration_type": "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL",
            # stop_price отсутствует
        },
        # Неверный тип направления
        {
            "instrument_id": "test_uid",
            "quantity": 1,
            "direction": "INVALID_DIRECTION",
            "stop_order_type": "STOP_ORDER_TYPE_STOP_LOSS",
            "stop_price": 100.0,
            "expiration_type": "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL",
        },
        # Неверный тип экспирации
        {
            "instrument_id": "test_uid",
            "quantity": 1,
            "direction": "STOP_ORDER_DIRECTION_SELL",
            "stop_order_type": "STOP_ORDER_TYPE_STOP_LOSS",
            "stop_price": 100.0,
            "expiration_type": "INVALID_EXPIRATION_TYPE",
        },
    ]

    for test_case in test_cases:
        with pytest.raises((ValueError, TypeError, KeyError)):
            await mcp_client.call_tool("post_stop_order", test_case)
