"""Tinkoff Invest MCP Server implementation."""

from datetime import datetime

from fastmcp import FastMCP


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP("Tinkoff Invest MCP Server")

    @mcp.tool()
    async def get_current_date() -> str:
        """Get current date and time.

        Returns:
            Current date and time in ISO format
        """
        return datetime.now().isoformat()

    return mcp


def main() -> None:
    """Run the MCP server."""
    mcp = create_server()
    mcp.run()


if __name__ == "__main__":
    main()
