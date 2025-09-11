"""Pydantic модели для истории операций."""

from decimal import Decimal

from pydantic import BaseModel, Field
from tinkoff.invest.schemas import Operation as TinkoffOperation
from tinkoff.invest.schemas import OperationsResponse as TinkoffOperationsResponse

from .common import money_to_decimal


class Operation(BaseModel):
    """Операция в истории счёта."""

    id: str = Field(..., description="ID операции")
    date: str = Field(..., description="Дата операции в ISO формате")
    type: str = Field(..., description="Тип операции")
    instrument_id: str | None = Field(None, description="UID инструмента")
    payment: Decimal = Field(..., description="Сумма операции")
    currency: str = Field(..., description="Валюта операции")
    price: Decimal | None = Field(None, description="Цена операции за 1 инструмент")
    quantity: int | None = Field(None, description="Количество единиц инструмента")
    state: str = Field(
        ..., description="Статус операции (EXECUTED, CANCELED, PROGRESS)"
    )
    quantity_rest: int | None = Field(
        None, description="Неисполненный остаток по сделке"
    )
    instrument_type: str | None = Field(
        None, description="Тип инструмента (bond, share, currency, etf, futures)"
    )
    type_description: str | None = Field(
        None, description="Текстовое описание типа операции"
    )

    @classmethod
    def from_tinkoff(cls, operation: TinkoffOperation) -> "Operation":
        """Создать из Tinkoff Operation.

        Args:
            operation: Operation от Tinkoff API

        Returns:
            Operation: Конвертированная операция
        """
        payment = money_to_decimal(operation.payment) or Decimal("0")
        price = money_to_decimal(operation.price) if operation.price else None

        # Новые поля
        state = str(operation.state) if operation.state else "UNSPECIFIED"
        quantity_rest = (
            operation.quantity_rest if hasattr(operation, "quantity_rest") else None
        )
        instrument_type = (
            operation.instrument_type if hasattr(operation, "instrument_type") else None
        )
        type_description = operation.type if hasattr(operation, "type") else None

        return cls(
            id=operation.id,
            date=operation.date.isoformat() if operation.date else "",
            type=str(operation.operation_type),
            instrument_id=operation.instrument_uid
            if hasattr(operation, "instrument_uid")
            else None,
            payment=payment,
            currency=operation.currency,
            price=price,
            quantity=operation.quantity if hasattr(operation, "quantity") else None,
            state=state,
            quantity_rest=quantity_rest,
            instrument_type=instrument_type,
            type_description=type_description,
        )


class OperationsResponse(BaseModel):
    """Ответ со списком операций."""

    operations: list[Operation] = Field(
        default_factory=list, description="Список операций"
    )

    @classmethod
    def from_tinkoff(
        cls, operations: TinkoffOperationsResponse
    ) -> "OperationsResponse":
        """Создать из Tinkoff OperationsResponse.

        Args:
            operations: OperationsResponse от Tinkoff API

        Returns:
            OperationsResponse: Конвертированные операции
        """
        operation_list = [Operation.from_tinkoff(op) for op in operations.operations]

        return cls(operations=operation_list)
