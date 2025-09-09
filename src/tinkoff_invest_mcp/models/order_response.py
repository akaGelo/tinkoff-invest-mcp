"""Модель ответа при создании ордера."""

from typing import ClassVar

from pydantic import BaseModel


class OrderResponse(BaseModel):
    """Ответ при создании торгового поручения."""

    order_id: str
    execution_report_status: str | None = None
    message: str | None = None
    direction: str | None = None

    class Config:
        json_encoders: ClassVar = {str: str}
