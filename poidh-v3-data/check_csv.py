#!/usr/bin/env python3
"""Re-read poidh_v3_wallets.csv as a consumer would and re-check it: exact header, unique checksummed addresses,
totals = sum of chains, per-chain paid == earned, and column sums == summary.json. Exit != 0 on any problem."""
import csv, json, sys
from decimal import Decimal
from eth_utils import is_checksum_address
CH = ["mainnet", "arbitrum", "base"]
HDR = ["wallet_address", "eth_paid_mainnet", "eth_paid_arbitrum", "eth_paid_base", "eth_paid_total", "eth_earned_mainnet", "eth_earned_arbitrum",
       "eth_earned_base", "eth_earned_total", "nfts_held_mainnet", "nfts_held_arbitrum", "nfts_held_base", "nfts_held_total"]
r = list(csv.reader(open("poidh_v3_wallets.csv"))); S = json.load(open("summary.json"))
errs = []
if r[0] != HDR: errs.append("header differs")
rows = [dict(zip(HDR, x)) for x in r[1:]]
if not rows: errs.append("0 rows")
if len({x["wallet_address"].lower() for x in rows}) != len(rows): errs.append("duplicate wallets")
for x in rows:
    if not is_checksum_address(x["wallet_address"]): errs.append("bad address " + x["wallet_address"])
    for k in ("eth_paid", "eth_earned", "nfts_held"):
        conv = int if k == "nfts_held" else Decimal
        if sum(conv(x[f"{k}_{c}"]) for c in CH) != conv(x[f"{k}_total"]): errs.append(f"{x['wallet_address']} {k} total")
W = Decimal(10) ** 18
for c in CH:
    p = sum(Decimal(x[f"eth_paid_{c}"]) for x in rows); e = sum(Decimal(x[f"eth_earned_{c}"]) for x in rows)
    n = sum(int(x[f"nfts_held_{c}"]) for x in rows); s = S["chains"][c]
    ok = p == e == Decimal(s["eth_paid_wei"]) / W and n == s["nfts_in_user_wallets"]
    print(f"{c}: CSV paid {p} earned {e} nfts {n} -> {'OK' if ok else 'MISMATCH'}")
    if not ok: errs.append(c)
tp = sum(Decimal(x["eth_paid_total"]) for x in rows); te = sum(Decimal(x["eth_earned_total"]) for x in rows)
print(f"all: CSV paid {tp} earned {te} rows {len(rows)}"); 
if tp != te or len(rows) != S["overall"]["wallet_rows"]: errs.append("overall")
if errs: print("ERRORS:", errs[:10]); sys.exit(1)
print("CSV OK")
