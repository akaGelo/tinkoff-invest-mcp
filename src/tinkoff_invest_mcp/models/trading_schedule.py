"""Pydantic модели для расписания торгов."""

from typing import Any

from pydantic import BaseModel, Field
from tinkoff.invest.schemas import (
    TradingDay as TinkoffTradingDay,
)
from tinkoff.invest.schemas import (
    TradingSchedule as TinkoffTradingSchedule,
)
from tinkoff.invest.schemas import (
    TradingSchedulesResponse as TinkoffTradingSchedulesResponse,
)


def _timestamp_to_iso(timestamp: Any) -> str | None:
    """Конвертировать timestamp в ISO строку.

    Args:
        timestamp: Timestamp от Tinkoff API или None

    Returns:
        str | None: ISO строка или None
    """
    if not timestamp:
        return None
    return timestamp.isoformat() if hasattr(timestamp, "isoformat") else None


class TradingDay(BaseModel):
    """Информация о торговом дне."""

    date: str = Field(..., description="Дата в ISO формате")
    is_trading_day: bool = Field(..., description="Торговый день или выходной")
    start_time: str | None = Field(None, description="Начало основной торговой сессии")
    end_time: str | None = Field(None, description="Конец основной торговой сессии")
    premarket_start_time: str | None = Field(None, description="Начало премаркета")
    premarket_end_time: str | None = Field(None, description="Конец премаркета")
    evening_start_time: str | None = Field(None, description="Начало вечерней сессии")
    evening_end_time: str | None = Field(None, description="Конец вечерней сессии")
    opening_auction_start_time: str | None = Field(
        None, description="Начало открывающего аукциона"
    )
    opening_auction_end_time: str | None = Field(
        None, description="Конец открывающего аукциона"
    )
    closing_auction_start_time: str | None = Field(
        None, description="Начало закрывающего аукциона"
    )
    closing_auction_end_time: str | None = Field(
        None, description="Конец закрывающего аукциона"
    )
    clearing_start_time: str | None = Field(None, description="Начало клиринга")
    clearing_end_time: str | None = Field(None, description="Конец клиринга")
    evening_opening_auction_start_time: str | None = Field(
        None, description="Начало вечернего открывающего аукциона"
    )

    @classmethod
    def from_tinkoff(cls, trading_day: TinkoffTradingDay) -> "TradingDay":
        """Создать из Tinkoff TradingDay.

        Args:
            trading_day: TradingDay от Tinkoff API

        Returns:
            TradingDay: Конвертированный торговый день
        """
        return cls(
            date=trading_day.date.isoformat() if trading_day.date else "",
            is_trading_day=trading_day.is_trading_day,
            start_time=_timestamp_to_iso(trading_day.start_time),
            end_time=_timestamp_to_iso(trading_day.end_time),
            premarket_start_time=_timestamp_to_iso(trading_day.premarket_start_time),
            premarket_end_time=_timestamp_to_iso(trading_day.premarket_end_time),
            evening_start_time=_timestamp_to_iso(trading_day.evening_start_time),
            evening_end_time=_timestamp_to_iso(trading_day.evening_end_time),
            opening_auction_start_time=_timestamp_to_iso(
                trading_day.opening_auction_start_time
            ),
            opening_auction_end_time=_timestamp_to_iso(
                trading_day.opening_auction_end_time
            ),
            closing_auction_start_time=_timestamp_to_iso(
                trading_day.closing_auction_start_time
            ),
            closing_auction_end_time=_timestamp_to_iso(
                trading_day.closing_auction_end_time
            ),
            clearing_start_time=_timestamp_to_iso(trading_day.clearing_start_time),
            clearing_end_time=_timestamp_to_iso(trading_day.clearing_end_time),
            evening_opening_auction_start_time=_timestamp_to_iso(
                trading_day.evening_opening_auction_start_time
            ),
        )


class TradingSchedule(BaseModel):
    """Расписание торгов для биржи."""

    exchange: str = Field(..., description="Код биржи (MOEX, SPB и т.д.)")
    days: list[TradingDay] = Field(
        default_factory=list, description="Список торговых дней"
    )

    @classmethod
    def from_tinkoff(cls, schedule: TinkoffTradingSchedule) -> "TradingSchedule":
        """Создать из Tinkoff TradingSchedule.

        Args:
            schedule: TradingSchedule от Tinkoff API

        Returns:
            TradingSchedule: Конвертированное расписание
        """
        days = [TradingDay.from_tinkoff(day) for day in schedule.days]
        return cls(exchange=schedule.exchange, days=days)


class TradingSchedulesResponse(BaseModel):
    """Ответ с расписанием торгов."""

    schedules: list[TradingSchedule] = Field(
        default_factory=list, description="Расписания бирж"
    )

    @classmethod
    def from_tinkoff(
        cls, response: TinkoffTradingSchedulesResponse
    ) -> "TradingSchedulesResponse":
        """Создать из Tinkoff TradingSchedulesResponse.

        Args:
            response: TradingSchedulesResponse от Tinkoff API

        Returns:
            TradingSchedulesResponse: Конвертированный ответ
        """
        schedules = [
            TradingSchedule.from_tinkoff(schedule) for schedule in response.exchanges
        ]
        return cls(schedules=schedules)
