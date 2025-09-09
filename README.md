# Tinkoff Invest MCP Server

MCP сервер для работы с Tinkoff Invest API.

## Установка

### Из исходников
```bash
uv tool install git+https://github.com/akaGelo/tinkoff-invest-mcp.git
```

### Для разработки
```bash
git clone git@github.com:akaGelo/tinkoff-invest-mcp.git
cd tinkoff-invest-mcp
uv tool install --editable .
```

## Тестирование

### MCP Inspector
Для интерактивного тестирования через веб-интерфейс:
```bash
npx @modelcontextprotocol/inspector uvx run python -m tinkoff_invest_mcp.server
```
Откроется браузер на http://localhost:6274 с UI для тестирования tools.
