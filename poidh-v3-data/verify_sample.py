#!/usr/bin/env python3
"""Independent spot check: for a sample of completed bounties per chain (always including a solo bounty, an open bounty
with a contributor who withdrew, and a vote-resolved bounty when they exist), re-fetch every related transaction and its
receipt by hash from RPC (not from the bulk log download), decode the receipt logs, check that the ETH sent with each
create/join transaction equals the logged amount, rebuild the contributions and gross amount, and compare with
completed_bounties.csv / the CSV credits. Writes sample_checks.json. Exit != 0 on any mismatch."""
import csv, json, os, sys, random
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc
from eth_abi import decode
from eth_utils import keccak
from config import CHAINS

random.seed(1540)
rpc.RPCS["base"] = ["https://base.gateway.tenderly.co", "https://mainnet.base.org", "https://base.drpc.org"]
K = lambda s: "0x" + keccak(text=s).hex()
EV = {K("BountyCreated(uint256,address,string,string,uint256,uint256,bool,uint256)"): "created",
      K("BountyJoined(uint256,address,uint256,uint256,uint256)"): "joined",
      K("WithdrawFromOpenBounty(uint256,address,uint256,uint256,uint256)"): "withdrew",
      K("ClaimAccepted(uint256,uint256,address,address,uint256,uint256,uint256,uint256)"): "accepted"}
per = list(csv.DictReader(open("completed_bounties.csv")))
out, bad = {}, []
for chain in (sys.argv[1:] or ["mainnet", "arbitrum", "base"]):
    core = CHAINS[chain]["core"].lower()
    L = json.load(open(f"data/{chain}_logs.json"))
    txs_by_bounty = defaultdict(set)
    for l in L["core"]:
        if l["topics"][0] in EV:
            txs_by_bounty[int(l["topics"][1], 16)].add(l["transactionHash"])
    withdrew = {int(l["topics"][1], 16) for l in L["core"] if l["topics"][0] == K("WithdrawFromOpenBounty(uint256,address,uint256,uint256,uint256)")}
    rows = [r for r in per if r["chain"] == chain]
    pick = []
    def add(cands, why):
        cands = [r for r in cands if r not in [p for p, _ in pick]]
        if cands: pick.append((cands[0], why))
    add([r for r in rows if r["type"] == "solo"], "solo bounty")
    add([r for r in rows if r["type"] == "open" and int(r["bounty_id"]) in withdrew], "open bounty with a withdrawn contributor")
    add([r for r in rows if r["via"].startswith("vote")], "accepted by contributor vote")
    add(sorted(rows, key=lambda r: -float(r["gross_eth"])), "largest completed bounty on the chain")
    add(sorted(rows, key=lambda r: -int(r["contributors"])), "most contributors")
    while len(pick) < 6 and len(pick) < len(rows):
        add(random.sample(rows, len(rows)), "random")
    res = []
    for r, why in pick:
        bid = int(r["bounty_id"])
        contrib = defaultdict(int); gross = None; winner = None; notes = []; txl = []
        fetched = []
        for h in txs_by_bounty[bid]:
            tx = rpc.call(chain, "eth_getTransactionByHash", [h]); rc = rpc.call(chain, "eth_getTransactionReceipt", [h])
            assert rc["status"] == "0x1" and rc["transactionHash"] == h
            fetched.append((int(rc["blockNumber"], 16), int(rc["transactionIndex"], 16), h, tx, rc))
        for _, _, h, tx, rc in sorted(fetched):  # chronological replay
            val = int(tx["value"], 16); kinds = []
            for l in rc["logs"]:
                if l["address"].lower() != core or l["topics"][0] not in EV or int(l["topics"][1], 16) != bid: continue
                k = EV[l["topics"][0]]; kinds.append(k)
                who = "0x" + l["topics"][2][-40:]
                if k == "created":
                    amt = decode(["string", "string", "uint256", "uint256", "bool", "uint256"], bytes.fromhex(l["data"][2:]))[2]
                    contrib[who] += amt
                    if tx["to"] and tx["to"].lower() == core and val != amt: notes.append(f"create tx value {val} != {amt}")
                elif k == "joined":
                    amt = decode(["uint256"] * 3, bytes.fromhex(l["data"][2:]))[0]
                    contrib[who] += amt
                    if tx["to"] and tx["to"].lower() == core and val != amt: notes.append(f"join tx value {val} != {amt}")
                elif k == "withdrew":
                    contrib[who] = 0
                elif k == "accepted":
                    d = decode(["address", "uint256", "uint256", "uint256", "uint256"], bytes.fromhex(l["data"][2:]))
                    gross = d[1]; winner = "0x" + l["topics"][3][-40:]
            txl.append({"tx": h, "events": kinds, "tx_value_wei": str(val), "from": tx["from"].lower(), "to": (tx["to"] or "").lower()})
        s = sum(contrib.values())
        ok = (gross is not None and s == gross and str(winner) == r["winner"]
              and r["gross_eth"] == r["sum_contributions_eth"] and abs(float(r["gross_eth"]) - gross / 1e18) < 1e-12 and not notes)
        if not ok: bad.append((chain, bid, notes))
        res.append({"bounty_id": bid, "why": why, "type": r["type"], "via": r["via"], "gross_wei": str(gross), "winner": winner,
                    "contributions_wei": {w: str(a) for w, a in contrib.items() if a}, "withdrawn_contributors": [w for w, a in contrib.items() if not a],
                    "txs": txl, "matches_dataset": ok, "notes": notes})
        print(chain, bid, why, "gross", gross, "contributors", len([a for a in contrib.values() if a]), "OK" if ok else "MISMATCH", flush=True)
    out[chain] = res
json.dump(out, open("sample_checks.json", "w"), indent=1)
if bad:
    print("MISMATCHES:", bad); sys.exit(1)
print("sample checks: all", sum(len(v) for v in out.values()), "bounties match")
