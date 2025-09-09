"""Централизованная регистрация всех MCP tools."""

from fastmcp import FastMCP

from .instruments import register_instruments_tools
from .orders import register_orders_tools


def register_all_tools(mcp: FastMCP) -> None:
    """Регистрация всех MCP tools в сервере.

    Args:
        mcp: FastMCP сервер для регистрации tools
    """
    # Регистрируем Orders tools
    register_orders_tools(mcp)

    # Регистрируем Instruments tools
    register_instruments_tools(mcp)

    # Здесь будут регистрироваться другие tools:
    # register_portfolio_tools(mcp)
    # register_market_tools(mcp)
