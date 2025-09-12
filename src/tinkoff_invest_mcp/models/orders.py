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
    execution_report_status: str = Field(
        ..., description="Текущий статус заявки (поручения)"
    )
    executed_order_price: Decimal | None = Field(
        None, description="Исполненная цена заявки"
    )
    initial_commission: Decimal | None = Field(None, description="Начальная комиссия")
    executed_commission: Decimal | None = Field(
        None, description="Фактическая комиссия по итогам исполнения заявки"
    )
    service_commission: Decimal | None = Field(
        None, description="Сервисная комиссия (биржевой сбор, гербовый сбор и т.д.)"
    )
    order_request_id: str | None = Field(
        None, description="Идентификатор ключа идемпотентности"
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
            execution_report_status=str(order.execution_report_status)
            if hasattr(order, "execution_report_status")
            else "UNKNOWN",
            executed_order_price=money_to_decimal(order.executed_order_price)
            if hasattr(order, "executed_order_price")
            else None,
            initial_commission=money_to_decimal(order.initial_commission)
            if hasattr(order, "initial_commission")
            else None,
            executed_commission=money_to_decimal(order.executed_commission)
            if hasattr(order, "executed_commission")
            else None,
            service_commission=money_to_decimal(order.service_commission)
            if hasattr(order, "service_commission")
            else None,
            order_request_id=getattr(order, "order_request_id", None),
        )

    @property
    def total_commission(self) -> Decimal | None:
        """Общая сумма всех комиссий.

        Returns:
            Decimal | None: Сумма executed_commission и service_commission или None
        """
        if self.executed_commission is None:
            return None
        total = self.executed_commission
        if self.service_commission:
            total += self.service_commission
        return total
