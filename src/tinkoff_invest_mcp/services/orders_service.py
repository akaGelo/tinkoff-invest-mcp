"""Orders service for Tinkoff Invest MCP."""

from decimal import Decimal

from ..models import (
    CancelOrderResponse,
    CreateOrderRequest,
    Order,
    OrderResponse,
)
from .base import BaseTinkoffService


class OrdersService(BaseTinkoffService):
    """Сервис для работы с торговыми заявками."""

    def get_orders(self) -> list[Order]:
        """Получить список активных торговых заявок.

        Returns:
            list[Order]: Список активных заявок
        """
        with self._client_context() as client:
            response = client.orders.get_orders(account_id=self.config.account_id)

            return [Order.from_tinkoff(order) for order in response.orders]

    def create_order(
        self,
        instrument_id: str,
        quantity: int,
        direction: str,
        order_type: str,
        price: str | float | int | None = None,
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
            price: Цена (только для ORDER_TYPE_LIMIT заявок). Принимает строку "15.475", число 15.475 или int 15

        Returns:
            OrderResponse: Информация о созданной заявке
        """
        order_request = CreateOrderRequest(
            instrument_id=instrument_id,
            quantity=quantity,
            direction=direction,  # type: ignore
            order_type=order_type,  # type: ignore
            price=Decimal(str(price)) if price is not None else None,
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
