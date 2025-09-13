"""Orders service for Tinkoff Invest MCP."""

from datetime import datetime, timedelta
from decimal import Decimal

from tinkoff.invest.schemas import OrderExecutionReportStatus

from ..models import (
    CancelOrderResponse,
    CreateOrderRequest,
    Order,
    OrderResponse,
)
from .base import BaseTinkoffService


class OrdersService(BaseTinkoffService):
    """Сервис для работы с торговыми заявками."""

    def get_active_orders(self, days_back: int = 7) -> list[Order]:
        """Получить список активных торговых заявок.

        Args:
            days_back: Количество дней назад для поиска заявок (по умолчанию 7)

        Returns:
            list[Order]: Список активных заявок
        """
        with self._client_context() as client:
            response = client.orders.get_orders(
                account_id=self.config.account_id,
                from_=datetime.now() - timedelta(days=days_back),
                to=datetime.now(),
                execution_status=[
                    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_NEW,
                    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_PARTIALLYFILL,
                ],
            )

            return [Order.from_tinkoff(order) for order in response.orders]

    def create_order(
        self,
        instrument_id: str,
        quantity: int,
        direction: str,
        order_type: str,
        price: float,
    ) -> OrderResponse:
        """Создать торговую заявку.

        Args:
            instrument_id: Идентификатор инструмента
            quantity: Количество лотов
            direction: Направление заявки:
                - ORDER_DIRECTION_BUY для покупки
                - ORDER_DIRECTION_SELL для продажи
            order_type: Тип заявки:
                - ORDER_TYPE_MARKET для рыночной заявки
                - ORDER_TYPE_LIMIT для лимитной заявки
            price: Цена. Для ORDER_TYPE_LIMIT - конкретная цена, для ORDER_TYPE_MARKET - передавать 0.0

        Returns:
            OrderResponse: Информация о созданной заявке
        """
        order_request = CreateOrderRequest(
            instrument_id=instrument_id,
            quantity=quantity,
            direction=direction,  # type: ignore
            order_type=order_type,  # type: ignore
            price=Decimal(price),
        )

        with self._client_context() as client:
            tinkoff_request = order_request.to_tinkoff_request(self.config.account_id)
            response = client.orders.post_order(**tinkoff_request)

            return OrderResponse.from_tinkoff(response)

    def cancel_order(self, order_id: str) -> CancelOrderResponse:
        """Отменить торговую заявку.

        Args:
            order_id: Идентификатор заявки

        Returns:
            CancelOrderResponse: Информация об отмене заявки
        """
        with self._client_context() as client:
            response = client.orders.cancel_order(
                account_id=self.config.account_id, order_id=order_id
            )

            return CancelOrderResponse(
                success=True,
                time=response.time,
            )
