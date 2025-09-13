"""Модели для создания торговых поручений."""

from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from tinkoff.invest.schemas import OrderDirection as TinkoffOrderDirection
from tinkoff.invest.schemas import OrderType as TinkoffOrderType
from tinkoff.invest.utils import decimal_to_quotation


class OrderDirection(str, Enum):
    """Направление поручения."""

    BUY = "ORDER_DIRECTION_BUY"
    SELL = "ORDER_DIRECTION_SELL"


class OrderType(str, Enum):
    """Тип поручения."""

    MARKET = "ORDER_TYPE_MARKET"
    LIMIT = "ORDER_TYPE_LIMIT"


class CreateOrderRequest(BaseModel):
    """Запрос на создание торгового поручения."""

    instrument_id: str = Field(
        ..., description="Идентификатор инструмента (FIGI или instrument_uid)"
    )
    quantity: int = Field(..., gt=0, description="Количество лотов для покупки/продажи")
    direction: OrderDirection = Field(..., description="Направление поручения")
    order_type: OrderType = Field(..., description="Тип поручения")
    price: Decimal = Field(
        ..., description="Цена за лот. 0 для MARKET ордеров, >0 для LIMIT"
    )
    order_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Уникальный ID поручения"
    )

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal, info: Any) -> Decimal:
        """Валидация цены в зависимости от типа ордера."""
        if not info.data:
            return v

        order_type = info.data.get("order_type")

        if order_type == OrderType.LIMIT and v <= 0:
            raise ValueError("Price must be positive for LIMIT orders")

        if order_type == OrderType.MARKET and v != 0:
            raise ValueError("Price must be 0 for MARKET orders")

        if v < 0:
            raise ValueError("Price cannot be negative")

        return v

    def to_tinkoff_request(self, account_id: str) -> dict[str, Any]:
        """Преобразовать в параметры для Tinkoff API.

        Args:
            account_id: ID счета

        Returns:
            dict: Параметры для post_order
        """
        # Преобразуем направление
        tinkoff_direction = (
            TinkoffOrderDirection.ORDER_DIRECTION_BUY
            if self.direction == OrderDirection.BUY
            else TinkoffOrderDirection.ORDER_DIRECTION_SELL
        )

        # Преобразуем тип ордера
        tinkoff_order_type = (
            TinkoffOrderType.ORDER_TYPE_MARKET
            if self.order_type == OrderType.MARKET
            else TinkoffOrderType.ORDER_TYPE_LIMIT
        )

        # Базовые параметры
        params = {
            "figi": "",  # Будет пустым, используется instrument_id
            "instrument_id": self.instrument_id,
            "quantity": self.quantity,
            "direction": tinkoff_direction,
            "account_id": account_id,
            "order_type": tinkoff_order_type,
            "order_id": self.order_id,
        }

        # Для лимитных ордеров добавляем цену
        if self.order_type == OrderType.LIMIT and self.price > 0:
            params["price"] = decimal_to_quotation(self.price)

        return params

    model_config = ConfigDict(use_enum_values=True)
