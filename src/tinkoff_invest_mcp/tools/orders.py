"""MCP инструменты для работы с торговыми заявками."""

from decimal import Decimal

from fastmcp import FastMCP
from tinkoff.invest import (
    OrderDirection as TinkoffOrderDirection,
)
from tinkoff.invest import (
    OrderType as TinkoffOrderType,
)
from tinkoff.invest.schemas import Quotation

from ..base import handle_api_errors
from ..client import AccountClient, create_account_client
from ..models.order_request import CreateOrderRequest, OrderDirection, OrderType
from ..models.order_response import OrderResponse
from ..models.orders import Order


@handle_api_errors
async def get_orders_impl(account_client: AccountClient) -> list[Order]:
    """Получить активные заявки для аккаунта.

    Args:
        account_client: AccountClient для работы с Tinkoff API

    Returns:
        List[dict]: Список активных заявок в упрощенном формате
    """
    response = await account_client.orders.get_orders(
        account_id=account_client.account_id
    )

    # Конвертируем через Pydantic модель
    orders = [Order.from_tinkoff(order) for order in response.orders]

    # Возвращаем как модели для MCP
    return orders


@handle_api_errors
async def create_order_impl(
    account_client: AccountClient, order_request: CreateOrderRequest
) -> OrderResponse:
    """Создать торговое поручение.

    Args:
        account_client: AccountClient для работы с Tinkoff API
        order_request: Параметры поручения

    Returns:
        dict: Информация о созданном поручении
    """
    # Конвертируем цену в Quotation если это LIMIT ордер
    price = None
    if order_request.order_type == OrderType.LIMIT and order_request.price:
        # Конвертируем Decimal в units + nano
        price_decimal = order_request.price
        units = int(price_decimal)
        nano = int((price_decimal - units) * 1_000_000_000)
        price = Quotation(units=units, nano=nano)

    # Конвертируем enum'ы в Tinkoff формат
    tinkoff_direction = (
        TinkoffOrderDirection.ORDER_DIRECTION_BUY
        if order_request.direction == OrderDirection.BUY
        else TinkoffOrderDirection.ORDER_DIRECTION_SELL
    )
    tinkoff_type = (
        TinkoffOrderType.ORDER_TYPE_MARKET
        if order_request.order_type == OrderType.MARKET
        else TinkoffOrderType.ORDER_TYPE_LIMIT
    )

    # Отправляем запрос
    response = await account_client.orders.post_order(
        instrument_id=order_request.instrument_id,
        quantity=order_request.quantity,
        price=price,
        direction=tinkoff_direction,
        account_id=account_client.account_id,
        order_type=tinkoff_type,
        order_id=order_request.order_id,
    )

    # Возвращаем через простую модель
    order_response = OrderResponse(
        order_id=response.order_id,
        execution_report_status=response.execution_report_status.name
        if response.execution_report_status
        else None,
        message=response.message,
        direction=response.direction.name if response.direction else None,
    )
    return order_response


def register_orders_tools(mcp: FastMCP) -> None:
    """Регистрация всех MCP tools для работы с заявками.

    Args:
        mcp: FastMCP сервер для регистрации tools
    """

    @mcp.tool()
    async def get_orders() -> list[Order]:
        """Get active orders for the configured account.

        Returns:
            List of active orders with order details
        """
        account_client = create_account_client()
        async with account_client:
            return await get_orders_impl(account_client)

    @mcp.tool()
    async def create_order(
        instrument_id: str,
        quantity: int,
        direction: str,
        order_type: str,
        price: str | None = None,
    ) -> OrderResponse:
        """Create a new trading order.

        Args:
            instrument_id: Instrument identifier (FIGI or instrument_uid)
            quantity: Number of lots to buy/sell (must be positive)
            direction: Order direction ("BUY" or "SELL")
            order_type: Order type ("MARKET" or "LIMIT")
            price: Price per lot as string (required for LIMIT orders, ignored for MARKET)

        Returns:
            Dict with created order information
        """
        # Конвертируем строки в enum'ы
        try:
            order_direction = OrderDirection(f"ORDER_DIRECTION_{direction.upper()}")
            order_order_type = OrderType(f"ORDER_TYPE_{order_type.upper()}")
        except ValueError as e:
            raise ValueError(f"Invalid direction or order_type: {e}")

        # Создаем запрос
        order_request = CreateOrderRequest(
            instrument_id=instrument_id,
            quantity=quantity,
            direction=order_direction,
            order_type=order_order_type,
            price=Decimal(price) if price is not None else None,
        )

        # Выполняем создание ордера
        account_client = create_account_client()
        async with account_client:
            return await create_order_impl(account_client, order_request)
