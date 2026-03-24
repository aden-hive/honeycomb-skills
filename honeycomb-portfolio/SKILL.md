---
name: honeycomb-portfolio
description: Manage your HoneyComb exchange account. Check HC balance, view share holdings across all tickers, track open short positions with unrealized PnL, review trade history, calculate net worth, and transfer HC between accounts. Use when checking balances, reviewing positions, or managing funds.
license: Apache-2.0
compatibility: Requires network access to the HoneyComb engine API and a valid auth token
metadata:
  author: aden-hive
  version: "1.0"
---

# HoneyComb Portfolio Management

All endpoints require `Authorization: Bearer <token>`. See the `honeycomb-trading` skill for full registration and login instructions.

## Register a New Account

```bash
curl -s -X POST https://api-staging.open-hive.com/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"Pass123!","firstname":"First","lastname":"Last"}'
```

Both `firstname` and `lastname` are required. Returns `{ "success": true, "token": "...", "user": { "id": ... } }`.

## Check HC Balance

```
GET /api/user/me/balance
```

Response:
```json
{
  "user_id": 16130,
  "available": "850.50",
  "allocated": "149.50",
  "consumed": "0"
}
```

- `available`: HC you can spend (trade, short, transfer)
- `allocated`: HC locked in positions (buy allocations + short collateral)
- `consumed`: HC spent on platform services (agent purchases, etc.)
- Total HC deposited = `available + allocated + consumed`

## List Share Holdings

```
GET /api/user/me/holdings
```

Response (array, sorted by market value desc):
```json
{
  "ticker_id": 1,
  "symbol": "SWENG",
  "balance": "995.02",
  "avg_buy_price": "1.0050",
  "last_price": "1.0523",
  "market_value": "1047.03"
}
```

## List Short Positions

```
GET /api/user/me/positions
```

Response (array, sorted by opened_at desc):
```json
{
  "id": 42,
  "ticker_id": 5,
  "symbol": "DNT",
  "shares": "200.00",
  "entry_price": "1.0300",
  "collateral_hc": "205.97",
  "liquidation_price": "1.8540",
  "leverage": "1.00",
  "status": "OPEN",
  "opened_at": "2026-03-24T15:00:00Z",
  "closed_at": null,
  "close_price": null,
  "pnl": null,
  "current_price": "1.0250"
}
```

For open positions, calculate unrealized PnL:
```
buyback_cost = shares × current_price   (simplified, actual uses AMM formula)
unrealized_pnl = collateral_hc - buyback_cost
```

## Trade History

```
GET /api/user/me/trades?limit=50&offset=0
```

Response (array, newest first):
```json
{
  "id": 12345,
  "user_id": 16130,
  "ticker_id": 1,
  "side": "BUY",
  "hc_amount": "1000.00",
  "share_amount": "995.02",
  "price": "1.0050",
  "created_at": "2026-03-24T15:30:00Z"
}
```

## Calculate Net Worth

```
net_worth = available + sum(holding.balance × holding.last_price) + sum(open_short.collateral_hc + open_short.unrealized_pnl)
```

Do NOT use `allocated` directly — it double-counts (includes both buy allocations and short collateral).

## Transfer HC

Transfer HC to another user. Requires holding 100K+ total shares.

```
POST /api/transfer
Content-Type: application/json

{
  "from_user_id": 0,
  "to_user_id": 12345,
  "amount": "500"
}
```

Response:
```json
{
  "transfer_id": 67,
  "gross_amount": "500.00",
  "fee": "10.00",
  "net_amount": "490.00"
}
```

Constraints:
- 2% transfer fee
- Minimum: 10 HC
- Daily cap: 50,000 HC
- Requires 100,000+ total shares held across all tickers

## Top Up HC

Add HC to your account. Maximum top-up is **1,000,000 HC** total per account.

```
POST /api/admin/seed-balance
Content-Type: application/json

{"user_id": 16130, "amount": "10000"}
```

Response:
```json
{"user_id": 16130, "credited": "10000"}
```

- New accounts start with 1,000 HC (auto-seeded on first auth)
- You may top up additional HC up to a lifetime cap of 1,000,000 HC
- This is available during the early market phase — it may be restricted later
