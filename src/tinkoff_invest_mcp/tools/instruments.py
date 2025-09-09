"""MCP инструменты для работы с финансовыми инструментами."""

from fastmcp import FastMCP

from ..base import handle_api_errors
from ..client import AccountClient, create_account_client
from ..models.instrument import Instrument
from ..models.trading_status import TradingStatus


@handle_api_errors
async def get_shares_impl(account_client: AccountClient) -> list[Instrument]:
    """Получить список акций.

    Args:
        account_client: AccountClient для работы с Tinkoff API

    Returns:
        List[Instrument]: Список торгуемых акций
    """
    response = await account_client.client.instruments.shares()

    shares = []
    for share in response.instruments:
        if not share.api_trade_available_flag:
            continue

        instrument = Instrument.from_tinkoff_share(share)
        shares.append(instrument)

    return shares


@handle_api_errors
async def get_bonds_impl(account_client: AccountClient) -> list[Instrument]:
    """Получить список облигаций.

    Args:
        account_client: AccountClient для работы с Tinkoff API

    Returns:
        List[Instrument]: Список торгуемых облигаций
    """
    response = await account_client.client.instruments.bonds()

    bonds = []
    for bond in response.instruments:
        if not bond.api_trade_available_flag:
            continue

        instrument = Instrument.from_tinkoff_bond(bond)
        bonds.append(instrument)

    return bonds


@handle_api_errors
async def get_etfs_impl(account_client: AccountClient) -> list[Instrument]:
    """Получить список ETF фондов.

    Args:
        account_client: AccountClient для работы с Tinkoff API

    Returns:
        List[Instrument]: Список торгуемых ETF фондов
    """
    response = await account_client.client.instruments.etfs()

    etfs = []
    for etf in response.instruments:
        if not etf.api_trade_available_flag:
            continue

        instrument = Instrument.from_tinkoff_etf(etf)
        etfs.append(instrument)

    return etfs


@handle_api_errors
async def find_instrument_impl(
    account_client: AccountClient, query: str
) -> list[Instrument]:
    """Поиск инструментов по запросу.

    Args:
        account_client: AccountClient для работы с Tinkoff API
        query: Поисковый запрос (тикер, название, ISIN)

    Returns:
        List[Instrument]: Найденные инструменты
    """
    response = await account_client.client.instruments.find_instrument(query=query)

    instruments = []
    for instrument in response.instruments:
        inst = Instrument.from_tinkoff_find_result(instrument)
        instruments.append(inst)

    return instruments


@handle_api_errors
async def get_trading_status_impl(
    account_client: AccountClient, instrument_id: str
) -> TradingStatus:
    """Получить торговый статус инструмента.

    Args:
        account_client: AccountClient для работы с Tinkoff API
        instrument_id: Идентификатор инструмента (UID)

    Returns:
        TradingStatus: Торговый статус инструмента
    """
    response = await account_client.client.market_data.get_trading_status(
        instrument_id=instrument_id
    )

    trading_status = TradingStatus(
        instrument_id=instrument_id,
        trading_status=response.trading_status.name,
        trading_status_value=int(response.trading_status),
        limit_order_available=response.limit_order_available_flag,
        market_order_available=response.market_order_available_flag,
        api_trade_available=response.api_trade_available_flag,
        only_best_price=response.only_best_price,
    )

    return trading_status


def register_instruments_tools(mcp: FastMCP) -> None:
    """Регистрация всех MCP tools для работы с инструментами.

    Args:
        mcp: FastMCP сервер для регистрации tools
    """

    @mcp.tool()
    async def get_shares() -> list[Instrument]:
        """Get list of shares (stocks).

        Returns:
            List of tradeable shares with their details
        """
        account_client = create_account_client()
        async with account_client:
            return await get_shares_impl(account_client)

    @mcp.tool()
    async def get_bonds() -> list[Instrument]:
        """Get list of bonds.

        Returns:
            List of tradeable bonds with their details
        """
        account_client = create_account_client()
        async with account_client:
            return await get_bonds_impl(account_client)

    @mcp.tool()
    async def get_etfs() -> list[Instrument]:
        """Get list of ETF funds.

        Returns:
            List of tradeable ETF funds with their details
        """
        account_client = create_account_client()
        async with account_client:
            return await get_etfs_impl(account_client)

    @mcp.tool()
    async def find_instrument(query: str) -> list[Instrument]:
        """Search instruments by name, ticker, ISIN.

        Args:
            query: Search query (ticker, name, ISIN)

        Returns:
            List of found instruments
        """
        account_client = create_account_client()
        async with account_client:
            return await find_instrument_impl(account_client, query)

    @mcp.tool()
    async def get_trading_status(instrument_id: str) -> TradingStatus:
        """Get trading status for an instrument.

        Args:
            instrument_id: Instrument identifier (UID)

        Returns:
            Trading status information with availability flags
        """
        account_client = create_account_client()
        async with account_client:
            return await get_trading_status_impl(account_client, instrument_id)
