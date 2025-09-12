"""Модели для финансовых инструментов."""

from typing import Any

from pydantic import BaseModel, Field


class Instrument(BaseModel):
    """Финансовый инструмент."""

    uid: str = Field(..., description="UID инструмента")
    name: str = Field(..., description="Название инструмента")
    ticker: str = Field(..., description="Тикер инструмента")
    currency: str = Field(..., description="Валюта расчётов")
    instrument_type: str = Field(..., description="Тип инструмента")
    lot: int | None = Field(None, description="Лотность инструмента")
    country_of_risk: str | None = Field(None, description="Код страны риска")
    sector: str | None = Field(None, description="Сектор экономики")
    isin: str | None = Field(None, description="ISIN-идентификатор инструмента")
    trading_status: str | None = Field(
        None, description="Текущий режим торгов инструмента"
    )
    buy_available_flag: bool | None = Field(
        None, description="Признак доступности для покупки"
    )
    sell_available_flag: bool | None = Field(
        None, description="Признак доступности для продажи"
    )
    maturity_date: str | None = Field(
        None,
        description="Дата погашения облигации в ISO формате (только для облигаций)",
    )

    @classmethod
    def from_tinkoff_share(cls, share: Any) -> "Instrument":
        """Создать из Tinkoff Share объекта."""
        return cls(
            uid=share.uid,
            name=share.name,
            ticker=share.ticker,
            currency=share.currency,
            instrument_type="share",
            lot=share.lot,
            country_of_risk=share.country_of_risk,
            sector=share.sector,
            isin=getattr(share, "isin", None),
            trading_status=str(share.trading_status)
            if hasattr(share, "trading_status")
            else None,
            buy_available_flag=getattr(share, "buy_available_flag", None),
            sell_available_flag=getattr(share, "sell_available_flag", None),
            maturity_date=None,
        )

    @classmethod
    def from_tinkoff_bond(cls, bond: Any) -> "Instrument":
        """Создать из Tinkoff Bond объекта."""
        return cls(
            uid=bond.uid,
            name=bond.name,
            ticker=bond.ticker,
            currency=bond.currency,
            instrument_type="bond",
            lot=bond.lot,
            country_of_risk=bond.country_of_risk,
            sector=getattr(bond, "sector", None),
            isin=getattr(bond, "isin", None),
            trading_status=str(bond.trading_status)
            if hasattr(bond, "trading_status")
            else None,
            buy_available_flag=getattr(bond, "buy_available_flag", None),
            sell_available_flag=getattr(bond, "sell_available_flag", None),
            maturity_date=bond.maturity_date.isoformat()
            if hasattr(bond, "maturity_date") and bond.maturity_date
            else None,
        )

    @classmethod
    def from_tinkoff_etf(cls, etf: Any) -> "Instrument":
        """Создать из Tinkoff Etf объекта."""
        return cls(
            uid=etf.uid,
            name=etf.name,
            ticker=etf.ticker,
            currency=etf.currency,
            instrument_type="etf",
            lot=etf.lot,
            country_of_risk=etf.country_of_risk,
            sector=getattr(etf, "sector", None),
            isin=getattr(etf, "isin", None),
            trading_status=str(etf.trading_status)
            if hasattr(etf, "trading_status")
            else None,
            buy_available_flag=getattr(etf, "buy_available_flag", None),
            sell_available_flag=getattr(etf, "sell_available_flag", None),
            maturity_date=None,
        )

    @classmethod
    def from_tinkoff_find_result(cls, instrument: Any) -> "Instrument":
        """Создать из результата FindInstrument."""
        # Определяем тип инструмента по наличию полей
        if hasattr(instrument, "instrument_type"):
            instrument_type = instrument.instrument_type
        else:
            # Fallback определение типа
            instrument_type = "unknown"

        return cls(
            uid=instrument.uid,
            name=instrument.name,
            ticker=instrument.ticker,
            currency=getattr(instrument, "currency", "unknown"),
            instrument_type=instrument_type,
            lot=getattr(instrument, "lot", None),
            country_of_risk=getattr(instrument, "country_of_risk", None),
            sector=getattr(instrument, "sector", None),
            isin=getattr(instrument, "isin", None),
            trading_status=str(instrument.trading_status)
            if hasattr(instrument, "trading_status")
            else None,
            buy_available_flag=getattr(instrument, "buy_available_flag", None),
            sell_available_flag=getattr(instrument, "sell_available_flag", None),
            maturity_date=instrument.maturity_date.isoformat()
            if hasattr(instrument, "maturity_date") and instrument.maturity_date
            else None,
        )

    @classmethod
    def from_tinkoff(cls, instrument: Any) -> "Instrument":
        """Создать из любого инструмента Tinkoff API.

        Args:
            instrument: Любой инструмент от Tinkoff API

        Returns:
            Instrument: Конвертированный инструмент
        """
        # Определяем тип инструмента по его классу или атрибутам
        class_name = instrument.__class__.__name__.lower()

        if "share" in class_name or hasattr(instrument, "share_type"):
            return cls.from_tinkoff_share(instrument)
        elif "bond" in class_name or hasattr(instrument, "aci_value"):
            return cls.from_tinkoff_bond(instrument)
        elif "etf" in class_name or hasattr(instrument, "expense_commission"):
            return cls.from_tinkoff_etf(instrument)
        else:
            # Fallback к общему методу
            return cls.from_tinkoff_find_result(instrument)


class PaginatedInstrumentsResponse(BaseModel):
    """Пагинированный ответ для списка инструментов."""

    instruments: list[Instrument] = Field(..., description="Список инструментов")
    total: int = Field(..., description="Общее количество инструментов")
    limit: int = Field(..., description="Лимит записей на странице")
    offset: int = Field(..., description="Смещение от начала")
    has_more: bool = Field(..., description="Есть ли еще данные")

    @classmethod
    def create(
        cls,
        instruments: list[Instrument],
        total: int,
        limit: int,
        offset: int,
    ) -> "PaginatedInstrumentsResponse":
        """Создать пагинированный ответ.

        Args:
            instruments: Список инструментов для текущей страницы
            total: Общее количество инструментов
            limit: Лимит записей на странице
            offset: Смещение от начала

        Returns:
            PaginatedInstrumentsResponse: Пагинированный ответ
        """
        has_more = offset + limit < total
        return cls(
            instruments=instruments,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )
