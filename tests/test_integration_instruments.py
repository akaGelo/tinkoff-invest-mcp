"""Интеграционные тесты для инструментов."""

import pytest

from .conftest import parse_mcp_result


@pytest.mark.asyncio
async def test_get_shares(mcp_client):
    """Тест получения списка акций."""
    result = await mcp_client.call_tool("get_shares", {})
    shares_data = parse_mcp_result(result)

    assert isinstance(shares_data, list)
    assert len(shares_data) > 0

    # Проверяем структуру первой акции
    share = shares_data[0]
    expected_fields = [
        "uid",
        "name",
        "ticker",
        "currency",
        "instrument_type",
    ]

    for field_name in expected_fields:
        assert field_name in share, f"Missing field {field_name} in share"

    assert share["instrument_type"] == "share"


@pytest.mark.asyncio
async def test_get_all_instrument_types(mcp_client):
    """Тест получения всех типов инструментов."""
    # Тестируем что все методы работают
    instruments_methods = [
        ("get_bonds", "bond"),
        ("get_etfs", "etf"),
    ]

    for method_name, expected_type in instruments_methods:
        result = await mcp_client.call_tool(method_name, {})
        data = parse_mcp_result(result)

        assert isinstance(data, list), f"{method_name} должен возвращать список"

        if data:  # Проверяем только если есть данные
            first_item = data[0]
            assert "uid" in first_item, f"{method_name}: отсутствует uid"
            assert first_item["instrument_type"] == expected_type


@pytest.mark.asyncio
async def test_find_instrument(mcp_client):
    """Тест поиска инструментов."""
    result = await mcp_client.call_tool("find_instrument", {"query": "SBER"})
    instruments_data = parse_mcp_result(result)

    assert isinstance(instruments_data, list)
    # Поиск может не найти результатов в песочнице - это нормально


@pytest.mark.asyncio
async def test_get_trading_status(mcp_client, test_instrument):
    """Тест получения торгового статуса инструмента."""
    instrument_uid = test_instrument["uid"]

    result = await mcp_client.call_tool(
        "get_trading_status", {"instrument_id": instrument_uid}
    )
    status_data = parse_mcp_result(result)

    assert isinstance(status_data, dict)
    assert "instrument_id" in status_data
    assert "trading_status" in status_data
    assert "api_trade_available" in status_data
    assert status_data["instrument_id"] == instrument_uid


@pytest.mark.asyncio
async def test_test_instrument_fixture(test_instrument):
    """Тест проверки фикстуры тестового инструмента."""
    assert isinstance(test_instrument, dict)
    assert test_instrument["uid"] == "e9139ddd-bf3c-4d03-a94f-ffdf7234c6be"
    assert test_instrument["instrument_type"] == "share"
    assert test_instrument["api_trade_available_flag"] is True
