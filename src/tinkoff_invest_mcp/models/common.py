"""Общие Pydantic модели для Tinkoff Invest API."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field
from tinkoff.invest.schemas import MoneyValue


def money_to_decimal(money: Any) -> Decimal | None:
    """Конвертировать MoneyValue в Decimal.

    Общий метод для конвертации денежных сумм из API в точный формат.

    Args:
        money: MoneyValue объект от Tinkoff API

    Returns:
        Decimal: Сумма в точном формате или None
    """
    if not money:
        return None
    return Decimal(str(money.units)) + Decimal(str(money.nano)) / Decimal("1000000000")


class MoneyAmount(BaseModel):
    """Денежная сумма в упрощенном формате.

    Конвертирует MoneyValue от Tinkoff API в простой формат
    с Decimal значением и валютой для точности.
    """

    value: Decimal = Field(..., description="Сумма в decimal формате")
    currency: str = Field(..., description="Код валюты (RUB, USD, EUR)")

    @classmethod
    def from_tinkoff(cls, money: MoneyValue | None) -> "MoneyAmount | None":
        """Создать из Tinkoff MoneyValue.

        Args:
            money: MoneyValue объект от Tinkoff API

        Returns:
            MoneyAmount: Конвертированная сумма или None
        """
        if not money:
            return None

        value = money_to_decimal(money)
        return cls(value=value, currency=money.currency) if value is not None else None

    def __str__(self) -> str:
        """Строковое представление суммы."""
        return f"{self.value:.2f} {self.currency.upper()}"
