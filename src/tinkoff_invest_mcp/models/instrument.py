"""Модели для финансовых инструментов."""

from pydantic import BaseModel


class Instrument(BaseModel):
    """Финансовый инструмент."""

    uid: str
    name: str
    ticker: str
    currency: str
    instrument_type: str
    lot: int | None = None
    country_of_risk: str | None = None
    sector: str | None = None

    @classmethod
    def from_tinkoff_share(cls, share) -> "Instrument":
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
        )

    @classmethod
    def from_tinkoff_bond(cls, bond) -> "Instrument":
        """Создать из Tinkoff Bond объекта."""
        return cls(
            uid=bond.uid,
            name=bond.name,
            ticker=bond.ticker,
            currency=bond.currency,
            instrument_type="bond",
            lot=bond.lot,
            country_of_risk=bond.country_of_risk,
        )

    @classmethod
    def from_tinkoff_etf(cls, etf) -> "Instrument":
        """Создать из Tinkoff Etf объекта."""
        return cls(
            uid=etf.uid,
            name=etf.name,
            ticker=etf.ticker,
            currency=etf.currency,
            instrument_type="etf",
            lot=etf.lot,
            country_of_risk=etf.country_of_risk,
        )

    @classmethod
    def from_tinkoff_find_result(cls, instrument) -> "Instrument":
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
        )
