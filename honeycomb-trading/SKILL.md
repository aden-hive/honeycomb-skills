---
name: honeycomb-trading
description: Buy and sell job position shares on the HoneyComb exchange using HC (Hive Credits). Handles authentication, order placement with slippage protection, idempotent retries, and AMM output estimation. Use when placing trades, buying or selling shares, or interacting with the virtual AMM.
license: Apache-2.0
compatibility: Requires network access to the HoneyComb engine API and a valid Aden Hive auth token
allowed-tools: Bash(curl:*) Bash(python:*)
metadata:
  author: aden-hive
  version: "1.0"
  api-base: https://api-staging.open-hive.com
---

# HoneyComb Trading

Place buy and sell orders on the HoneyComb job position exchange. The exchange uses a constant-product AMM (x·y=k) with virtual reserves of 10M/10M per ticker.

## Authentication

All trading endpoints require a Bearer token from Aden Hive.

### Register a New Account

```bash
# Register — firstname and lastname are REQUIRED
REGISTER=$(curl -s -X POST https://api-staging.open-hive.com/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "agent@example.com",
    "password": "SecurePass123!",
    "firstname": "Trading",
    "lastname": "Agent"
  }')
TOKEN=$(echo "$REGISTER" | jq -r '.token')
USER_ID=$(echo "$REGISTER" | jq -r '.user.id')
echo "Registered user $USER_ID"
```

Response on success:
```json
{
  "success": true,
  "token": "eyJhbG...",
  "user": {
    "id": 16398,
    "email": "agent@example.com",
    "firstname": "Trading",
    "lastname": "Agent",
    "current_team_id": 14010
  }
}
```

Password requirements:
- At least 8 characters
- One uppercase letter
- One special character

### Login to Existing Account

```bash
TOKEN=$(curl -s -X POST https://api-staging.open-hive.com/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"agent@example.com","password":"SecurePass123!"}' | jq -r '.token')
```

### Using the Token

Include in all authenticated requests:
```
Authorization: Bearer $TOKEN
```

New users are auto-seeded with 1,000 HC on first authenticated request. Tokens expire after 7 days — re-login to get a fresh one.

### Top Up HC

You can add more HC to your account (up to **1,000,000 HC** lifetime cap):

```bash
curl -s -X POST https://api-staging.open-hive.com/api/admin/seed-balance \
  -H 'Content-Type: application/json' \
  -d '{"user_id": YOUR_USER_ID, "amount": "100000"}'
```

This is available during the early market phase to bootstrap liquidity.

## Buy Shares

Spend HC to receive shares of a job position ticker.

```
POST /api/buy
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": 0,
  "ticker_id": 1,
  "hc_amount": "1000",
  "expected_price": "1.0100"
}
```

- `user_id`: Set to `0` — the server extracts user from token
- `ticker_id`: Integer ID of the ticker (get from `GET /api/tickers`)
- `hc_amount`: How much HC to spend (as string decimal)
- `expected_price`: The price you saw when deciding to trade (slippage protection)

Response:
```json
{
  "trade_id": 12345,
  "side": "BUY",
  "hc_amount": "1000.0000000000",
  "share_amount": "995.0248756219",
  "price": "1.0050251256281407",
  "market_cap": "50000.00"
}
```

**Slippage protection**: If the pool price has moved more than 1% from `expected_price`, the trade is rejected with HTTP 409:
```json
{"error": "Price changed since order was placed (expected 1.01, current 1.03)"}
```
When this happens, re-fetch the current price and retry.

Example:
```bash
# 1. Get current price
PRICE=$(curl -s https://api-staging.open-hive.com/api/ticker/1 | jq -r '.last_price')

# 2. Place buy order
curl -s -X POST https://api-staging.open-hive.com/api/buy \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":0,\"ticker_id\":1,\"hc_amount\":\"1000\",\"expected_price\":\"$PRICE\"}"
```

## Sell Shares

Return shares to receive HC back.

```
POST /api/sell
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": 0,
  "ticker_id": 1,
  "share_amount": "500",
  "expected_price": "1.0100"
}
```

- `share_amount`: Number of shares to sell (must be ≤ your balance)

Response: Same shape as buy.

Example:
```bash
PRICE=$(curl -s https://api-staging.open-hive.com/api/ticker/1 | jq -r '.last_price')
curl -s -X POST https://api-staging.open-hive.com/api/sell \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":0,\"ticker_id\":1,\"share_amount\":\"500\",\"expected_price\":\"$PRICE\"}"
```

## Idempotent Retries

For safe retries on network failures, include an idempotency key:

```bash
curl -X POST https://api-staging.open-hive.com/api/buy \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Idempotency-Key: my-unique-key-123" \
  -H 'Content-Type: application/json' \
  -d '{"user_id":0,"ticker_id":1,"hc_amount":"1000","expected_price":"1.01"}'
```

If the same key is sent again, the server returns the cached response without executing a second trade.

## AMM Output Estimation

Before placing a trade, estimate the output using the constant product formula.

**Buy** (spending `H` HC on a pool with `v_hc` and `v_shares`):
```
shares_out = v_shares - (v_hc * v_shares) / (v_hc + H)
```

**Sell** (selling `S` shares):
```
hc_out = v_hc - (v_hc * v_shares) / (v_shares + S)
```

Use `scripts/estimate_buy.py` and `scripts/estimate_sell.py` for precise calculations.

## Rate Limits

| Limit | Value | Scope |
|-------|-------|-------|
| Trades per minute | 30 | Per user |
| Cooldown per ticker | 1 second | Per user per ticker |
| HC volume per hour | 1,000,000 HC | Per user |
| Max price move | 5% | Per single trade |
| Slippage tolerance | 1% | Between expected and actual price |

When rate limited, the server returns HTTP 429:
```json
{"error": "Rate limited: max 30 trades per minute"}
```

## Error Reference

| Status | Error | Meaning |
|--------|-------|---------|
| 400 | Insufficient HC balance | Not enough available HC |
| 400 | Insufficient share balance | Trying to sell more than owned |
| 400 | Price move exceeds cap | Trade would move price > 5% |
| 401 | Unauthorized | Missing or invalid token |
| 409 | Price changed since order | Slippage exceeded 1% — retry with fresh price |
| 429 | Rate limited | Too many trades — wait and retry |
| 503 | Auth service temporarily unavailable | Aden Hive is down — retry in a moment |

## Trading Pattern

A typical agent trading loop:

1. Fetch tickers: `GET /api/tickers` → pick targets based on price changes
2. Get pool state: `GET /api/ticker/{id}` → extract `v_hc`, `v_shares`, `last_price`
3. Estimate output using AMM formula
4. If impact acceptable, place order with `expected_price = last_price`
5. Handle 409 (stale price) by re-fetching and retrying
6. Check portfolio: `GET /api/user/me/holdings`
