"""Модели ответов для операций с заявками."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from tinkoff.invest.schemas import PostOrderResponse as TinkoffPostOrderResponse


class OrderResponse(BaseModel):
    """Ответ при создании торгового поручения."""

    order_id: str
    execution_report_status: str | None = None
    message: str | None = None
    direction: str | None = None

    @classmethod
    def from_tinkoff(cls, response: TinkoffPostOrderResponse) -> "OrderResponse":
        """Создать из Tinkoff PostOrderResponse.

        Args:
            response: PostOrderResponse от Tinkoff API

        Returns:
            OrderResponse: Конвертированный ответ
        """
        return cls(
            order_id=response.order_id,
            execution_report_status=str(response.execution_report_status)
            if response.execution_report_status
            else None,
            message=getattr(response, "message", None),
            direction=getattr(response, "direction", None),
        )

    model_config = ConfigDict()


class CancelOrderResponse(BaseModel):
    """Ответ при отмене торговой заявки."""

    success: bool = Field(..., description="Успешность операции")
    time: datetime | None = Field(None, description="Время отмены заявки")

    model_config = ConfigDict()


class StopOrderResponse(BaseModel):
    """Ответ при создании стоп-заявки."""

    success: bool = Field(..., description="Успешность операции")
    stop_order_id: str = Field(..., description="ID созданной стоп-заявки")
    order_request_id: str | None = Field(None, description="ID запроса заявки")

    model_config = ConfigDict()


class CancelStopOrderResponse(BaseModel):
    """Ответ при отмене стоп-заявки."""

    success: bool = Field(..., description="Успешность операции")
    time: datetime | None = Field(None, description="Время отмены стоп-заявки")

    model_config = ConfigDict()
