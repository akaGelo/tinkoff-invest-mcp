"""Декораторы и утилиты для Tinkoff Invest MCP Server."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from tinkoff.invest.schemas import MoneyValue

logger = logging.getLogger(__name__)


def serialize_money(money: MoneyValue | None) -> float | None:
    """Конвертация MoneyValue в float.

    Args:
        money: MoneyValue объект от Tinkoff API

    Returns:
        float: Денежная сумма в decimal формате или None
    """
    if not money:
        return None
    return money.units + money.nano / 1_000_000_000


def handle_api_errors(func: Callable) -> Callable:
    """Декоратор для обработки ошибок Tinkoff API.

    Логирует ошибки и может добавить retry logic в будущем.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {e}")
            # В будущем можно добавить retry logic, метрики, etc.
            raise

    return wrapper
