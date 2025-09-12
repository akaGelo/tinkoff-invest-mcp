"""Tinkoff Invest MCP Server implementation."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from datetime import datetime
from decimal import Decimal

import fastmcp.utilities.logging
from fastmcp import FastMCP
from tinkoff.invest import Client
from tinkoff.invest.schemas import InstrumentIdType
from tinkoff.invest.services import Services

from .cache import InstrumentsCache
from .config import TinkoffConfig
from .constants import DEFAULT_INSTRUMENTS_LIMIT, DEFAULT_PAGINATION_OFFSET
from .models import (
    CancelOrderResponse,
    CancelStopOrderResponse,
    CandlesResponse,
    CashBalanceResponse,
    CreateOrderRequest,
    Instrument,
    LastPricesResponse,
    OperationsResponse,
    Order,
    OrderBookResponse,
    OrderResponse,
    PaginatedInstrumentsResponse,
    PortfolioResponse,
    StopOrderRequest,
    StopOrderResponse,
    StopOrdersResponse,
    TradingSchedulesResponse,
    TradingStatusResponse,
)
from .models.common import money_to_decimal
from .models.market_data import LastPrice
from .utils import CandleUtils, DateTimeUtils


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

    def initialize(self) -> None:
        """Инициализация клиента и регистрация tools."""
        if self._initialized:
            return

        self.logger.info("🔧 Setting up Tinkoff client...")

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

    def _get_instrument_info(self, uid: str) -> tuple[str, str]:
        """Получить имя и тикер инструмента по UID.

        Args:
            uid: UID инструмента

        Returns:
            tuple: (name, ticker) или ("Unknown", "UNKNOWN") если не найдено
        """
        return self._cache.get_instrument_info(uid)

    def _paginate_instruments(
        self, instruments: list[Instrument], limit: int, offset: int
    ) -> PaginatedInstrumentsResponse:
        """Применить пагинацию к списку инструментов.

        Args:
            instruments: Список инструментов для пагинации
            limit: Максимальное количество элементов
            offset: Смещение для пагинации

        Returns:
            PaginatedInstrumentsResponse: Пагинированный результат
        """
        total = len(instruments)
        start_idx = offset
        end_idx = offset + limit

        # Проверяем границы
        if start_idx >= total:
            paginated_instruments = []
        else:
            paginated_instruments = instruments[start_idx:end_idx]

        return PaginatedInstrumentsResponse.create(
            instruments=paginated_instruments,
            total=total,
            limit=limit,
            offset=offset,
        )

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
            response = client.operations.get_portfolio(
                account_id=self.config.account_id
            )

            # Обогащаем позиции данными об инструментах
            portfolio = PortfolioResponse.from_tinkoff(response)
            for position in portfolio.positions:
                name, ticker = self._get_instrument_info(position.instrument_id)
                position.instrument_name = name
                position.instrument_ticker = ticker

            return portfolio

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
            response = client.operations.get_positions(
                account_id=self.config.account_id
            )
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
            from_dt = DateTimeUtils.parse_iso_datetime(from_date) if from_date else None
            to_dt = DateTimeUtils.parse_iso_datetime(to_date) if to_date else None

            response = client.operations.get_operations(
                account_id=self.config.account_id,
                figi=instrument_uid or "",
                from_=from_dt,
                to=to_dt,
            )

            # Обогащаем операции данными об инструментах
            operations = OperationsResponse.from_tinkoff(response)
            for operation in operations.operations:
                if operation.instrument_id:
                    name, ticker = self._get_instrument_info(operation.instrument_id)
                    operation.instrument_name = name
                    operation.instrument_ticker = ticker

            return operations

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

            # Обогащаем данные именами из кэша
            enriched_prices = []
            for tinkoff_price in response.last_prices:
                name, ticker = self._get_instrument_info(tinkoff_price.instrument_uid)

                price = LastPrice(
                    instrument_id=tinkoff_price.instrument_uid,
                    instrument_name=name,
                    instrument_ticker=ticker,
                    price=money_to_decimal(tinkoff_price.price) or Decimal("0"),
                    time=tinkoff_price.time.isoformat() if tinkoff_price.time else "",
                )
                enriched_prices.append(price)

            return LastPricesResponse(prices=enriched_prices)

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
        candle_interval = CandleUtils.get_candle_interval(interval)

        with self._client_context() as client:
            # Преобразуем строки в datetime если нужно
            from_dt = DateTimeUtils.parse_iso_datetime(from_date)
            to_dt = DateTimeUtils.parse_iso_datetime(to_date)

            response = client.market_data.get_candles(
                instrument_id=instrument_uid,
                interval=candle_interval,
                from_=from_dt,
                to=to_dt,
            )

            # Обогащаем данными об инструменте
            candles = CandlesResponse.from_tinkoff(response, instrument_uid, interval)
            name, ticker = self._get_instrument_info(instrument_uid)
            candles.instrument_name = name
            candles.instrument_ticker = ticker

            return candles

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
                instrument_id=instrument_uid, depth=depth
            )

            # Обогащаем данными об инструменте
            order_book = OrderBookResponse.from_tinkoff(response)
            name, ticker = self._get_instrument_info(instrument_uid)
            order_book.instrument_name = name
            order_book.instrument_ticker = ticker

            return order_book

    def get_trading_status(self, instrument_uid: str) -> TradingStatusResponse:
        """Получить торговый статус инструмента.

        Args:
            instrument_uid: UID инструмента

        Returns:
            TradingStatusResponse: Информация о возможности торговли инструментом
        """
        with self._client_context() as client:
            response = client.market_data.get_trading_status(
                instrument_id=instrument_uid
            )

            # Обогащаем данными об инструменте
            trading_status = TradingStatusResponse.from_tinkoff(response)
            name, ticker = self._get_instrument_info(instrument_uid)
            trading_status.instrument_name = name
            trading_status.instrument_ticker = ticker

            return trading_status

    def get_trading_schedules(
        self,
        exchange: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> TradingSchedulesResponse:
        """Получить расписание торгов.

        Args:
            exchange: Код биржи (MOEX, SPB). Если None - все биржи
            from_date: Начало периода в ISO формате
            to_date: Конец периода в ISO формате

        Returns:
            TradingSchedulesResponse: Расписание торгов на указанный период
        """
        with self._client_context() as client:
            # Преобразуем строки в datetime если нужно
            from_dt = DateTimeUtils.parse_iso_datetime(from_date) if from_date else None
            to_dt = DateTimeUtils.parse_iso_datetime(to_date) if to_date else None

            response = client.instruments.trading_schedules(
                exchange=exchange or "",
                from_=from_dt,
                to=to_dt,
            )

            return TradingSchedulesResponse.from_tinkoff(response)

    # Orders methods
    def get_orders(self) -> list[Order]:
        """Получить активные заявки.

        Returns:
            list[Order]: Список активных торговых заявок
        """
        with self._client_context() as client:
            response = client.orders.get_orders(account_id=self.config.account_id)
            return [Order.from_tinkoff(order) for order in response.orders]

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
            instrument_id: ID инструмента (UID)
            quantity: Количество лотов
            direction: Направление заявки. Используйте:
                - ORDER_DIRECTION_BUY для покупки
                - ORDER_DIRECTION_SELL для продажи
            order_type: Тип заявки. Используйте:
                - ORDER_TYPE_MARKET для рыночной заявки
                - ORDER_TYPE_LIMIT для лимитной заявки
            price: Цена (только для ORDER_TYPE_LIMIT заявок). Принимает строку "15.475", число 15.475 или int 15

        Returns:
            OrderResponse: Информация о созданной заявке
        """
        # Создаем объект заявки из параметров
        order_request = CreateOrderRequest(
            instrument_id=instrument_id,
            quantity=quantity,
            direction=direction,  # type: ignore
            order_type=order_type,  # type: ignore
            price=Decimal(str(price)) if price is not None else None,
        )

        with self._client_context() as client:
            tinkoff_request = order_request.to_tinkoff_request(self.config.account_id)
            response = client.orders.post_order(**tinkoff_request)
            return OrderResponse.from_tinkoff(response)

    def cancel_order(self, order_id: str) -> CancelOrderResponse:
        """Отменить торговую заявку.

        Args:
            order_id: ID заявки для отмены

        Returns:
            CancelOrderResponse: Результат отмены заявки
        """
        with self._client_context() as client:
            response = client.orders.cancel_order(
                account_id=self.config.account_id, order_id=order_id
            )
            return CancelOrderResponse(
                success=True, time=getattr(response, "time", None)
            )

    # Stop orders methods
    def get_stop_orders(self) -> StopOrdersResponse:
        """Получить список активных стоп-заявок по счету.

        Используйте для получения списка активных стоп-заявок (stop-loss, take-profit, stop-limit).
        Стоп-заявки обрабатываются отдельно от обычных заявок.

        Returns:
            StopOrdersResponse: Список активных стоп-заявок
        """
        with self._client_context() as client:
            response = client.stop_orders.get_stop_orders(
                account_id=self.config.account_id
            )
            return StopOrdersResponse.from_tinkoff(response)

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

        Создать стоп-заявку для автоматического управления рисками. Используйте:
        - stop_order_type: STOP_ORDER_TYPE_TAKE_PROFIT для тейк-профита
        - stop_order_type: STOP_ORDER_TYPE_STOP_LOSS для стоп-лосса
        - stop_order_type: STOP_ORDER_TYPE_STOP_LIMIT для стоп-лимита
        - direction: STOP_ORDER_DIRECTION_BUY для покупки, STOP_ORDER_DIRECTION_SELL для продажи
        - expiration_type: STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL до отмены
        - expiration_type: STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_DATE до указанной даты

        Args:
            instrument_id: ID инструмента (UID)
            quantity: Количество лотов
            direction: Направление (STOP_ORDER_DIRECTION_BUY/SELL)
            stop_order_type: Тип стоп-заявки (STOP_ORDER_TYPE_TAKE_PROFIT/STOP_LOSS/STOP_LIMIT)
            stop_price: Цена активации стоп-заявки. Принимает строку "280.5", число 280.5 или int 280
            expiration_type: Тип экспирации (GOOD_TILL_CANCEL/GOOD_TILL_DATE)
            price: Цена исполнения (только для STOP_ORDER_TYPE_STOP_LIMIT). Принимает строку "275.0", число 275.0 или int 275
            expire_date: Дата экспирации в ISO формате (для GOOD_TILL_DATE)

        Returns:
            StopOrderResponse: Информация о созданной стоп-заявке
        """
        # Создаем объект стоп-заявки из параметров
        stop_order_request = StopOrderRequest(
            instrument_id=instrument_id,
            quantity=quantity,
            direction=direction,  # type: ignore[arg-type]
            stop_order_type=stop_order_type,  # type: ignore[arg-type]
            stop_price=Decimal(str(stop_price)),
            expiration_type=expiration_type,  # type: ignore[arg-type]
            price=Decimal(str(price)) if price is not None else None,
            expire_date=datetime.fromisoformat(expire_date) if expire_date else None,
        )

        with self._client_context() as client:
            tinkoff_request = stop_order_request.to_tinkoff_request(
                self.config.account_id
            )
            response = client.stop_orders.post_stop_order(**tinkoff_request)
            return StopOrderResponse(
                success=True,
                stop_order_id=response.stop_order_id,
                order_request_id=getattr(response, "order_request_id", None),
            )

    def cancel_stop_order(self, stop_order_id: str) -> CancelStopOrderResponse:
        """Отменить активную стоп-заявку по её ID.

        Args:
            stop_order_id: ID стоп-заявки для отмены

        Returns:
            CancelStopOrderResponse: Результат отмены стоп-заявки
        """
        with self._client_context() as client:
            response = client.stop_orders.cancel_stop_order(
                account_id=self.config.account_id, stop_order_id=stop_order_id
            )
            return CancelStopOrderResponse(
                success=True, time=getattr(response, "time", None)
            )

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

    def get_shares(
        self,
        limit: int = DEFAULT_INSTRUMENTS_LIMIT,
        offset: int = DEFAULT_PAGINATION_OFFSET,
    ) -> PaginatedInstrumentsResponse:
        """Получить список акций с пагинацией.

        Args:
            limit: Максимальное количество акций для возврата (по умолчанию 100000)
            offset: Смещение для пагинации (по умолчанию 0)

        Returns:
            PaginatedInstrumentsResponse: Пагинированный список акций
        """
        shares = self._cache.get_instruments_by_type("share")
        return self._paginate_instruments(shares, limit, offset)

    def get_bonds(
        self,
        limit: int = DEFAULT_INSTRUMENTS_LIMIT,
        offset: int = DEFAULT_PAGINATION_OFFSET,
    ) -> PaginatedInstrumentsResponse:
        """Получить список облигаций с пагинацией.

        Args:
            limit: Максимальное количество облигаций для возврата (по умолчанию 100000)
            offset: Смещение для пагинации (по умолчанию 0)

        Returns:
            PaginatedInstrumentsResponse: Пагинированный список облигаций
        """
        bonds = self._cache.get_instruments_by_type("bond")
        return self._paginate_instruments(bonds, limit, offset)

    def get_etfs(
        self,
        limit: int = DEFAULT_INSTRUMENTS_LIMIT,
        offset: int = DEFAULT_PAGINATION_OFFSET,
    ) -> PaginatedInstrumentsResponse:
        """Получить список ETF с пагинацией.

        Args:
            limit: Максимальное количество ETF для возврата (по умолчанию 100000)
            offset: Смещение для пагинации (по умолчанию 0)

        Returns:
            PaginatedInstrumentsResponse: Пагинированный список ETF
        """
        etfs = self._cache.get_instruments_by_type("etf")
        return self._paginate_instruments(etfs, limit, offset)


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
