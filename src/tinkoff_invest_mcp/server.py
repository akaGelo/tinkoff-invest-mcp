"""Tinkoff Invest MCP Server implementation."""

from fastmcp import FastMCP

from .tools.registry import register_all_tools


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP("Tinkoff Invest MCP Server")

    # Регистрируем все tools централизованно
    register_all_tools(mcp)

    return mcp


def main() -> None:
    """Run the MCP server."""
    mcp = create_server()
    mcp.run()


if __name__ == "__main__":
    main()
