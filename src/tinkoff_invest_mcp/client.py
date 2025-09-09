"""Фабрика для создания и конфигурации Tinkoff AsyncClient."""

import os

from tinkoff.invest import AsyncClient
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX


def _get_env_var(name: str, required: bool = True, default: str = "") -> str:
    """Получить переменную окружения с валидацией."""
    value = os.environ.get(name, default)
    if required and not value:
        raise ValueError(f"Required environment variable '{name}' not set")
    return value


def _create_client_config() -> tuple[str, str, str, str]:
    """Создать конфигурацию для AsyncClient из переменных окружения."""
    token = _get_env_var("TINKOFF_TOKEN", required=True)
    account_id = _get_env_var("TINKOFF_ACCOUNT_ID", required=True)
    mode = _get_env_var("TINKOFF_MODE", required=False, default="sandbox")
    app_name = _get_env_var(
        "TINKOFF_APP_NAME", required=False, default="tinkoff-invest-mcp"
    )

    # Определяем API target
    target = INVEST_GRPC_API_SANDBOX if mode == "sandbox" else INVEST_GRPC_API

    return token, account_id, target, app_name


class AccountClient:
    """Клиент с встроенным account_id для удобства работы."""

    def __init__(self, client: AsyncClient, account_id: str):
        self._client = client
        self.account_id = account_id
        self._initialized_client = None

    async def __aenter__(self):
        self._initialized_client = await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def orders(self):
        if not self._initialized_client:
            raise RuntimeError("Client not initialized. Use 'async with' statement.")
        return self._initialized_client.orders

    @property
    def users(self):
        if not self._initialized_client:
            raise RuntimeError("Client not initialized. Use 'async with' statement.")
        return self._initialized_client.users

    @property
    def instruments(self):
        if not self._initialized_client:
            raise RuntimeError("Client not initialized. Use 'async with' statement.")
        return self._initialized_client.instruments

    @property
    def client(self):
        """Доступ к инициализированному клиенту."""
        if not self._initialized_client:
            raise RuntimeError("Client not initialized. Use 'async with' statement.")
        return self._initialized_client


def create_account_client() -> AccountClient:
    """Создать AccountClient с конфигурацией из переменных окружения."""
    token, account_id, target, app_name = _create_client_config()
    client = AsyncClient(token, target=target, app_name=app_name)
    return AccountClient(client, account_id)
