"""Pydantic модели для работы со стоп-заявками."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from tinkoff.invest.schemas import StopOrderDirection as TinkoffStopOrderDirection
from tinkoff.invest.schemas import (
    StopOrderExpirationType as TinkoffStopOrderExpirationType,
)
from tinkoff.invest.schemas import StopOrderType as TinkoffStopOrderType
from tinkoff.invest.utils import decimal_to_quotation

from .common import money_to_decimal


class StopOrderType(str, Enum):
    """Тип стоп-заявки."""

    TAKE_PROFIT = "STOP_ORDER_TYPE_TAKE_PROFIT"
    STOP_LOSS = "STOP_ORDER_TYPE_STOP_LOSS"
    STOP_LIMIT = "STOP_ORDER_TYPE_STOP_LIMIT"


class StopOrderExpirationType(str, Enum):
    """Тип экспирации стоп-заявки."""

    GOOD_TILL_CANCEL = "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL"
    GOOD_TILL_DATE = "STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_DATE"


class StopOrderDirection(str, Enum):
    """Направление стоп-заявки."""

    BUY = "STOP_ORDER_DIRECTION_BUY"
    SELL = "STOP_ORDER_DIRECTION_SELL"


class StopOrder(BaseModel):
    """Модель стоп-заявки из Tinkoff API.

    Содержит информацию о стоп-заявке (stop-loss, take-profit, stop-limit).
    """

    stop_order_id: str = Field(..., description="ID стоп-заявки")
    instrument_uid: str = Field(..., description="UID инструмента")
    direction: str = Field(
        ..., description="Направление: STOP_ORDER_DIRECTION_BUY/SELL"
    )
    lots: int = Field(..., description="Количество лотов")
    stop_order_type: str = Field(
        ..., description="Тип: STOP_ORDER_TYPE_TAKE_PROFIT/STOP_LOSS/STOP_LIMIT"
    )
    price: Decimal | None = Field(None, description="Цена исполнения")
    stop_price: Decimal = Field(..., description="Цена активации стоп-заявки")
    currency: str | None = Field(None, description="Валюта цены")
    create_date: datetime | None = Field(None, description="Дата создания")
    activation_date_time: datetime | None = Field(None, description="Дата активации")
    expiration_time: datetime | None = Field(None, description="Дата экспирации")
    stop_order_status: str | None = Field(
        None, description="Статус стоп-заявки: ACTIVE/EXECUTED/CANCELED"
    )

    @classmethod
    def from_tinkoff(cls, stop_order: Any) -> "StopOrder":
        """Создать StopOrder из объекта Tinkoff API.

        Args:
            stop_order: Объект стоп-заявки от Tinkoff API

        Returns:
            StopOrder: Конвертированная модель стоп-заявки

        Raises:
            ValueError: Если stop_price отсутствует или не может быть сконвертирован
        """
        # Проверяем обязательное поле stop_price
        if not hasattr(stop_order, "stop_price") or stop_order.stop_price is None:
            raise ValueError("stop_price field is missing in Tinkoff API response")

        stop_price_decimal = money_to_decimal(stop_order.stop_price)
        if stop_price_decimal is None:
            raise ValueError(
                f"Failed to parse stop_price from API: {stop_order.stop_price}"
            )

        return cls(
            stop_order_id=stop_order.stop_order_id,
            instrument_uid=stop_order.instrument_uid,
            direction=str(stop_order.direction),
            lots=stop_order.lots_requested,
            stop_order_type=str(getattr(stop_order, "order_type", "UNKNOWN")),
            price=money_to_decimal(getattr(stop_order, "price", None)),
            stop_price=stop_price_decimal,
            currency=stop_order.stop_price.currency if stop_order.stop_price else None,
            create_date=getattr(stop_order, "create_date", None),
            activation_date_time=getattr(stop_order, "activation_date_time", None),
            expiration_time=getattr(stop_order, "expiration_time", None),
            stop_order_status=str(getattr(stop_order, "status", "UNKNOWN")),
        )


class StopOrderRequest(BaseModel):
    """Запрос на создание стоп-заявки."""

    instrument_id: str = Field(
        ..., description="Идентификатор инструмента (instrument_uid)"
    )
    quantity: int = Field(..., gt=0, description="Количество лотов")
    direction: StopOrderDirection = Field(..., description="Направление стоп-заявки")
    stop_order_type: StopOrderType = Field(
        ...,
        description="Тип стоп-заявки: STOP_ORDER_TYPE_TAKE_PROFIT для тейк-профита, STOP_ORDER_TYPE_STOP_LOSS для стоп-лосса, STOP_ORDER_TYPE_STOP_LIMIT для стоп-лимита",
    )
    stop_price: Decimal = Field(..., description="Цена активации стоп-заявки")
    price: Decimal = Field(
        ...,
        description="Цена исполнения. 0 для TAKE_PROFIT/STOP_LOSS, >0 для STOP_LIMIT",
    )
    expiration_type: StopOrderExpirationType = Field(
        ...,
        description="Тип экспирации: STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL до отмены, STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_DATE до даты",
    )
    expire_date: datetime | None = Field(
        None, description="Дата экспирации (обязательна для GOOD_TILL_DATE)"
    )

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal, info: Any) -> Decimal:
        """Валидация цены в зависимости от типа стоп-заявки."""
        if not info.data:
            return v

        stop_order_type = info.data.get("stop_order_type")

        if stop_order_type == StopOrderType.STOP_LIMIT and v <= 0:
            raise ValueError("Price must be positive for STOP_LIMIT orders")

        if (
            stop_order_type in (StopOrderType.TAKE_PROFIT, StopOrderType.STOP_LOSS)
            and v != 0
        ):
            raise ValueError("Price must be 0 for TAKE_PROFIT and STOP_LOSS orders")

        if v < 0:
            raise ValueError("Price cannot be negative")

        return v

    @field_validator("expire_date")
    @classmethod
    def validate_expire_date(cls, v: datetime | None, info: Any) -> datetime | None:
        """Валидация даты экспирации."""
        if not info.data:
            return v

        expiration_type = info.data.get("expiration_type")

        if expiration_type == StopOrderExpirationType.GOOD_TILL_DATE and v is None:
            raise ValueError("expire_date is required for GOOD_TILL_DATE orders")

        return v

    def to_tinkoff_request(self, account_id: str) -> dict[str, Any]:
        """Преобразовать в параметры для Tinkoff API.

        Args:
            account_id: ID счета

        Returns:
            dict: Параметры для post_stop_order
        """
        # Преобразуем направление
        tinkoff_direction = (
            TinkoffStopOrderDirection.STOP_ORDER_DIRECTION_BUY
            if self.direction == StopOrderDirection.BUY
            else TinkoffStopOrderDirection.STOP_ORDER_DIRECTION_SELL
        )

        # Преобразуем тип стоп-заявки
        if self.stop_order_type == StopOrderType.TAKE_PROFIT:
            tinkoff_stop_type = TinkoffStopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT
        elif self.stop_order_type == StopOrderType.STOP_LOSS:
            tinkoff_stop_type = TinkoffStopOrderType.STOP_ORDER_TYPE_STOP_LOSS
        else:  # STOP_LIMIT
            tinkoff_stop_type = TinkoffStopOrderType.STOP_ORDER_TYPE_STOP_LIMIT

        # Преобразуем тип экспирации
        tinkoff_expiration = (
            TinkoffStopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
            if self.expiration_type == StopOrderExpirationType.GOOD_TILL_CANCEL
            else TinkoffStopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_DATE
        )

        # Базовые параметры
        params = {
            "figi": "",  # Будет пустым, используется instrument_id
            "instrument_id": self.instrument_id,
            "quantity": self.quantity,
            "direction": tinkoff_direction,
            "account_id": account_id,
            "stop_order_type": tinkoff_stop_type,
            "expiration_type": tinkoff_expiration,
            "stop_price": decimal_to_quotation(self.stop_price),
        }

        # Для stop-limit заявок добавляем цену исполнения
        if self.stop_order_type == StopOrderType.STOP_LIMIT and self.price:
            params["price"] = decimal_to_quotation(self.price)

        # Для заявок с датой экспирации добавляем дату
        if (
            self.expiration_type == StopOrderExpirationType.GOOD_TILL_DATE
            and self.expire_date
        ):
            params["expire_date"] = self.expire_date

        return params

    model_config = ConfigDict(use_enum_values=True)


class StopOrdersResponse(BaseModel):
    """Ответ со списком стоп-заявок."""

    stop_orders: list[StopOrder] = Field(
        default_factory=list, description="Список активных стоп-заявок"
    )

    @classmethod
    def from_tinkoff(cls, response: Any) -> "StopOrdersResponse":
        """Создать StopOrdersResponse из ответа Tinkoff API.

        Args:
            response: Ответ от get_stop_orders

        Returns:
            StopOrdersResponse: Конвертированный ответ
        """
        return cls(
            stop_orders=[
                StopOrder.from_tinkoff(stop_order)
                for stop_order in getattr(response, "stop_orders", [])
            ]
        )
