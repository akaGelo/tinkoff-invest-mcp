"""Pydantic модели для рыночных данных."""

from decimal import Decimal

from pydantic import BaseModel, Field
from tinkoff.invest.schemas import (
    GetCandlesResponse as TinkoffGetCandlesResponse,
)
from tinkoff.invest.schemas import (
    GetOrderBookResponse as TinkoffGetOrderBookResponse,
)
from tinkoff.invest.schemas import (
    GetTradingStatusResponse as TinkoffGetTradingStatusResponse,
)
from tinkoff.invest.schemas import (
    HistoricCandle as TinkoffHistoricCandle,
)
from tinkoff.invest.schemas import (
    Order as TinkoffOrder,
)

from .common import money_to_decimal


class LastPrice(BaseModel):
    """Последняя цена инструмента."""

    instrument_id: str = Field(..., description="UID инструмента")
    instrument_name: str = Field(..., description="Название инструмента")
    instrument_ticker: str = Field(..., description="Тикер инструмента")
    price: Decimal = Field(..., description="Последняя цена")
    time: str = Field(..., description="Время обновления в ISO формате")


class LastPricesResponse(BaseModel):
    """Ответ с последними ценами."""

    prices: list[LastPrice] = Field(default_factory=list, description="Последние цены")


class Candle(BaseModel):
    """Историческая свеча."""

    time: str = Field(..., description="Время в ISO формате")
    open: Decimal = Field(..., description="Цена открытия")
    high: Decimal = Field(..., description="Максимальная цена")
    low: Decimal = Field(..., description="Минимальная цена")
    close: Decimal = Field(..., description="Цена закрытия")
    volume: int = Field(..., description="Объём торгов")
    is_complete: bool = Field(..., description="Завершённость свечи")

    @classmethod
    def from_tinkoff(cls, candle: TinkoffHistoricCandle) -> "Candle":
        """Создать из Tinkoff HistoricCandle.

        Args:
            candle: HistoricCandle от Tinkoff API

        Returns:
            Candle: Конвертированная свеча
        """
        open_price = money_to_decimal(candle.open) or Decimal("0")
        high_price = money_to_decimal(candle.high) or Decimal("0")
        low_price = money_to_decimal(candle.low) or Decimal("0")
        close_price = money_to_decimal(candle.close) or Decimal("0")

        return cls(
            time=candle.time.isoformat() if candle.time else "",
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=candle.volume,
            is_complete=candle.is_complete,
        )


class CandlesResponse(BaseModel):
    """Ответ с историческими свечами."""

    candles: list[Candle] = Field(
        default_factory=list, description="Исторические свечи"
    )
    instrument_id: str = Field(..., description="UID инструмента")
    instrument_name: str = Field(..., description="Название инструмента")
    instrument_ticker: str = Field(..., description="Тикер инструмента")
    interval: str = Field(..., description="Интервал свечей")

    @classmethod
    def from_tinkoff(
        cls, response: TinkoffGetCandlesResponse, instrument_id: str, interval: str
    ) -> "CandlesResponse":
        """Создать из Tinkoff GetCandlesResponse.

        Args:
            response: GetCandlesResponse от Tinkoff API
            instrument_id: UID инструмента
            interval: Интервал свечей

        Returns:
            CandlesResponse: Конвертированные свечи
        """
        candles = [Candle.from_tinkoff(candle) for candle in response.candles]

        return cls(
            candles=candles,
            instrument_id=instrument_id,
            instrument_name="Unknown",
            instrument_ticker="UNKNOWN",
            interval=interval,
        )


class OrderBookItem(BaseModel):
    """Элемент стакана заявок."""

    price: Decimal = Field(..., description="Цена")
    quantity: int = Field(..., description="Количество в лотах")

    @classmethod
    def from_tinkoff(cls, order: TinkoffOrder) -> "OrderBookItem":
        """Создать из Tinkoff Order.

        Args:
            order: Order от Tinkoff API

        Returns:
            OrderBookItem: Конвертированный элемент стакана
        """
        price = money_to_decimal(order.price) or Decimal("0")

        return cls(price=price, quantity=order.quantity)


class OrderBookResponse(BaseModel):
    """Ответ со стаканом заявок."""

    instrument_id: str = Field(..., description="UID инструмента")
    instrument_name: str = Field(..., description="Название инструмента")
    instrument_ticker: str = Field(..., description="Тикер инструмента")
    bids: list[OrderBookItem] = Field(
        default_factory=list, description="Заявки на покупку"
    )
    asks: list[OrderBookItem] = Field(
        default_factory=list, description="Заявки на продажу"
    )
    last_price: Decimal | None = Field(None, description="Последняя цена")
    close_price: Decimal | None = Field(None, description="Цена закрытия")
    limit_up: Decimal | None = Field(None, description="Верхний лимит цены")
    limit_down: Decimal | None = Field(None, description="Нижний лимит цены")
    time: str = Field(..., description="Время обновления в ISO формате")

    @classmethod
    def from_tinkoff(cls, response: TinkoffGetOrderBookResponse) -> "OrderBookResponse":
        """Создать из Tinkoff GetOrderBookResponse.

        Args:
            response: GetOrderBookResponse от Tinkoff API

        Returns:
            OrderBookResponse: Конвертированный стакан
        """
        bids = [OrderBookItem.from_tinkoff(bid) for bid in response.bids]
        asks = [OrderBookItem.from_tinkoff(ask) for ask in response.asks]

        last_price = (
            money_to_decimal(response.last_price) if response.last_price else None
        )
        close_price = (
            money_to_decimal(response.close_price) if response.close_price else None
        )
        limit_up = money_to_decimal(response.limit_up) if response.limit_up else None
        limit_down = (
            money_to_decimal(response.limit_down) if response.limit_down else None
        )

        return cls(
            instrument_id=response.instrument_uid,
            instrument_name="Unknown",
            instrument_ticker="UNKNOWN",
            bids=bids,
            asks=asks,
            last_price=last_price,
            close_price=close_price,
            limit_up=limit_up,
            limit_down=limit_down,
            time=response.orderbook_ts.isoformat() if response.orderbook_ts else "",
        )


class TradingStatusResponse(BaseModel):
    """Ответ со статусом торгов."""

    instrument_id: str = Field(..., description="UID инструмента")
    instrument_name: str = Field(..., description="Название инструмента")
    instrument_ticker: str = Field(..., description="Тикер инструмента")
    trading_status: str = Field(..., description="Статус торгов")
    limit_order_available: bool = Field(..., description="Доступность лимитных заявок")
    market_order_available: bool = Field(..., description="Доступность рыночных заявок")

    @classmethod
    def from_tinkoff(
        cls, response: TinkoffGetTradingStatusResponse
    ) -> "TradingStatusResponse":
        """Создать из Tinkoff GetTradingStatusResponse.

        Args:
            response: GetTradingStatusResponse от Tinkoff API

        Returns:
            TradingStatusResponse: Конвертированный статус
        """
        return cls(
            instrument_id=response.instrument_uid,
            instrument_name="Unknown",
            instrument_ticker="UNKNOWN",
            trading_status=str(response.trading_status),
            limit_order_available=response.limit_order_available_flag,
            market_order_available=response.market_order_available_flag,
        )
