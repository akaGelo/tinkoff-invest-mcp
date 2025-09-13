"""Portfolio service for Tinkoff Invest MCP."""

from ..models import CashBalanceResponse, PortfolioResponse
from .base import BaseTinkoffService


class PortfolioService(BaseTinkoffService):
    """Сервис для работы с портфелем."""

    def get_portfolio(self) -> PortfolioResponse:
        """Получить состав портфеля.

        Возвращает все позиции в портфеле с информацией о:
        - Количестве и стоимости каждой позиции
        - Средней цене покупки и текущей цене
        - Ожидаемой доходности (P&L) по каждой позиции
        - Общей стоимости портфеля

        Returns:
            PortfolioResponse: Полная информация о портфеле
        """
        with self._client_context() as client:
            response = client.operations.get_portfolio(
                account_id=self.config.account_id
            )

            return PortfolioResponse.from_tinkoff(response)

    def get_cash_balance(self) -> CashBalanceResponse:
        """Получить денежный баланс счета.

        Возвращает информацию о денежных средствах:
        - Доступные средства по каждой валюте
        - Заблокированные средства (в активных заявках)

        Returns:
            CashBalanceResponse: Информация о денежных средствах
        """
        with self._client_context() as client:
            response = client.operations.get_positions(
                account_id=self.config.account_id
            )

            return CashBalanceResponse.from_tinkoff(response)
