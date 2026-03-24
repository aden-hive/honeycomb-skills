---
name: honeycomb-short-selling
description: Open and manage short positions on HoneyComb job tickers. Profit when a ticker's price drops. Covers opening shorts with collateral, closing (full/partial), margin withdrawal, liquidation risk, and position health monitoring. Use when betting against a job position or hedging long exposure.
license: Apache-2.0
compatibility: Requires network access to the HoneyComb engine API and a valid auth token
metadata:
  author: aden-hive
  version: "1.0"
---

# HoneyComb Short Selling

Short a job position ticker to profit when its price drops. The exchange uses virtual shorting — no borrowing from other users. You lock HC as collateral, the system creates synthetic shares and sells them into the AMM.

All endpoints require `Authorization: Bearer <token>`.

## Open a Short Position

Lock HC as collateral to open a short position.

```
POST /api/short/open
Content-Type: application/json

{
  "user_id": 0,
  "ticker_id": 1,
  "collateral": "500",
  "expected_price": "1.0100"
}
```

- `collateral`: HC to lock (minimum 10 HC)
- Leverage is fixed at 1x: shares = collateral / spot_price
- `expected_price`: Slippage protection (same as buy/sell)

Response:
```json
{
  "position_id": 42,
  "shares": "495.05",
  "entry_price": "1.0100",
  "collateral_hc": "499.97",
  "liquidation_price": "1.8000"
}
```

- `collateral_hc`: The actual collateral stored (equals HC extracted from the virtual sell, not your input — they differ by slippage)
- `liquidation_price`: If the ticker reaches this price, your position is auto-liquidated

Example:
```bash
PRICE=$(curl -s https://api-staging.open-hive.com/api/ticker/1 | jq -r '.last_price')
curl -s -X POST https://api-staging.open-hive.com/api/short/open \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":0,\"ticker_id\":1,\"collateral\":\"500\",\"expected_price\":\"$PRICE\"}"
```

## Close a Short Position (Full)

Close the entire position. The system buys back shares from the AMM and returns your collateral ± PnL.

```
POST /api/short/close
Content-Type: application/json

{
  "user_id": 0,
  "position_id": 42
}
```

Response:
```json
{
  "position_id": 42,
  "pnl": "12.50",
  "returned_hc": "512.47"
}
```

- `pnl`: Positive = profit (price dropped), negative = loss (price rose)
- `returned_hc`: HC returned to your available balance. Clamped to 0 (max loss = collateral)

## Partial Close

Close part of a position, keeping the rest open.

```
POST /api/short/partial-close
Content-Type: application/json

{
  "user_id": 0,
  "position_id": 42,
  "shares_to_close": "200"
}
```

If `shares_to_close >= total_shares`, it becomes a full close.

## Withdraw Excess Margin

If your short is profitable, withdraw some of the excess margin without closing.

```
POST /api/short/withdraw-margin
Content-Type: application/json

{
  "user_id": 0,
  "position_id": 42,
  "amount": "50"
}
```

Fails if the withdrawal would push your position below the maintenance margin (20%).

## PnL Calculation

See [references/SHORT_MECHANICS.md](references/SHORT_MECHANICS.md) for the full math.

Quick summary:
- **PnL = collateral_hc - buyback_cost**
- buyback_cost = HC needed to remove your shares from the AMM
- If price dropped: buyback is cheap → positive PnL
- If price rose: buyback is expensive → negative PnL
- Max loss: your entire collateral

## Liquidation

A background engine checks all open shorts every 5 seconds. If the current price reaches your `liquidation_price`, the position is force-closed with a 1% liquidation fee.

**Maintenance margin**: 20%. Liquidation triggers when your position equity falls below 20% of collateral.

**Liquidation price formula** (1x leverage):
```
liq_price = entry_price × 1.8
```

## Check Open Positions

```bash
curl -s https://api-staging.open-hive.com/api/user/me/positions \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.status == "OPEN")'
```

## Trading Pattern: Short

1. Identify a ticker you believe will decline (check negative news, high automation score)
2. Get current price: `GET /api/ticker/{id}`
3. Open short with desired collateral
4. Monitor: check `current_price` vs `entry_price` in positions endpoint
5. Close when target PnL reached, or before liquidation price

## Buy-Closes-Short Rule

If you have an open short on ticker X and you place a **buy** on the same ticker, the buy auto-closes your short (partially or fully) instead of creating a conflicting long position. The engine handles this transparently.
