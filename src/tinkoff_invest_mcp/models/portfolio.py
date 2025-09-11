"""Pydantic модели для портфеля и баланса."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field
from tinkoff.invest.schemas import PortfolioPosition as TinkoffPortfolioPosition
from tinkoff.invest.schemas import PortfolioResponse as TinkoffPortfolioResponse
from tinkoff.invest.schemas import PositionsResponse as TinkoffPositionsResponse

from .common import money_to_decimal


class PortfolioPosition(BaseModel):
    """Позиция в портфеле."""

    instrument_id: str = Field(..., description="UID инструмента")
    instrument_type: str = Field(..., description="Тип инструмента")
    quantity: Decimal = Field(
        ..., description="Количество инструмента в портфеле в штуках"
    )
    average_price: Decimal = Field(..., description="Средневзвешенная цена позиции")
    current_price: Decimal = Field(..., description="Текущая цена за 1 инструмент")
    expected_yield: Decimal = Field(
        ..., description="Текущая рассчитанная доходность позиции"
    )
    currency: str = Field(..., description="Валюта инструмента")
    blocked: bool = Field(..., description="Заблокировано на бирже")
    accrued_interest: Decimal | None = Field(
        None, description="Текущий НКД (накопленный купонный доход)"
    )

    @classmethod
    def from_tinkoff(cls, position: TinkoffPortfolioPosition) -> "PortfolioPosition":
        """Создать из Tinkoff PortfolioPosition.

        Args:
            position: PortfolioPosition от Tinkoff API

        Returns:
            PortfolioPosition: Конвертированная позиция
        """
        quantity = money_to_decimal(position.quantity) or Decimal("0")
        average_price = money_to_decimal(position.average_position_price) or Decimal(
            "0"
        )
        current_price = money_to_decimal(position.current_price) or Decimal("0")
        expected_yield = money_to_decimal(position.expected_yield) or Decimal("0")

        accrued_interest = (
            money_to_decimal(position.current_nkd) if position.current_nkd else None
        )

        return cls(
            instrument_id=position.instrument_uid,
            instrument_type=position.instrument_type,
            quantity=quantity,
            average_price=average_price,
            current_price=current_price,
            expected_yield=expected_yield,
            currency=position.average_position_price.currency
            if position.average_position_price
            else "RUB",
            blocked=position.blocked,
            accrued_interest=accrued_interest,
        )


class PortfolioResponse(BaseModel):
    """Ответ с составом портфеля."""

    positions: list[PortfolioPosition] = Field(
        default_factory=list, description="Список позиций в портфеле"
    )
    total_yield_percentage: Decimal = Field(
        ..., description="Текущая относительная доходность портфеля, в %"
    )
    account_id: str = Field(..., description="Идентификатор счёта")
    total_portfolio_value: Decimal = Field(..., description="Общая стоимость портфеля")
    daily_yield: Decimal = Field(..., description="Доходность за текущий торговый день")
    daily_yield_percentage: Decimal = Field(
        ...,
        description="Относительная доходность за текущий торговый день, в %",
    )

    @classmethod
    def from_tinkoff(cls, portfolio: TinkoffPortfolioResponse) -> "PortfolioResponse":
        """Создать из Tinkoff PortfolioResponse.

        Args:
            portfolio: PortfolioResponse от Tinkoff API

        Returns:
            PortfolioResponse: Конвертированный портфель
        """
        positions = [PortfolioPosition.from_tinkoff(pos) for pos in portfolio.positions]
        total_yield_percentage = money_to_decimal(portfolio.expected_yield) or Decimal(
            "0"
        )
        total_portfolio_value = money_to_decimal(
            portfolio.total_amount_portfolio
        ) or Decimal("0")
        daily_yield = money_to_decimal(portfolio.daily_yield) or Decimal("0")
        daily_yield_percentage = money_to_decimal(
            portfolio.daily_yield_relative
        ) or Decimal("0")

        return cls(
            positions=positions,
            total_yield_percentage=total_yield_percentage,
            account_id=portfolio.account_id,
            total_portfolio_value=total_portfolio_value,
            daily_yield=daily_yield,
            daily_yield_percentage=daily_yield_percentage,
        )


class CashBalanceResponse(BaseModel):
    """Ответ с денежными балансами по валютам."""

    money: list[dict[str, Any]] = Field(
        default_factory=list, description="Денежные позиции портфеля"
    )
    blocked: list[dict[str, Any]] = Field(
        default_factory=list, description="Заблокированные позиции портфеля"
    )

    @classmethod
    def from_tinkoff(cls, positions: TinkoffPositionsResponse) -> "CashBalanceResponse":
        """Создать из Tinkoff PositionsResponse.

        Args:
            positions: PositionsResponse от Tinkoff API

        Returns:
            CashBalanceResponse: Конвертированный баланс
        """
        return cls(
            money=[mv.__dict__ for mv in positions.money],
            blocked=[mv.__dict__ for mv in positions.blocked],
        )
