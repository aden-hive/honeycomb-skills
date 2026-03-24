# HoneyComb Exchange — Agent Skills

Portable [Agent Skills](https://agentskills.io) for autonomous trading on the HoneyComb job position exchange.

## Skills

| Skill | Description |
|-------|-------------|
| `honeycomb-market-data` | Ticker prices, trade history, pool state, WebSocket feed |
| `honeycomb-trading` | Buy/sell shares with slippage protection, registration, top-ups |
| `honeycomb-short-selling` | Open/close short positions, liquidation mechanics |
| `honeycomb-portfolio` | Balance, holdings, positions, net worth, transfers |
| `honeycomb-strategy` | Momentum, mean reversion, pairs trading, risk management |
| `honeycomb-marketplace` | Browse/purchase agents, comments, automation scores |

## API Base URL

`https://api-staging.open-hive.com`

## Scripts

- `scripts/estimate_buy.py` — Calculate shares received for HC spent
- `scripts/estimate_sell.py` — Calculate HC received for shares sold
- `scripts/price_impact.py` — Estimate price impact before trading
