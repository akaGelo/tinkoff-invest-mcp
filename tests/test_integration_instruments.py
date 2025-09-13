"""Интеграционные тесты для инструментов."""

import pytest

from .conftest import parse_mcp_result


@pytest.mark.asyncio
async def test_get_shares(mcp_client):
    """Тест получения списка акций с пагинацией."""
    result = await mcp_client.call_tool("get_shares", {})
    shares_data = parse_mcp_result(result)

    assert isinstance(shares_data, dict), (
        "get_shares должен возвращать dict с пагинацией"
    )
    assert "instruments" in shares_data
    assert "total" in shares_data
    assert "limit" in shares_data
    assert "offset" in shares_data
    assert "has_more" in shares_data

    assert isinstance(shares_data["instruments"], list)
    assert len(shares_data["instruments"]) > 0

    # Проверяем структуру первой акции
    share = shares_data["instruments"][0]
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
    # Тестируем bonds с пагинацией
    result = await mcp_client.call_tool("get_bonds", {})
    bonds_data = parse_mcp_result(result)

    assert isinstance(bonds_data, dict), "get_bonds должен возвращать dict с пагинацией"
    assert "instruments" in bonds_data
    assert "total" in bonds_data
    assert "limit" in bonds_data
    assert "offset" in bonds_data
    assert "has_more" in bonds_data

    assert isinstance(bonds_data["instruments"], list)
    assert bonds_data["total"] > 0
    assert bonds_data["limit"] == 10  # default limit
    assert bonds_data["offset"] == 0  # default offset

    if bonds_data["instruments"]:
        first_bond = bonds_data["instruments"][0]
        assert "uid" in first_bond, "get_bonds: отсутствует uid"
        assert first_bond["instrument_type"] == "bond"
        # Проверяем что поле maturity_date присутствует (может быть None)
        assert "maturity_date" in first_bond, "get_bonds: отсутствует maturity_date"
        # Проверяем что поля НКД и купонов присутствуют (могут быть None)
        assert "aci_value" in first_bond, "get_bonds: отсутствует aci_value"
        assert "coupon_quantity_per_year" in first_bond, (
            "get_bonds: отсутствует coupon_quantity_per_year"
        )
        assert "floating_coupon_flag" in first_bond, (
            "get_bonds: отсутствует floating_coupon_flag"
        )

    # Тестируем ETFs с пагинацией
    result = await mcp_client.call_tool("get_etfs", {})
    etfs_data = parse_mcp_result(result)

    assert isinstance(etfs_data, dict), "get_etfs должен возвращать dict с пагинацией"
    assert "instruments" in etfs_data
    assert "total" in etfs_data
    assert "limit" in etfs_data
    assert "offset" in etfs_data
    assert "has_more" in etfs_data

    assert isinstance(etfs_data["instruments"], list)

    if etfs_data["instruments"]:  # Проверяем только если есть данные
        first_item = etfs_data["instruments"][0]
        assert "uid" in first_item, "get_etfs: отсутствует uid"
        assert first_item["instrument_type"] == "etf"


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

    # В песочнице инструмент может быть недоступен, это ожидаемая ситуация
    try:
        result = await mcp_client.call_tool(
            "get_trading_status", {"instrument_uid": instrument_uid}
        )
        status_data = parse_mcp_result(result)

        assert isinstance(status_data, dict)
        assert "instrument_id" in status_data
        assert "trading_status" in status_data
        assert status_data["instrument_id"] == instrument_uid
    except Exception as e:
        # В песочнице инструмент может не существовать - это нормально
        error_msg = str(e)
        assert "not found" in error_msg.lower() or "50002" in error_msg
        print(f"Instrument not found in sandbox (expected): {error_msg[:100]}")
        # Тест считается пройденным, так как API работает корректно


@pytest.mark.asyncio
async def test_get_bonds_pagination(mcp_client):
    """Тест пагинации для bonds."""
    # Запрашиваем первые 10 облигаций
    result = await mcp_client.call_tool("get_bonds", {"limit": 10, "offset": 0})
    page1_data = parse_mcp_result(result)

    assert isinstance(page1_data, dict)
    assert len(page1_data["instruments"]) <= 10
    assert page1_data["limit"] == 10
    assert page1_data["offset"] == 0

    if page1_data["has_more"]:
        # Запрашиваем следующие 10 облигаций
        result2 = await mcp_client.call_tool("get_bonds", {"limit": 10, "offset": 10})
        page2_data = parse_mcp_result(result2)

        assert isinstance(page2_data, dict)
        assert len(page2_data["instruments"]) <= 10
        assert page2_data["limit"] == 10
        assert page2_data["offset"] == 10
        assert (
            page2_data["total"] == page1_data["total"]
        )  # Total должно быть одинаковое

        # Проверяем что инструменты разные
        page1_uids = {bond["uid"] for bond in page1_data["instruments"]}
        page2_uids = {bond["uid"] for bond in page2_data["instruments"]}
        assert page1_uids.isdisjoint(page2_uids), (
            "Страницы должны содержать разные инструменты"
        )


@pytest.mark.asyncio
async def test_test_instrument_fixture(test_instrument):
    """Тест проверки фикстуры тестового инструмента."""
    assert isinstance(test_instrument, dict)
    assert test_instrument["uid"] == "e9139ddd-bf3c-4d03-a94f-ffdf7234c6be"
    assert test_instrument["instrument_type"] == "share"
    assert test_instrument["api_trade_available_flag"] is True
