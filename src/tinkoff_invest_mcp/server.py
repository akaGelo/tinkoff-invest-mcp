"""Tinkoff Invest MCP Server implementation."""

from collections.abc import Generator
from contextlib import contextmanager

import fastmcp.utilities.logging
from fastmcp import FastMCP
from tinkoff.invest import Client
from tinkoff.invest.services import Services

from .cache import InstrumentsCache
from .config import TinkoffConfig
from .services import (
    InstrumentsService,
    MarketDataService,
    OperationsService,
    OrdersService,
    PortfolioService,
    StopOrdersService,
)


class TinkoffMCPService:
    """Централизованный MCP сервис для Tinkoff Invest API."""

    def __init__(self, config: TinkoffConfig | None = None) -> None:
        """Инициализация сервиса.

        Args:
            config: Конфигурация для сервиса. Если None, загружается из env
        """
        self.logger = fastmcp.utilities.logging.get_logger("tinkoff-invest-mcp")
        self.logger.info("🚀 Initializing Tinkoff Invest MCP Service...")

        # Загружаем конфигурацию
        self.config = config or TinkoffConfig.from_env()

        # Логируем конфигурацию без чувствительных данных
        self.logger.info(f"📊 Configuration: {self.config.mask_sensitive_data()}")

        self.mcp = FastMCP("Tinkoff Invest MCP Server")
        self._initialized = False

        # Инициализируем кэш инструментов
        self._cache = InstrumentsCache(self._client_context)

        # Инициализируем сервисы
        self.portfolio_service = PortfolioService(self.config, self._cache)
        self.operations_service = OperationsService(self.config, self._cache)
        self.market_data_service = MarketDataService(self.config, self._cache)
        self.orders_service = OrdersService(self.config, self._cache)
        self.stop_orders_service = StopOrdersService(self.config, self._cache)
        self.instruments_service = InstrumentsService(self.config, self._cache)

    def initialize(self) -> None:
        """Инициализация клиента и регистрация tools."""
        if self._initialized:
            return

        self.logger.info("🔧 Setting up Tinkoff client...")

        # Устанавливаем флаг инициализации для всех сервисов
        for service in [
            self.portfolio_service,
            self.operations_service,
            self.market_data_service,
            self.orders_service,
            self.stop_orders_service,
            self.instruments_service,
        ]:
            service._set_initialized(True)

        # Конфигурация уже загружена и валидирована в __init__
        self.logger.info("📋 Registering MCP tools...")
        self._register_tools()
        self.logger.info("✅ All tools registered successfully")

        self._initialized = True
        self.logger.info("🎯 Tinkoff Invest MCP Service ready to serve!")

    def cleanup(self) -> None:
        """Graceful shutdown клиента."""
        self.logger.info("🔌 Closing Tinkoff client connection...")
        self._initialized = False

        # Устанавливаем флаг для всех сервисов
        for service in [
            self.portfolio_service,
            self.operations_service,
            self.market_data_service,
            self.orders_service,
            self.stop_orders_service,
            self.instruments_service,
        ]:
            service._set_initialized(False)

    @contextmanager
    def _client_context(self) -> Generator[Services, None, None]:
        """Контекстный менеджер для работы с клиентом."""
        if not self._initialized:
            raise RuntimeError("Service not initialized. Call initialize() first.")

        # Создаем новый клиент для каждого вызова
        client = Client(
            self.config.token, target=self.config.target, app_name=self.config.app_name
        )
        with client as client_instance:
            yield client_instance

    def _register_tools(self) -> None:
        """Регистрация всех MCP tools из сервисов."""
        services = [
            self.portfolio_service,
            self.operations_service,
            self.market_data_service,
            self.orders_service,
            self.stop_orders_service,
            self.instruments_service,
        ]

        # Автоматически регистрируем все публичные методы сервисов как MCP tools
        for service in services:
            service_tools = service.get_mcp_tools()
            for tool_name, tool_method in service_tools.items():
                self.mcp.tool()(tool_method)
                self.logger.debug(
                    f"Registered tool: {tool_name} from {service.__class__.__name__}"
                )


def create_server() -> FastMCP:
    """Создать и сконфигурировать MCP сервер."""
    service = TinkoffMCPService()
    service.initialize()
    return service.mcp


def main() -> None:
    """Entry point для запуска MCP сервера."""
    import asyncio

    server = create_server()
    asyncio.run(server.run())  # type: ignore[func-returns-value]


if __name__ == "__main__":
    main()
