#!/usr/bin/env python3
"""Estimate price impact for a HoneyComb AMM trade.

Usage:
    python price_impact.py buy  --hc 1000 --v_hc 10000000 --v_shares 10000000
    python price_impact.py sell --shares 500 --v_hc 10000000 --v_shares 10000000
"""
import argparse
from decimal import Decimal, getcontext

getcontext().prec = 30


def estimate_buy(hc_amount: Decimal, v_hc: Decimal, v_shares: Decimal) -> dict:
    k = v_hc * v_shares
    spot = v_hc / v_shares
    new_v_hc = v_hc + hc_amount
    new_v_shares = k / new_v_hc
    shares_out = v_shares - new_v_shares
    exec_price = hc_amount / shares_out
    new_price = new_v_hc / new_v_shares
    impact = (exec_price / spot - 1) * 100
    return {
        "side": "BUY",
        "hc_spent": float(hc_amount),
        "shares_received": float(shares_out.quantize(Decimal("0.0001"))),
        "execution_price": float(exec_price.quantize(Decimal("0.000001"))),
        "spot_before": float(spot.quantize(Decimal("0.000001"))),
        "spot_after": float(new_price.quantize(Decimal("0.000001"))),
        "price_impact_pct": float(impact.quantize(Decimal("0.01"))),
    }


def estimate_sell(share_amount: Decimal, v_hc: Decimal, v_shares: Decimal) -> dict:
    k = v_hc * v_shares
    spot = v_hc / v_shares
    new_v_shares = v_shares + share_amount
    new_v_hc = k / new_v_shares
    hc_out = v_hc - new_v_hc
    exec_price = hc_out / share_amount
    new_price = new_v_hc / new_v_shares
    impact = (1 - exec_price / spot) * 100
    return {
        "side": "SELL",
        "shares_sold": float(share_amount),
        "hc_received": float(hc_out.quantize(Decimal("0.0001"))),
        "execution_price": float(exec_price.quantize(Decimal("0.000001"))),
        "spot_before": float(spot.quantize(Decimal("0.000001"))),
        "spot_after": float(new_price.quantize(Decimal("0.000001"))),
        "price_impact_pct": float(impact.quantize(Decimal("0.01"))),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HoneyComb AMM price impact estimator")
    parser.add_argument("side", choices=["buy", "sell"])
    parser.add_argument("--hc", type=str, help="HC amount to spend (buy)")
    parser.add_argument("--shares", type=str, help="Shares to sell (sell)")
    parser.add_argument("--v_hc", type=str, required=True, help="Pool virtual HC reserve")
    parser.add_argument("--v_shares", type=str, required=True, help="Pool virtual share reserve")
    args = parser.parse_args()

    v_hc = Decimal(args.v_hc)
    v_shares = Decimal(args.v_shares)

    if args.side == "buy":
        if not args.hc:
            parser.error("--hc required for buy")
        result = estimate_buy(Decimal(args.hc), v_hc, v_shares)
    else:
        if not args.shares:
            parser.error("--shares required for sell")
        result = estimate_sell(Decimal(args.shares), v_hc, v_shares)

    import json
    print(json.dumps(result, indent=2))
