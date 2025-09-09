"""Модели для создания торговых поручений."""

from decimal import Decimal
from enum import Enum
from typing import ClassVar
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


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
    price: Decimal | None = Field(None, description="Цена за лот (для LIMIT ордеров)")
    order_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Уникальный ID поручения"
    )

    @field_validator("price")
    @classmethod
    def validate_price(cls, v, info):
        """Валидация цены в зависимости от типа ордера."""
        if not info.data:
            return v

        order_type = info.data.get("order_type")

        if order_type == OrderType.LIMIT and v is None:
            raise ValueError("Price is required for LIMIT orders")

        if order_type == OrderType.MARKET and v is not None:
            raise ValueError("Price should not be set for MARKET orders")

        if v is not None and v <= 0:
            raise ValueError("Price must be positive")

        return v

    class Config:
        use_enum_values = True
        json_encoders: ClassVar = {Decimal: str}
