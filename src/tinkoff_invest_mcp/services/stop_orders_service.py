"""Stop orders service for Tinkoff Invest MCP."""

from datetime import datetime
from decimal import Decimal

from ..models import (
    CancelStopOrderResponse,
    StopOrderRequest,
    StopOrderResponse,
    StopOrdersResponse,
)
from .base import BaseTinkoffService


class StopOrdersService(BaseTinkoffService):
    """Сервис для работы со стоп-заявками."""

    def get_stop_orders(self) -> StopOrdersResponse:
        """Получить список активных стоп-заявок.

        Returns:
            StopOrdersResponse: Список активных стоп-заявок
        """
        with self._client_context() as client:
            response = client.stop_orders.get_stop_orders(
                account_id=self.config.account_id
            )

            return StopOrdersResponse.from_tinkoff(response)

    def post_stop_order(
        self,
        instrument_id: str,
        quantity: int,
        direction: str,
        stop_order_type: str,
        stop_price: str | float | int,
        expiration_type: str,
        price: str | float | int | None = None,
        expire_date: str | None = None,
    ) -> StopOrderResponse:
        """Создать стоп-заявку.

        Args:
            instrument_id: Идентификатор инструмента
            quantity: Количество лотов
            direction: Направление стоп-заявки:
                - STOP_ORDER_DIRECTION_BUY для покупки
                - STOP_ORDER_DIRECTION_SELL для продажи
            stop_order_type: Тип стоп-заявки:
                - STOP_ORDER_TYPE_TAKE_PROFIT - тейк-профит
                - STOP_ORDER_TYPE_STOP_LOSS - стоп-лосс
                - STOP_ORDER_TYPE_STOP_LIMIT - стоп-лимит
            stop_price: Цена активации стоп-заявки. Принимает строку, число или int
            expiration_type: Тип истечения стоп-заявки:
                - STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL - до отмены
                - STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_DATE - до даты
            price: Цена исполнения (для STOP_LIMIT). Принимает строку, число или int
            expire_date: Дата истечения (для GOOD_TILL_DATE). Формат ISO 8601

        Returns:
            StopOrderResponse: Информация о созданной стоп-заявке
        """
        stop_order_request = StopOrderRequest(
            instrument_id=instrument_id,
            quantity=quantity,
            direction=direction,  # type: ignore[arg-type]
            stop_order_type=stop_order_type,  # type: ignore[arg-type]
            stop_price=Decimal(str(stop_price)),
            expiration_type=expiration_type,  # type: ignore[arg-type]
            price=Decimal(str(price)) if price is not None else None,
            expire_date=datetime.fromisoformat(expire_date) if expire_date else None,
        )

        with self._client_context() as client:
            tinkoff_request = stop_order_request.to_tinkoff_request(
                self.config.account_id
            )
            response = client.stop_orders.post_stop_order(**tinkoff_request)

            return StopOrderResponse(
                success=True,
                stop_order_id=response.stop_order_id,
                order_request_id=response.order_request_id,
            )

    def cancel_stop_order(self, stop_order_id: str) -> CancelStopOrderResponse:
        """Отменить стоп-заявку.

        Args:
            stop_order_id: Идентификатор стоп-заявки

        Returns:
            CancelStopOrderResponse: Информация об отмене стоп-заявки
        """
        with self._client_context() as client:
            response = client.stop_orders.cancel_stop_order(
                account_id=self.config.account_id, stop_order_id=stop_order_id
            )

            return CancelStopOrderResponse(
                success=True,
                time=response.time,
            )
