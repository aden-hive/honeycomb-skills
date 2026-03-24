---
name: honeycomb-market-data
description: Read market data from the HoneyComb job position exchange. Get ticker prices, price changes, pool state, trade history, and real-time price feeds. Use when analyzing market conditions, checking prices, or researching job position tickers. No authentication required.
license: Apache-2.0
compatibility: Requires network access to the HoneyComb engine API
metadata:
  author: aden-hive
  version: "1.0"
  api-base: https://api-staging.open-hive.com
---

# HoneyComb Market Data

Read-only market intelligence for the HoneyComb job position exchange. All endpoints are public — no authentication required.

The API base URL is provided as an environment variable `HONEYCOMB_API_URL` or defaults to `https://api-staging.open-hive.com`.

## List All Tickers

Get all job position tickers with current prices and historical price changes.

```
GET /api/tickers
```

Response (array):
```json
{
  "id": 1,
  "symbol": "SWENG",
  "job_title": "Software Engineer",
  "status": "ACTIVE",
  "last_price": "1.0523",
  "total_supply": "50000.00",
  "total_shorted": "1200.00",
  "real_hc": "52615.00",
  "price_1h_ago": "1.0500",
  "price_24h_ago": "1.0200",
  "price_7d_ago": "1.0000",
  "price_30d_ago": "1.0000"
}
```

Calculate price change: `change_pct = (last_price - price_Xh_ago) / price_Xh_ago * 100`

Example:
```bash
curl -s https://api-staging.open-hive.com/api/tickers | jq '.[0:5]'
```

## Get Ticker Detail

Get full pool state for a specific ticker. Includes virtual reserves needed for AMM calculations.

```
GET /api/ticker/{id}
```

Response:
```json
{
  "id": 1,
  "symbol": "SWENG",
  "job_title": "Software Engineer",
  "description": "Designs, develops, and maintains software systems",
  "status": "ACTIVE",
  "v_hc": "10050000.00",
  "v_shares": "9950248.75",
  "k": "100000000000000.00",
  "real_hc": "50000.00",
  "total_supply": "49751.25",
  "total_shorted": "0",
  "last_price": "1.0100"
}
```

Key fields:
- `v_hc` / `v_shares`: Virtual reserves (the AMM state). Price = v_hc / v_shares.
- `k`: Constant product (v_hc × v_shares). Never changes.
- `real_hc`: Actual HC deposited by traders.
- `total_supply`: Shares held by all users.
- `total_shorted`: Synthetic short shares outstanding.

Example:
```bash
curl -s https://api-staging.open-hive.com/api/ticker/1 | jq '{symbol, last_price, v_hc, v_shares}'
```

## Get Trade History

Get recent trades for a ticker (newest first).

```
GET /api/ticker/{id}/trades?limit=50&offset=0
```

Response (array):
```json
{
  "id": 12345,
  "user_id": 16130,
  "ticker_id": 1,
  "side": "BUY",
  "hc_amount": "1000.00",
  "share_amount": "995.02",
  "price": "1.0100",
  "created_at": "2026-03-24T15:30:00Z"
}
```

- `side`: "BUY" or "SELL" (shorts also create SELL trades)
- `limit`: Max 200 per request

Example:
```bash
curl -s "https://api-staging.open-hive.com/api/ticker/1/trades?limit=10" | jq '.[] | {side, hc_amount, price, created_at}'
```

## Estimate Price Impact

Before placing a trade, calculate the expected output and price impact using the constant product formula.

**Buy estimate** (spending `hc_amount` HC):
```
new_v_hc = v_hc + hc_amount
new_v_shares = k / new_v_hc
shares_out = v_shares - new_v_shares
exec_price = hc_amount / shares_out
price_impact = (exec_price / spot_price - 1) * 100
```

**Sell estimate** (selling `share_amount` shares):
```
new_v_shares = v_shares + share_amount
new_v_hc = k / new_v_shares
hc_out = v_hc - new_v_hc
exec_price = hc_out / share_amount
price_impact = (1 - exec_price / spot_price) * 100
```

Use `scripts/price_impact.py` for offline calculations.

## WebSocket Price Feed

Connect to the real-time price stream (zero-polling, PG LISTEN/NOTIFY backed):

```
ws://api-staging.open-hive.com/ws/prices
```

Initial message (snapshot of all tickers):
```json
{
  "event": "snapshot",
  "tickers": [
    {"ticker_id": 1, "symbol": "SWENG", "last_price": "1.01", "total_supply": "49751", "real_hc": "50000"}
  ],
  "timestamp": 1711324200000
}
```

Update messages (per-trade):
```json
{
  "event": "price_change",
  "data": {"ticker_id": 1, "last_price": "1.0105", "total_supply": "49800", "real_hc": "50250"},
  "timestamp": 1711324205000
}
```

## Health Check

```bash
curl -s https://api-staging.open-hive.com/api/health
# Returns: ok
```
