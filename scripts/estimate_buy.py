#!/usr/bin/env python3
"""Estimate shares received for a given HC spend on the HoneyComb AMM.

Usage:
    python estimate_buy.py --hc 1000 --v_hc 10000000 --v_shares 10000000
    python estimate_buy.py --hc 5000 --ticker-id 1 --api https://api-staging.open-hive.com
"""
import argparse, json, sys
from decimal import Decimal, getcontext
getcontext().prec = 30


def estimate(hc: Decimal, v_hc: Decimal, v_shares: Decimal):
    k = v_hc * v_shares
    spot = v_hc / v_shares
    new_v_hc = v_hc + hc
    new_v_shares = k / new_v_hc
    shares_out = v_shares - new_v_shares
    exec_price = hc / shares_out
    return {
        "hc_spent": str(hc),
        "shares_received": str(shares_out.quantize(Decimal("0.0001"))),
        "execution_price": str(exec_price.quantize(Decimal("0.000001"))),
        "spot_price": str(spot.quantize(Decimal("0.000001"))),
        "price_impact_pct": str(((exec_price / spot - 1) * 100).quantize(Decimal("0.01"))),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--hc", required=True, help="HC to spend")
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

    print(json.dumps(estimate(Decimal(args.hc), v_hc, v_shares), indent=2))
