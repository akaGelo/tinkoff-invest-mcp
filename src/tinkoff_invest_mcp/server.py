"""Tinkoff Invest MCP Server implementation."""

from collections.abc import Generator
from contextlib import contextmanager

import fastmcp.utilities.logging
from fastmcp import FastMCP
from tinkoff.invest import Client
from tinkoff.invest.services import Services

from .cache import InstrumentsCache
from .config import TinkoffConfig
from .constants import DEFAULT_INSTRUMENTS_LIMIT, DEFAULT_PAGINATION_OFFSET
from .models import (
    CancelOrderResponse,
    CancelStopOrderResponse,
    CandlesResponse,
    CashBalanceResponse,
    Instrument,
    LastPricesResponse,
    OperationsResponse,
    Order,
    OrderBookResponse,
    OrderResponse,
    PaginatedInstrumentsResponse,
    PortfolioResponse,
    StopOrderResponse,
    StopOrdersResponse,
    TradingSchedulesResponse,
    TradingStatusResponse,
)
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
            service.set_initialized(True)

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
            service.set_initialized(False)

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
        """Регистрация всех MCP tools."""
        # Portfolio tools
        self.mcp.tool()(self.get_portfolio)
        self.mcp.tool()(self.get_cash_balance)

        # Operations tools
        self.mcp.tool()(self.get_operations)

        # Market data tools
        self.mcp.tool()(self.get_last_prices)
        self.mcp.tool()(self.get_candles)
        self.mcp.tool()(self.get_order_book)
        self.mcp.tool()(self.get_trading_status)
        self.mcp.tool()(self.get_trading_schedules)

        # Orders tools
        self.mcp.tool()(self.get_orders)
        self.mcp.tool()(self.create_order)
        self.mcp.tool()(self.cancel_order)

        # Stop orders tools
        self.mcp.tool()(self.get_stop_orders)
        self.mcp.tool()(self.post_stop_order)
        self.mcp.tool()(self.cancel_stop_order)

        # Instruments tools
        self.mcp.tool()(self.find_instrument)
        self.mcp.tool()(self.get_instrument_by_uid)
        self.mcp.tool()(self.get_shares)
        self.mcp.tool()(self.get_bonds)
        self.mcp.tool()(self.get_etfs)

    # Делегирующие методы для Portfolio
    def get_portfolio(self) -> PortfolioResponse:
        """Получить состав портфеля.

        Возвращает все позиции в портфеле с информацией о:
        - Количестве и стоимости каждой позиции
        - Средней цене покупки и текущей цене
        - Ожидаемой доходности (P&L) по каждой позиции
        - Общей стоимости портфеля

        Returns:
            PortfolioResponse: Полная информация о портфеле
        """
        return self.portfolio_service.get_portfolio()

    def get_cash_balance(self) -> CashBalanceResponse:
        """Получить денежный баланс счета.

        Возвращает информацию о денежных средствах:
        - Доступные средства по каждой валюте
        - Заблокированные средства (в активных заявках)

        Returns:
            CashBalanceResponse: Информация о денежных средствах
        """
        return self.portfolio_service.get_cash_balance()

    # Делегирующие методы для Operations
    def get_operations(
        self,
        from_date: str,
        to_date: str | None = None,
        state: str | None = None,
        instrument_uid: str | None = None,
    ) -> OperationsResponse:
        """Получить операции по счету за период.

        Args:
            from_date: Начальная дата периода в формате ISO 8601 (например, '2024-01-01T00:00:00Z')
            to_date: Конечная дата периода. Если не указана, используется текущий момент
            state: Фильтр по статусу операции. Возможные значения:
                - OPERATION_STATE_EXECUTED - исполненные операции
                - OPERATION_STATE_CANCELED - отмененные операции
            instrument_uid: Фильтр по идентификатору инструмента

        Returns:
            OperationsResponse: Список операций за период
        """
        return self.operations_service.get_operations(
            from_date, to_date, state, instrument_uid
        )

    # Делегирующие методы для Market Data
    def get_last_prices(self, instrument_uids: list[str]) -> LastPricesResponse:
        """Получить последние цены по списку инструментов.

        Args:
            instrument_uids: Список идентификаторов инструментов

        Returns:
            LastPricesResponse: Последние цены по запрошенным инструментам
        """
        return self.market_data_service.get_last_prices(instrument_uids)

    def get_candles(
        self,
        instrument_uid: str,
        from_date: str,
        to_date: str | None = None,
        interval: str = "CANDLE_INTERVAL_1_MIN",
    ) -> CandlesResponse:
        """Получить свечи по инструменту за период.

        Args:
            instrument_uid: Идентификатор инструмента
            from_date: Начальная дата периода в формате ISO 8601
            to_date: Конечная дата периода. Если не указана, используется текущий момент
            interval: Интервал свечей:
                - CANDLE_INTERVAL_1_MIN - 1 минута
                - CANDLE_INTERVAL_5_MIN - 5 минут
                - CANDLE_INTERVAL_15_MIN - 15 минут
                - CANDLE_INTERVAL_HOUR - 1 час
                - CANDLE_INTERVAL_DAY - 1 день

        Returns:
            CandlesResponse: Свечи за запрошенный период
        """
        return self.market_data_service.get_candles(
            instrument_uid, from_date, to_date, interval
        )

    def get_order_book(self, instrument_uid: str, depth: int = 10) -> OrderBookResponse:
        """Получить стакан заявок по инструменту.

        Args:
            instrument_uid: Идентификатор инструмента
            depth: Глубина стакана (количество уровней цен с каждой стороны)

        Returns:
            OrderBookResponse: Стакан заявок с бидами и асками
        """
        return self.market_data_service.get_order_book(instrument_uid, depth)

    def get_trading_status(self, instrument_uid: str) -> TradingStatusResponse:
        """Получить торговый статус инструмента.

        Args:
            instrument_uid: Идентификатор инструмента

        Returns:
            TradingStatusResponse: Текущий торговый статус
        """
        return self.market_data_service.get_trading_status(instrument_uid)

    def get_trading_schedules(
        self,
        exchange: str = "MOEX",
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> TradingSchedulesResponse:
        """Получить расписание торгов биржи.

        Args:
            exchange: Код биржи (MOEX, MOEX_PLUS, MOEX_EVENING_WEEKEND, SPB)
            from_date: Начальная дата периода в формате ISO 8601
            to_date: Конечная дата периода

        Returns:
            TradingSchedulesResponse: Расписание торгов биржи
        """
        return self.market_data_service.get_trading_schedules(
            exchange, from_date, to_date
        )

    # Делегирующие методы для Orders
    def get_orders(self) -> list[Order]:
        """Получить список активных торговых заявок.

        Returns:
            list[Order]: Список активных заявок
        """
        return self.orders_service.get_orders()

    def create_order(
        self,
        instrument_id: str,
        quantity: int,
        direction: str,
        order_type: str,
        price: str | float | int | None = None,
    ) -> OrderResponse:
        """Создать торговую заявку.

        Args:
            instrument_id: Идентификатор инструмента
            quantity: Количество лотов
            direction: Направление заявки:
                - ORDER_DIRECTION_BUY для покупки
                - ORDER_DIRECTION_SELL для продажи
            order_type: Тип заявки:
                - ORDER_TYPE_MARKET для рыночной заявки
                - ORDER_TYPE_LIMIT для лимитной заявки
            price: Цена (только для ORDER_TYPE_LIMIT заявок). Принимает строку "15.475", число 15.475 или int 15

        Returns:
            OrderResponse: Информация о созданной заявке
        """
        return self.orders_service.create_order(
            instrument_id, quantity, direction, order_type, price
        )

    def cancel_order(self, order_id: str) -> CancelOrderResponse:
        """Отменить торговую заявку.

        Args:
            order_id: Идентификатор заявки

        Returns:
            CancelOrderResponse: Информация об отмене заявки
        """
        return self.orders_service.cancel_order(order_id)

    # Делегирующие методы для Stop Orders
    def get_stop_orders(self) -> StopOrdersResponse:
        """Получить список активных стоп-заявок.

        Returns:
            StopOrdersResponse: Список активных стоп-заявок
        """
        return self.stop_orders_service.get_stop_orders()

    def post_stop_order(
        self,
        instrument_id: str,
        quantity: int,
        direction: str,
        stop_order_type: str,
        stop_price: str | float | int,
        expiration_type: str,
        price: str | float | int | None = None,
        expire_date: str | None = None,
    ) -> StopOrderResponse:
        """Создать стоп-заявку.

        Args:
            instrument_id: Идентификатор инструмента
            quantity: Количество лотов
            direction: Направление стоп-заявки:
                - STOP_ORDER_DIRECTION_BUY для покупки
                - STOP_ORDER_DIRECTION_SELL для продажи
            stop_order_type: Тип стоп-заявки:
                - STOP_ORDER_TYPE_TAKE_PROFIT - тейк-профит
                - STOP_ORDER_TYPE_STOP_LOSS - стоп-лосс
                - STOP_ORDER_TYPE_STOP_LIMIT - стоп-лимит
            stop_price: Цена активации стоп-заявки. Принимает строку, число или int
            expiration_type: Тип истечения стоп-заявки:
                - STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL - до отмены
                - STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_DATE - до даты
            price: Цена исполнения (для STOP_LIMIT). Принимает строку, число или int
            expire_date: Дата истечения (для GOOD_TILL_DATE). Формат ISO 8601

        Returns:
            StopOrderResponse: Информация о созданной стоп-заявке
        """
        return self.stop_orders_service.post_stop_order(
            instrument_id,
            quantity,
            direction,
            stop_order_type,
            stop_price,
            expiration_type,
            price,
            expire_date,
        )

    def cancel_stop_order(self, stop_order_id: str) -> CancelStopOrderResponse:
        """Отменить стоп-заявку.

        Args:
            stop_order_id: Идентификатор стоп-заявки

        Returns:
            CancelStopOrderResponse: Информация об отмене стоп-заявки
        """
        return self.stop_orders_service.cancel_stop_order(stop_order_id)

    # Делегирующие методы для Instruments
    def find_instrument(self, query: str) -> list[Instrument]:
        """Найти инструмент по запросу.

        Args:
            query: Поисковый запрос (тикер, ISIN, FIGI или название)

        Returns:
            list[Instrument]: Список найденных инструментов
        """
        return self.instruments_service.find_instrument(query)

    def get_instrument_by_uid(self, uid: str) -> Instrument:
        """Получить инструмент по его UID.

        Args:
            uid: Уникальный идентификатор инструмента

        Returns:
            Instrument: Информация об инструменте
        """
        return self.instruments_service.get_instrument_by_uid(uid)

    def get_shares(
        self,
        limit: int = DEFAULT_INSTRUMENTS_LIMIT,
        offset: int = DEFAULT_PAGINATION_OFFSET,
    ) -> PaginatedInstrumentsResponse:
        """Получить список акций.

        Args:
            limit: Максимальное количество инструментов
            offset: Смещение для пагинации

        Returns:
            PaginatedInstrumentsResponse: Список акций с информацией о пагинации
        """
        return self.instruments_service.get_shares(limit, offset)

    def get_bonds(
        self,
        limit: int = DEFAULT_INSTRUMENTS_LIMIT,
        offset: int = DEFAULT_PAGINATION_OFFSET,
    ) -> PaginatedInstrumentsResponse:
        """Получить список облигаций.

        Args:
            limit: Максимальное количество инструментов
            offset: Смещение для пагинации

        Returns:
            PaginatedInstrumentsResponse: Список облигаций с информацией о пагинации
        """
        return self.instruments_service.get_bonds(limit, offset)

    def get_etfs(
        self,
        limit: int = DEFAULT_INSTRUMENTS_LIMIT,
        offset: int = DEFAULT_PAGINATION_OFFSET,
    ) -> PaginatedInstrumentsResponse:
        """Получить список ETF.

        Args:
            limit: Максимальное количество инструментов
            offset: Смещение для пагинации

        Returns:
            PaginatedInstrumentsResponse: Список ETF с информацией о пагинации
        """
        return self.instruments_service.get_etfs(limit, offset)


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
