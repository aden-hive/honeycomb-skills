# Constant Product AMM Mathematics

The HoneyComb exchange uses a Uniswap v2-style constant product AMM: **x · y = k**

## Pool State

Each ticker has a virtual liquidity pool:
- `v_hc`: Virtual HC reserve (starts at 10,000,000)
- `v_shares`: Virtual share reserve (starts at 10,000,000)
- `k = v_hc × v_shares` (constant, never changes)
- `spot_price = v_hc / v_shares`

## Buy Formula

Spending `H` HC to buy shares:
```
new_v_hc = v_hc + H
new_v_shares = k / new_v_hc
shares_out = v_shares - new_v_shares

execution_price = H / shares_out
new_spot_price = new_v_hc / new_v_shares
```

## Sell Formula

Selling `S` shares for HC:
```
new_v_shares = v_shares + S
new_v_hc = k / new_v_shares
hc_out = v_hc - new_v_hc

execution_price = hc_out / S
new_spot_price = new_v_hc / new_v_shares
```

## Price Impact

Price impact is the difference between spot price and execution price:
```
buy_impact = (H / shares_out) / spot_price - 1
sell_impact = 1 - (hc_out / S) / spot_price
```

For small trades relative to pool size, impact ≈ `trade_size / v_hc`.

## Slippage Curve

The AMM's slippage follows a hyperbolic curve. For a pool with 10M/10M reserves:

| Trade Size (HC) | Shares Out | Price Impact |
|-----------------|-----------|--------------|
| 100             | 99.999    | 0.001%       |
| 1,000           | 999.9     | 0.01%        |
| 10,000          | 9,990     | 0.10%        |
| 100,000         | 99,010    | 1.00%        |
| 500,000         | 476,190   | 5.00%        |

The 5% max price move cap means a single trade can move the price at most 5%.

## Key Properties

1. **Shares can never be depleted**: As v_shares → 0, price → ∞. The curve is asymptotic.
2. **k never changes**: Only the ratio v_hc/v_shares shifts with trades.
3. **Real HC vs Virtual HC**: `real_hc` tracks actual user deposits. Virtual reserves are phantom numbers.
4. **Price is path-independent**: The final price depends only on total net flow, not trade sequence.

## Inverse Formulas

How much HC to spend to get exactly `S` shares:
```
hc_needed = (v_hc × S) / (v_shares - S)
```

How many shares to sell to get exactly `H` HC:
```
shares_needed = (v_shares × H) / (v_hc - H)
```

These are useful for "I want exactly X" scenarios.
