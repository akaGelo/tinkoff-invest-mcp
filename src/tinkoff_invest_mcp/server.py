"""Tinkoff Invest MCP Server implementation."""

import os
from collections.abc import Generator
from contextlib import contextmanager, suppress
from datetime import datetime
from typing import Any

import fastmcp.utilities.logging
from fastmcp import FastMCP
from tinkoff.invest import Client
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
from tinkoff.invest.schemas import CandleInterval, InstrumentIdType
from tinkoff.invest.services import Services

from .models import (
    CandlesResponse,
    CashBalanceResponse,
    CreateOrderRequest,
    Instrument,
    LastPricesResponse,
    OperationsResponse,
    Order,
    OrderBookResponse,
    OrderResponse,
    PortfolioResponse,
    TradingStatusResponse,
)


class TinkoffMCPService:
    """Централизованный MCP сервис для Tinkoff Invest API."""

    def __init__(self) -> None:
        """Инициализация сервиса."""
        self.logger = fastmcp.utilities.logging.get_logger("tinkoff-invest-mcp")
        self.logger.info("🚀 Initializing Tinkoff Invest MCP Service...")

        self.mcp = FastMCP("Tinkoff Invest MCP Server")
        self.client = None
        self._initialized = False

        # Инициализируем атрибуты с типами
        self.token: str | None = None
        self.account_id: str | None = None
        self.mode: str = "sandbox"
        self.app_name: str = "tinkoff-invest-mcp"
        self.target: str | None = None

    def initialize(self) -> None:
        """Инициализация клиента и регистрация tools."""
        if self._initialized:
            return

        self.logger.info("🔧 Setting up Tinkoff client...")

        # Загружаем конфигурацию из environment
        self.token = os.environ.get("TINKOFF_TOKEN")
        if not self.token:
            raise ValueError("Required environment variable 'TINKOFF_TOKEN' not set")

        self.account_id = os.environ.get("TINKOFF_ACCOUNT_ID")
        if not self.account_id:
            raise ValueError(
                "Required environment variable 'TINKOFF_ACCOUNT_ID' not set"
            )

        self.mode = os.environ.get("TINKOFF_MODE", "sandbox")
        self.app_name = os.environ.get("TINKOFF_APP_NAME", "tinkoff-invest-mcp")

        # Определяем API target
        self.target = (
            INVEST_GRPC_API_SANDBOX if self.mode == "sandbox" else INVEST_GRPC_API
        )

        # Не создаем клиент здесь, создаем для каждого вызова
        self.client = None

        self.logger.info("📋 Registering MCP tools...")
        self._register_tools()
        self.logger.info("✅ All tools registered successfully")

        self._initialized = True
        self.logger.info("🎯 Tinkoff Invest MCP Service ready to serve!")

    def cleanup(self) -> None:
        """Graceful shutdown клиента."""
        if self.client:
            self.logger.info("🔌 Closing Tinkoff client connection...")  # type: ignore[unreachable]
            self.client.close()
            self.client = None
            self._initialized = False

    @contextmanager
    def _client_context(self) -> Generator[Services, None, None]:
        """Контекстный менеджер для работы с клиентом."""
        if not self._initialized:
            raise RuntimeError("Service not initialized. Call initialize() first.")

        # Создаем новый клиент для каждого вызова
        if not self.token:
            raise RuntimeError("Token is not set")
        client = Client(self.token, target=self.target, app_name=self.app_name)
        try:
            with client as client_instance:
                yield client_instance
        finally:
            # Клиент автоматически закроется в with
            pass

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

        # Orders tools
        self.mcp.tool()(self.get_orders)
        self.mcp.tool()(self.create_order)
        self.mcp.tool()(self.cancel_order)

        # Instruments tools
        self.mcp.tool()(self.find_instrument)
        self.mcp.tool()(self.get_instrument_by_uid)
        self.mcp.tool()(self.get_shares)
        self.mcp.tool()(self.get_bonds)
        self.mcp.tool()(self.get_etfs)

    # Portfolio methods
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
        with self._client_context() as client:
            if not self.account_id:
                raise RuntimeError("Account ID is not set")
            response = client.operations.get_portfolio(account_id=self.account_id)
            return PortfolioResponse.from_tinkoff(response)

    def get_cash_balance(self) -> CashBalanceResponse:
        """Получить денежные балансы по валютам.

        Возвращает информацию о денежных средствах:
        - Общую сумму по каждой валюте
        - Доступную сумму для торговли
        - Заблокированную сумму в заявках
        - Общую стоимость в рублях

        Returns:
            CashBalanceResponse: Балансы по всем валютам
        """
        with self._client_context() as client:
            if not self.account_id:
                raise RuntimeError("Account ID is not set")
            response = client.operations.get_positions(account_id=self.account_id)
            return CashBalanceResponse.from_tinkoff(response)

    # Operations methods
    def get_operations(
        self,
        instrument_uid: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> OperationsResponse:
        """Получить историю операций по счету.

        Args:
            instrument_uid: UID инструмента для фильтрации (опционально)
            from_date: Дата начала периода в формате ISO 8601 (YYYY-MM-DD)
            to_date: Дата окончания периода в формате ISO 8601 (YYYY-MM-DD)

        Returns:
            OperationsResponse: Список операций за указанный период
        """
        with self._client_context() as client:
            # Преобразуем строки в datetime если нужно
            from_dt = (
                datetime.fromisoformat(from_date.replace("Z", "+00:00"))
                if isinstance(from_date, str)
                else from_date
            )
            to_dt = (
                datetime.fromisoformat(to_date.replace("Z", "+00:00"))
                if isinstance(to_date, str)
                else to_date
            )

            if not self.account_id:
                raise RuntimeError("Account ID is not set")
            response = client.operations.get_operations(
                account_id=self.account_id,
                figi=instrument_uid or "",
                from_=from_dt,
                to=to_dt,
            )
            return OperationsResponse.from_tinkoff(response)

    # Market data methods
    def get_last_prices(self, instrument_uids: list[str]) -> LastPricesResponse:
        """Получить последние цены по инструментам.

        Args:
            instrument_uids: Список UID инструментов

        Returns:
            LastPricesResponse: Последние цены по запрошенным инструментам
        """
        with self._client_context() as client:
            response = client.market_data.get_last_prices(instrument_id=instrument_uids)
            return LastPricesResponse.from_tinkoff(response)

    def get_candles(
        self,
        instrument_uid: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> CandlesResponse:
        """Получить исторические свечи по инструменту.

        Args:
            instrument_uid: UID инструмента
            interval: Интервал свечей (1min, 5min, 15min, hour, day)
            from_date: Дата начала в формате ISO 8601
            to_date: Дата окончания в формате ISO 8601

        Returns:
            CandlesResponse: Исторические данные свечей
        """
        # Преобразуем строковый интервал в enum
        interval_map = {
            "1min": CandleInterval.CANDLE_INTERVAL_1_MIN,
            "5min": CandleInterval.CANDLE_INTERVAL_5_MIN,
            "15min": CandleInterval.CANDLE_INTERVAL_15_MIN,
            "hour": CandleInterval.CANDLE_INTERVAL_HOUR,
            "day": CandleInterval.CANDLE_INTERVAL_DAY,
        }

        candle_interval = interval_map.get(interval)
        if not candle_interval:
            raise ValueError(f"Unsupported interval: {interval}")

        with self._client_context() as client:
            # Преобразуем строки в datetime если нужно
            from_dt = (
                datetime.fromisoformat(from_date.replace("Z", "+00:00"))
                if isinstance(from_date, str)
                else from_date
            )
            to_dt = (
                datetime.fromisoformat(to_date.replace("Z", "+00:00"))
                if isinstance(to_date, str)
                else to_date
            )

            response = client.market_data.get_candles(
                figi=instrument_uid,
                interval=candle_interval,
                from_=from_dt,
                to=to_dt,
            )
            return CandlesResponse.from_tinkoff(response, instrument_uid, interval)

    def get_order_book(self, instrument_uid: str, depth: int = 10) -> OrderBookResponse:
        """Получить стакан заявок по инструменту.

        Args:
            instrument_uid: UID инструмента
            depth: Глубина стакана (количество уровней цен)

        Returns:
            OrderBookResponse: Стакан заявок на покупку и продажу
        """
        with self._client_context() as client:
            response = client.market_data.get_order_book(
                figi=instrument_uid, depth=depth
            )
            return OrderBookResponse.from_tinkoff(response)

    def get_trading_status(self, instrument_uid: str) -> TradingStatusResponse:
        """Получить торговый статус инструмента.

        Args:
            instrument_uid: UID инструмента

        Returns:
            TradingStatusResponse: Информация о возможности торговли инструментом
        """
        with self._client_context() as client:
            response = client.market_data.get_trading_status(figi=instrument_uid)
            return TradingStatusResponse.from_tinkoff(response)

    # Orders methods
    def get_orders(self) -> list[Order]:
        """Получить активные заявки.

        Returns:
            list[Order]: Список активных торговых заявок
        """
        with self._client_context() as client:
            if not self.account_id:
                raise RuntimeError("Account ID is not set")
            response = client.orders.get_orders(account_id=self.account_id)
            return [Order.from_tinkoff(order) for order in response.orders]

    def create_order(
        self,
        instrument_id: str,
        quantity: int,
        direction: str,
        order_type: str,
        price: float | None = None,
    ) -> OrderResponse:
        """Создать торговую заявку.

        Args:
            instrument_id: ID инструмента (UID)
            quantity: Количество лотов
            direction: Направление (BUY/SELL)
            order_type: Тип заявки (MARKET/LIMIT)
            price: Цена (только для LIMIT заявок)

        Returns:
            OrderResponse: Информация о созданной заявке
        """
        from decimal import Decimal

        # Создаем объект заявки из параметров
        order_request = CreateOrderRequest(
            instrument_id=instrument_id,
            quantity=quantity,
            direction=direction,  # type: ignore
            order_type=order_type,  # type: ignore
            price=Decimal(str(price)) if price is not None else None,
        )

        with self._client_context() as client:
            if not self.account_id:
                raise RuntimeError("Account ID is not set")
            tinkoff_request = order_request.to_tinkoff_request(self.account_id)
            response = client.orders.post_order(**tinkoff_request)
            return OrderResponse.from_tinkoff(response)

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """Отменить торговую заявку.

        Args:
            order_id: ID заявки для отмены

        Returns:
            dict: Результат отмены заявки
        """
        with self._client_context() as client:
            if not self.account_id:
                raise RuntimeError("Account ID is not set")
            response = client.orders.cancel_order(
                account_id=self.account_id, order_id=order_id
            )
            return {"success": True, "time": response.time.isoformat()}

    # Instruments methods
    def find_instrument(self, query: str) -> list[Instrument]:
        """Найти инструменты по названию или тикеру.

        Args:
            query: Поисковый запрос (название компании, тикер)

        Returns:
            list[Instrument]: Список найденных инструментов
        """
        with self._client_context() as client:
            response = client.instruments.find_instrument(query=query)
            return [
                Instrument.from_tinkoff(instrument)
                for instrument in response.instruments
            ]

    def get_instrument_by_uid(self, uid: str) -> Instrument:
        """Получить информацию об инструменте по UID.

        Args:
            uid: Уникальный идентификатор инструмента

        Returns:
            Instrument: Подробная информация об инструменте
        """
        with self._client_context() as client:
            response = client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID, id=uid
            )
            return Instrument.from_tinkoff(response.instrument)

    def get_shares(self) -> list[Instrument]:
        """Получить список всех акций.

        Returns:
            list[Instrument]: Список акций
        """
        with self._client_context() as client:
            response = client.instruments.shares()
            return [
                Instrument.from_tinkoff_share(share) for share in response.instruments
            ]

    def get_bonds(self) -> list[Instrument]:
        """Получить список всех облигаций.

        Returns:
            list[Instrument]: Список облигаций
        """
        with self._client_context() as client:
            response = client.instruments.bonds()
            return [Instrument.from_tinkoff_bond(bond) for bond in response.instruments]

    def get_etfs(self) -> list[Instrument]:
        """Получить список всех ETF.

        Returns:
            list[Instrument]: Список ETF
        """
        with self._client_context() as client:
            response = client.instruments.etfs()
            return [Instrument.from_tinkoff_etf(etf) for etf in response.instruments]


def create_server() -> FastMCP:
    """Создать и сконфигурировать MCP сервер."""
    service = TinkoffMCPService()
    service.initialize()
    return service.mcp


def main() -> None:
    """Запустить MCP сервер."""
    mcp = create_server()
    with suppress(KeyboardInterrupt):
        mcp.run()


if __name__ == "__main__":
    main()
