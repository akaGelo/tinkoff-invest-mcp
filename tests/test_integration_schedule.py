"""Интеграционные тесты для расписания торгов."""

from datetime import datetime, timedelta

import pytest

from .conftest import parse_mcp_result


@pytest.mark.asyncio
async def test_get_trading_schedules_all_exchanges(mcp_client):
    """Тест получения расписания торгов для всех бирж."""
    # Получаем расписание на неделю вперед (начинаем с завтрашнего дня)
    from_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")

    result = await mcp_client.call_tool(
        "get_trading_schedules",
        {
            "from_date": from_date,
            "to_date": to_date,
        },
    )
    schedule_data = parse_mcp_result(result)

    assert isinstance(schedule_data, dict), (
        "get_trading_schedules должен возвращать dict"
    )
    assert "schedules" in schedule_data
    assert isinstance(schedule_data["schedules"], list)


@pytest.mark.asyncio
async def test_get_trading_schedules_moex(mcp_client):
    """Тест получения расписания торгов для Московской биржи."""
    # Получаем расписание на неделю вперед для MOEX (начинаем с завтрашнего дня)
    from_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")

    result = await mcp_client.call_tool(
        "get_trading_schedules",
        {
            "exchange": "MOEX",
            "from_date": from_date,
            "to_date": to_date,
        },
    )
    schedule_data = parse_mcp_result(result)

    assert isinstance(schedule_data, dict)
    assert "schedules" in schedule_data
    assert isinstance(schedule_data["schedules"], list)

    # Если есть данные, проверяем структуру
    if schedule_data["schedules"]:
        first_schedule = schedule_data["schedules"][0]
        assert "exchange" in first_schedule
        assert "days" in first_schedule
        assert isinstance(first_schedule["days"], list)

        # Проверяем структуру торгового дня
        if first_schedule["days"]:
            first_day = first_schedule["days"][0]
            expected_fields = [
                "date",
                "is_trading_day",
                "start_time",
                "end_time",
            ]

            for field_name in expected_fields:
                assert field_name in first_day, (
                    f"Missing field {field_name} in trading day"
                )


@pytest.mark.asyncio
async def test_get_trading_schedules_structure(mcp_client):
    """Тест структуры ответа расписания торгов."""
    # Получаем расписание на завтра
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    result = await mcp_client.call_tool(
        "get_trading_schedules",
        {
            "from_date": tomorrow,
            "to_date": tomorrow,
        },
    )
    schedule_data = parse_mcp_result(result)

    assert isinstance(schedule_data, dict)
    assert "schedules" in schedule_data

    # Если есть расписания, проверяем подробную структуру
    if schedule_data["schedules"]:
        for schedule in schedule_data["schedules"]:
            assert isinstance(schedule["exchange"], str)
            assert isinstance(schedule["days"], list)

            for day in schedule["days"]:
                # Обязательные поля
                assert isinstance(day["date"], str)
                assert isinstance(day["is_trading_day"], bool)

                # Опциональные поля времени могут быть None или строками
                optional_time_fields = [
                    "start_time",
                    "end_time",
                    "premarket_start_time",
                    "premarket_end_time",
                    "evening_start_time",
                    "evening_end_time",
                    "opening_auction_start_time",
                    "opening_auction_end_time",
                    "closing_auction_start_time",
                    "closing_auction_end_time",
                ]

                for field in optional_time_fields:
                    if field in day:
                        assert day[field] is None or isinstance(day[field], str)


@pytest.mark.asyncio
async def test_get_trading_schedules_without_dates(mcp_client):
    """Тест получения расписания торгов без указания дат."""
    result = await mcp_client.call_tool("get_trading_schedules", {})
    schedule_data = parse_mcp_result(result)

    assert isinstance(schedule_data, dict)
    assert "schedules" in schedule_data
    # Без дат может ничего не возвращать - это нормально
    assert isinstance(schedule_data["schedules"], list)
