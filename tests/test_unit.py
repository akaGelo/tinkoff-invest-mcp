"""Служебные тесты MCP сервера."""

import os

import pytest
from fastmcp import Client

from tinkoff_invest_mcp.server import create_server


def test_env_validation():
    """Проверка валидации переменных окружения."""
    from tinkoff_invest_mcp.client import create_account_client

    original_token = os.environ.get("TINKOFF_TOKEN")
    if original_token:
        del os.environ["TINKOFF_TOKEN"]

    try:
        with pytest.raises(
            ValueError, match="Required environment variable 'TINKOFF_TOKEN' not set"
        ):
            create_account_client()
    finally:
        if original_token:
            os.environ["TINKOFF_TOKEN"] = original_token


@pytest.mark.asyncio
async def test_server_initialization():
    """Проверка инициализации сервера."""
    required_vars = ["TINKOFF_TOKEN", "TINKOFF_ACCOUNT_ID"]
    for var in required_vars:
        assert os.environ.get(var), f"Required env var {var} not set"

    mcp = create_server()
    async with Client(mcp) as client:
        assert client is not None


@pytest.mark.asyncio
async def test_mcp_tool_registration():
    """Проверка регистрации MCP инструментов."""
    mcp = create_server()

    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_tools = ["get_orders", "create_order"]
        for tool_name in expected_tools:
            assert tool_name in tool_names

        # Проверяем get_orders tool
        orders_tool = next((t for t in tools if t.name == "get_orders"), None)
        assert orders_tool is not None
        assert orders_tool.description is not None
        assert "orders" in orders_tool.description.lower()

        # Проверяем create_order tool
        create_order_tool = next((t for t in tools if t.name == "create_order"), None)
        assert create_order_tool is not None
        assert create_order_tool.description is not None
        assert "create" in create_order_tool.description.lower()
