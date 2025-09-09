"""Общие фикстуры для тестов."""

import json
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastmcp import Client

from tinkoff_invest_mcp.server import create_server


@pytest.fixture(autouse=True)
def load_test_env():
    """Автоматическая загрузка .env.test перед каждым тестом."""
    env_file = Path(".env.test")
    if env_file.exists():
        load_dotenv(env_file, override=True)


@pytest_asyncio.fixture
async def mcp_client():
    """Фикстура для MCP клиента."""
    mcp = create_server()
    async with Client(mcp) as client:
        yield client


def parse_mcp_result(result):
    """Парсим результат от FastMCP Client."""
    text_content = result.content[0]  # Первый элемент content
    json_data = text_content.text
    return json.loads(json_data)


@pytest_asyncio.fixture
async def test_instrument():
    """Фикстура с захардкоженным тестовым инструментом."""
    # Используем российскую акцию ВСМПО-АВИСМА
    return {
        "uid": "e9139ddd-bf3c-4d03-a94f-ffdf7234c6be",
        "name": "ВСМПО-АВИСМА",
        "ticker": "VSMO",
        "currency": "rub",
        "instrument_type": "share",
        "api_trade_available_flag": True,
        "lot": 1,
        "country_of_risk": "RU",
        "sector": "materials",
    }
