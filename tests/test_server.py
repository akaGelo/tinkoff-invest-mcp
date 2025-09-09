"""Tests for Tinkoff Invest MCP Server."""

from datetime import datetime

import pytest
from fastmcp import Client

from tinkoff_invest_mcp.server import create_server


@pytest.mark.asyncio
async def test_get_current_date_tool() -> None:
    """Test get_current_date tool returns valid ISO format datetime."""
    mcp = create_server()

    async with Client(mcp) as client:
        result = await client.call_tool("get_current_date", {})

        # Проверяем что результат не пустой
        assert result is not None

        # FastMCP возвращает CallToolResult, получаем данные из него
        date_str = result.data if hasattr(result, "data") else str(result)

        assert isinstance(date_str, str)

        # Проверяем что можно распарсить как datetime
        parsed_date = datetime.fromisoformat(date_str)
        assert isinstance(parsed_date, datetime)

        # Проверяем что дата близка к текущей (в пределах минуты)
        now = datetime.now()
        diff = abs((now - parsed_date).total_seconds())
        assert diff < 60, f"Date difference too large: {diff} seconds"


@pytest.mark.asyncio
async def test_server_initialization() -> None:
    """Test that server initializes correctly."""
    mcp = create_server()

    async with Client(mcp) as client:
        # Проверяем что клиент успешно подключился
        assert client is not None

        # Получаем список доступных tools
        tools = await client.list_tools()

        # Проверяем что наш tool зарегистрирован
        tool_names = [tool.name for tool in tools]
        assert "get_current_date" in tool_names


@pytest.mark.asyncio
async def test_tool_metadata() -> None:
    """Test that tool has correct metadata."""
    mcp = create_server()

    async with Client(mcp) as client:
        tools = await client.list_tools()

        # Находим наш tool
        date_tool = next((t for t in tools if t.name == "get_current_date"), None)

        assert date_tool is not None
        assert date_tool.description is not None
        assert "date" in date_tool.description.lower()
        assert "time" in date_tool.description.lower()
