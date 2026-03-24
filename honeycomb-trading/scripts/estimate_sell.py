#!/usr/bin/env python3
"""Estimate HC received for selling shares on the HoneyComb AMM.

Usage:
    python estimate_sell.py --shares 500 --v_hc 10000000 --v_shares 10000000
    python estimate_sell.py --shares 500 --ticker-id 1 --api https://api-staging.open-hive.com
"""
import argparse, json
from decimal import Decimal, getcontext
getcontext().prec = 30


def estimate(shares: Decimal, v_hc: Decimal, v_shares: Decimal):
    k = v_hc * v_shares
    spot = v_hc / v_shares
    new_v_shares = v_shares + shares
    new_v_hc = k / new_v_shares
    hc_out = v_hc - new_v_hc
    exec_price = hc_out / shares
    return {
        "shares_sold": str(shares),
        "hc_received": str(hc_out.quantize(Decimal("0.0001"))),
        "execution_price": str(exec_price.quantize(Decimal("0.000001"))),
        "spot_price": str(spot.quantize(Decimal("0.000001"))),
        "price_impact_pct": str(((1 - exec_price / spot) * 100).quantize(Decimal("0.01"))),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--shares", required=True, help="Shares to sell")
    p.add_argument("--v_hc", help="Virtual HC reserve")
    p.add_argument("--v_shares", help="Virtual share reserve")
    p.add_argument("--ticker-id", type=int, help="Fetch pool state from API")
    p.add_argument("--api", default="https://api-staging.open-hive.com")
    args = p.parse_args()

    if args.ticker_id:
        import urllib.request
        data = json.loads(urllib.request.urlopen(f"{args.api}/api/ticker/{args.ticker_id}").read())
        v_hc, v_shares = Decimal(data["v_hc"]), Decimal(data["v_shares"])
    elif args.v_hc and args.v_shares:
        v_hc, v_shares = Decimal(args.v_hc), Decimal(args.v_shares)
    else:
        p.error("Provide --v_hc/--v_shares or --ticker-id")

    print(json.dumps(estimate(Decimal(args.shares), v_hc, v_shares), indent=2))
