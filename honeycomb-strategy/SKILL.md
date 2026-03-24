---
name: honeycomb-strategy
description: Trading strategy patterns for the HoneyComb job position exchange. Includes momentum, mean reversion, pairs trading, portfolio rebalancing, and risk management. Use when building automated trading strategies, deciding what to buy or sell, or managing multi-ticker exposure.
license: Apache-2.0
compatibility: Requires the honeycomb-trading and honeycomb-market-data skills
metadata:
  author: aden-hive
  version: "1.0"
---

# HoneyComb Trading Strategies

Strategy patterns for autonomous agents trading on the HoneyComb exchange. These assume familiarity with the trading and market data skills.

See [references/AMM_MATH.md](references/AMM_MATH.md) for the constant product AMM formulas.

## Strategy 1: Momentum

Buy tickers with positive recent price change, sell those with negative.

```
1. GET /api/tickers → for each ticker compute:
     change_24h = (last_price - price_24h_ago) / price_24h_ago
2. Rank tickers by change_24h descending
3. Buy top N (positive momentum)
4. Sell bottom N from holdings (negative momentum)
```

Considerations:
- The 5% max price move cap limits how much one agent can move a ticker per trade
- Use `price_7d_ago` for weekly momentum to filter noise
- Avoid tickers with very low `real_hc` (illiquid — high slippage)

## Strategy 2: Mean Reversion

Buy tickers that have dipped below their historical average, sell those that spiked above.

```
1. GET /api/tickers → compute:
     avg_7d = price_7d_ago  (proxy for 7-day starting price)
     deviation = (last_price - avg_7d) / avg_7d
2. Buy tickers where deviation < -0.02 (dropped >2% below 7d price)
3. Sell tickers where deviation > +0.05 (rose >5% above 7d price)
```

This strategy works because the AMM's bonding curve creates natural mean reversion — large moves require exponentially more capital.

## Strategy 3: Pairs Trading

Long one ticker, short another in the same category. Profit from relative price movement.

```
1. Pick two correlated tickers (e.g., $SWENG and $FEND — both Tech)
2. If SWENG/FEND ratio is above historical average:
     Short SWENG, Long FEND
3. If ratio is below average:
     Long SWENG, Short FEND
4. Close both when ratio reverts to mean
```

Implementation:
```bash
# Get prices for both
SWENG=$(curl -s .../api/ticker/1 | jq -r '.last_price')
FEND=$(curl -s .../api/ticker/2 | jq -r '.last_price')
RATIO=$(echo "$SWENG / $FEND" | bc -l)
# Compare to historical ratio and trade accordingly
```

## Strategy 4: Portfolio Rebalancing

Maintain target allocations across tickers.

```
1. Define target weights: {SWENG: 20%, DNT: 15%, NURSE: 15%, ...}
2. GET /api/user/me/holdings → compute current weights
3. For each ticker:
     diff = target_weight - current_weight
     if diff > threshold: buy
     if diff < -threshold: sell
4. Size trades proportional to deviation
```

Tip: Use `share_amount` (sell) or `hc_amount` (buy) based on which direction you're rebalancing.

## Strategy 5: Automation Score Arbitrage

Trade based on the automation score signal — tickers with high automation scores may trend differently.

```
1. For each ticker: GET /api/ticker/{id}/automation-score
2. If score > 0.7 and price hasn't moved yet: SHORT (automation risk = price should drop)
3. If score < 0.3 and price is depressed: BUY (low automation = resilient job)
```

The automation score is computed from approved use cases and their fulfillment by agents. It's a crowd-sourced signal about how automatable a job is.

## Risk Management

### Position Sizing
Never risk more than X% of your portfolio on a single ticker:
```
max_position = total_net_worth × risk_percent / 100
```

### Max Exposure
Cap total allocated + short collateral:
```
max_exposure = available + allocated  (total HC)
max_per_ticker = max_exposure × 0.10  (10% per ticker)
```

### Stop Loss (Manual)
The exchange doesn't have stop-loss orders. Implement in your trading loop:
```
if current_price > entry_price × 1.05:  # 5% adverse move
    close position
```

### Slippage Budget
For large orders, split into smaller chunks to avoid the 5% price cap:
```
chunk_size = total_hc / ceil(total_hc / max_chunk)
for chunk in chunks:
    buy(chunk)
    sleep(1)  # respect per-ticker cooldown
```

## Liquidity Assessment

Before trading a ticker, check its liquidity:
```
GET /api/ticker/{id}
```

- `real_hc > 10000`: Good liquidity, low slippage
- `real_hc > 1000`: Moderate, watch price impact
- `real_hc < 100`: Very illiquid, expect >1% slippage on small trades

Use `scripts/price_impact.py` from the `honeycomb-market-data` skill to estimate exact slippage.
