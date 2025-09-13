"""Market data service for Tinkoff Invest MCP."""

from datetime import datetime
from decimal import Decimal
from typing import ClassVar

from tinkoff.invest.schemas import CandleInterval

from ..models import (
    CandlesResponse,
    LastPricesResponse,
    OrderBookResponse,
    TradingSchedulesResponse,
    TradingStatusResponse,
)
from ..models.common import money_to_decimal
from ..models.market_data import LastPrice
from .base import BaseTinkoffService


class MarketDataService(BaseTinkoffService):
    """Сервис для работы с рыночными данными."""

    INTERVAL_MAP: ClassVar[dict[str, CandleInterval]] = {
        "CANDLE_INTERVAL_1_MIN": CandleInterval.CANDLE_INTERVAL_1_MIN,
        "CANDLE_INTERVAL_5_MIN": CandleInterval.CANDLE_INTERVAL_5_MIN,
        "CANDLE_INTERVAL_15_MIN": CandleInterval.CANDLE_INTERVAL_15_MIN,
        "CANDLE_INTERVAL_HOUR": CandleInterval.CANDLE_INTERVAL_HOUR,
        "CANDLE_INTERVAL_DAY": CandleInterval.CANDLE_INTERVAL_DAY,
        "1min": CandleInterval.CANDLE_INTERVAL_1_MIN,
        "5min": CandleInterval.CANDLE_INTERVAL_5_MIN,
        "15min": CandleInterval.CANDLE_INTERVAL_15_MIN,
        "hour": CandleInterval.CANDLE_INTERVAL_HOUR,
        "day": CandleInterval.CANDLE_INTERVAL_DAY,
    }

    @classmethod
    def _get_candle_interval(cls, interval: str) -> CandleInterval:
        """Преобразовать строковый интервал в enum.

        Args:
            interval: Строковое представление интервала

        Returns:
            CandleInterval: Enum интервала

        Raises:
            ValueError: Если интервал не поддерживается
        """
        candle_interval = cls.INTERVAL_MAP.get(interval)
        if not candle_interval:
            raise ValueError(f"Unsupported interval: {interval}")
        return candle_interval

    def get_last_prices(self, instrument_uids: list[str]) -> LastPricesResponse:
        """Получить последние цены по списку инструментов.

        Args:
            instrument_uids: Список идентификаторов инструментов

        Returns:
            LastPricesResponse: Последние цены по запрошенным инструментам
        """
        with self._client_context() as client:
            response = client.market_data.get_last_prices(instrument_id=instrument_uids)

            enriched_prices = []
            for tinkoff_price in response.last_prices:
                name, ticker = self._get_instrument_info(tinkoff_price.instrument_uid)

                price = LastPrice(
                    instrument_id=tinkoff_price.instrument_uid,
                    instrument_name=name,
                    instrument_ticker=ticker,
                    price=money_to_decimal(tinkoff_price.price) or Decimal("0"),
                    time=tinkoff_price.time.isoformat(),
                )
                enriched_prices.append(price)

            return LastPricesResponse(prices=enriched_prices)

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
        from_dt = self._parse_datetime(from_date)
        to_dt = self._parse_datetime(to_date) if to_date else datetime.now()
        tinkoff_interval = self._get_candle_interval(interval)

        with self._client_context() as client:
            response = client.market_data.get_candles(
                instrument_id=instrument_uid,
                from_=from_dt,
                to=to_dt,
                interval=tinkoff_interval,
            )

            name, ticker = self._get_instrument_info(instrument_uid)

            return CandlesResponse.from_tinkoff(response, instrument_uid, interval)

    def get_order_book(self, instrument_uid: str, depth: int = 10) -> OrderBookResponse:
        """Получить стакан заявок по инструменту.

        Args:
            instrument_uid: Идентификатор инструмента
            depth: Глубина стакана (количество уровней цен с каждой стороны)

        Returns:
            OrderBookResponse: Стакан заявок с бидами и асками
        """
        with self._client_context() as client:
            response = client.market_data.get_order_book(
                instrument_id=instrument_uid, depth=min(depth, 50)
            )

            name, ticker = self._get_instrument_info(instrument_uid)

            return OrderBookResponse.from_tinkoff(response)

    def get_trading_status(self, instrument_uid: str) -> TradingStatusResponse:
        """Получить торговый статус инструмента.

        Args:
            instrument_uid: Идентификатор инструмента

        Returns:
            TradingStatusResponse: Текущий торговый статус
        """
        with self._client_context() as client:
            response = client.market_data.get_trading_status(
                instrument_id=instrument_uid
            )

            name, ticker = self._get_instrument_info(instrument_uid)

            return TradingStatusResponse(
                instrument_id=response.instrument_uid,
                instrument_name=name,
                instrument_ticker=ticker,
                trading_status=str(response.trading_status),
                limit_order_available=response.limit_order_available_flag,
                market_order_available=response.market_order_available_flag,
            )

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
        from_dt = self._parse_datetime(from_date) if from_date else datetime.now()
        to_dt = self._parse_datetime(to_date) if to_date else from_dt

        with self._client_context() as client:
            response = client.instruments.trading_schedules(
                exchange=exchange, from_=from_dt, to=to_dt
            )

            return TradingSchedulesResponse.from_tinkoff(response)
