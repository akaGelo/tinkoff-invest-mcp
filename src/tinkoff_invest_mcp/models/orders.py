"""Pydantic модели для работы с заявками."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from .common import money_to_decimal


class Order(BaseModel):
    """Модель торговой заявки из Tinkoff API.

    Упрощенная версия содержит только основные поля,
    необходимые для работы MCP инструментов.
    """

    order_id: str = Field(..., description="ID заявки для операций")
    instrument_uid: str = Field(..., description="UID инструмента для API")
    direction: str = Field(..., description="Направление: BUY/SELL")
    lots_requested: int = Field(..., description="Заявлено лотов")
    lots_executed: int = Field(..., description="Исполнено лотов")
    order_type: str = Field(..., description="Тип заявки: LIMIT/MARKET")
    order_date: datetime | None = Field(None, description="Дата создания заявки")
    price: Decimal | None = Field(None, description="Цена заявки в decimal")
    currency: str | None = Field(None, description="Валюта цены")
    aci_value: Decimal | None = Field(
        None, description="НКД (накопленный купонный доход)"
    )

    @classmethod
    def from_tinkoff(cls, order: Any) -> "Order":
        """Создать Order из объекта Tinkoff API.

        Args:
            order: Объект заявки от Tinkoff API

        Returns:
            Order: Конвертированная модель заявки
        """
        return cls(
            order_id=order.order_id,
            instrument_uid=order.instrument_uid,
            direction=str(order.direction),
            lots_requested=order.lots_requested,
            lots_executed=order.lots_executed,
            order_type=str(order.order_type),
            order_date=order.order_date,
            price=money_to_decimal(order.initial_security_price),
            currency=order.initial_security_price.currency
            if order.initial_security_price
            else None,
            aci_value=money_to_decimal(getattr(order, "aci_value", None)),
        )
