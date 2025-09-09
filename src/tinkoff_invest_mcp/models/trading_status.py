"""Модель торгового статуса инструмента."""

from pydantic import BaseModel, Field


class TradingStatus(BaseModel):
    """Торговый статус инструмента."""

    instrument_id: str = Field(..., description="Идентификатор инструмента")
    trading_status: str = Field(..., description="Статус торговли (название)")
    trading_status_value: int = Field(
        ..., description="Статус торговли (числовое значение)"
    )
    limit_order_available: bool = Field(..., description="Доступность лимитных заявок")
    market_order_available: bool = Field(..., description="Доступность рыночных заявок")
    api_trade_available: bool = Field(..., description="Доступность торговли через API")
    only_best_price: bool = Field(..., description="Только лучшая цена")
