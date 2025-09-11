"""Модель ответа при создании ордера."""

from pydantic import BaseModel, ConfigDict
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
