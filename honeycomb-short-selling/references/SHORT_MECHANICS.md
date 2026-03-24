# Short Position Mechanics — Full Math

## Opening a Short

Given collateral `C` HC and spot price `P = v_hc / v_shares`:

```
shares = C / P                          (1x leverage)
new_v_shares = v_shares + shares
new_v_hc = k / new_v_shares
hc_extracted = v_hc - new_v_hc          (what the virtual sell got from the AMM)
stored_collateral = hc_extracted         (NOT the user's input C — they differ by slippage)
```

The stored collateral equals `hc_extracted` so that a solo round-trip (open then immediately close on an unchanged pool) yields PnL = 0.

## Closing a Short

```
new_v_shares = v_shares - shares         (remove shares from pool)
new_v_hc = k / new_v_shares
buyback_cost = new_v_hc - v_hc           (HC needed to buy back shares)
pnl = stored_collateral - buyback_cost
returned_hc = max(0, stored_collateral + pnl)
             = max(0, 2 * stored_collateral - buyback_cost)
```

- If price dropped since open: `buyback_cost < stored_collateral` → positive PnL
- If price rose: `buyback_cost > stored_collateral` → negative PnL
- Max loss: `returned_hc = 0` when `buyback_cost >= 2 * stored_collateral`

## Liquidation Price

```
liq_price = entry_price × (1 + (1 - maintenance_margin) / leverage)
```

With default 1x leverage and 20% maintenance margin:
```
liq_price = entry_price × (1 + 0.8 / 1) = entry_price × 1.8
```

The position is liquidated when the pool spot price reaches `liq_price`. A 1% fee is deducted.

## Position Health

```
buyback_cost = k / (v_shares - shares) - v_hc
equity = stored_collateral - buyback_cost
health_pct = (equity / stored_collateral) × 100
```

- health > 50%: Safe
- health 20-50%: Caution
- health ≤ 20%: Near liquidation
- health ≤ 0%: Liquidated

## Partial Close

For closing `S` shares out of total `T`:

```
fraction = S / T
partial_collateral = stored_collateral × fraction
partial_buyback = k / (v_shares - S) - v_hc
partial_pnl = partial_collateral - partial_buyback
partial_return = max(0, partial_collateral + partial_pnl)
```

The remaining position has `T - S` shares and `stored_collateral - partial_collateral` collateral.
