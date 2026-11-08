#!/usr/bin/env python3
"""Build the consolidated poidh v3 wallet CSV from data/<chain>_logs.json (events) + data/<chain>_state.json (state at
the cutoff block), with every reconciliation asserted. Exit code != 0 if any check fails.
Usage: build.py [--drop-join N]   (--drop-join: positive control, deletes the N-th BountyJoined log of the first chain
                                    that has one, which must make the reconciliation fail)"""
import csv, json, os, sys
from collections import defaultdict, Counter
from decimal import Decimal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eth_abi import decode
from eth_utils import keccak, to_checksum_address
from config import CHAINS, CUTOFF_TS

ZERO = "0x" + "0" * 40
CH = ["mainnet", "arbitrum", "base"]
SIGS = {
    "BountyCreated": ("BountyCreated(uint256,address,string,string,uint256,uint256,bool,uint256)", ["string", "string", "uint256", "uint256", "bool", "uint256"]),
    "ClaimCreated": ("ClaimCreated(uint256,address,uint256,address,string,string,uint256,string,uint256)", ["address", "string", "string", "uint256", "string", "uint256"]),
    "ClaimAccepted": ("ClaimAccepted(uint256,uint256,address,address,uint256,uint256,uint256,uint256)", ["address", "uint256", "uint256", "uint256", "uint256"]),
    "BountyJoined": ("BountyJoined(uint256,address,uint256,uint256,uint256)", ["uint256", "uint256", "uint256"]),
    "BountyCancelled": ("BountyCancelled(uint256,address,uint256,uint256)", ["uint256", "uint256"]),
    "WithdrawFromOpenBounty": ("WithdrawFromOpenBounty(uint256,address,uint256,uint256,uint256)", ["uint256", "uint256", "uint256"]),
    "Withdrawal": ("Withdrawal(address,uint256)", ["uint256"]),
    "WithdrawalTo": ("WithdrawalTo(address,address,uint256)", ["uint256"]),
    "VotingStarted": ("VotingStarted(uint256,uint256,uint256,uint256,uint256)", ["uint256", "uint256", "uint256"]),
    "VoteCast": ("VoteCast(address,uint256,uint256,bool,uint256,uint256)", ["bool", "uint256", "uint256"]),
    "VotingResolved": ("VotingResolved(uint256,uint256,bool,uint256,uint256,uint256)", ["bool", "uint256", "uint256", "uint256"]),
    "RefundClaimed": ("RefundClaimed(uint256,address,uint256,uint256)", ["uint256", "uint256"]),
}
T0 = {"0x" + keccak(text=s).hex(): (name, types) for name, (s, types) in SIGS.items()}
TRANSFER = "0x" + keccak(text="Transfer(address,address,uint256)").hex()
WEI = Decimal(10) ** 18

failures = []
def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("CHECK FAILED:", msg, file=sys.stderr)
    return cond

def topic_int(t): return int(t, 16)
def topic_addr(t): return "0x" + t[-40:].lower()

def eth(w):  # exact decimal string from integer wei
    if w == 0: return "0"
    s = format(Decimal(w) / WEI, "f")
    return s.rstrip("0").rstrip(".") if "." in s else s

drop = int(sys.argv[sys.argv.index("--drop-join") + 1]) if "--drop-join" in sys.argv else None
OUT = "out_control" if drop is not None else "."
os.makedirs(OUT, exist_ok=True)

paid = defaultdict(lambda: defaultdict(int))      # wallet -> chain -> wei
earned = defaultdict(lambda: defaultdict(int))
nfts = defaultdict(lambda: defaultdict(int))
funded_n = defaultdict(lambda: defaultdict(int)); won_n = defaultdict(lambda: defaultdict(int))
claims_n = defaultdict(lambda: defaultdict(int)); created_n = defaultdict(lambda: defaultdict(int))
known = set()  # every issuer / contributor / claimant / winner / NFT holder
protocol_rows = []
summary = {"cutoff_utc": "2026-11-08T03:59:54Z", "cutoff_unix": CUTOFF_TS, "chains": {}}
per_bounty = []

for chain in CH:
    lp, sp = f"data/{chain}_logs.json", f"data/{chain}_state.json"
    if not (os.path.exists(lp) and os.path.exists(sp)):
        check(False, f"{chain}: missing {lp} or {sp}"); continue
    L, S = json.load(open(lp)), json.load(open(sp))
    cfg = CHAINS[chain]; core, nftc = cfg["core"].lower(), cfg["nft"].lower()
    check(L["to_block"] == S["block"], f"{chain}: logs end block {L['to_block']} != state block {S['block']}")
    PROTOCOL = {core: "poidh v3 core contract (claim NFT escrow)", nftc: "poidh v3 NFT contract", ZERO: "zero address"}
    ev = []
    joins_seen = 0
    for l in L["core"]:
        assert l["address"].lower() == core
        t0 = l["topics"][0]
        if t0 not in T0:
            check(False, f"{chain}: unknown event topic {t0} in tx {l['transactionHash']}"); continue
        name, types = T0[t0]
        if name == "BountyJoined" and drop is not None and not summary.get("control_dropped"):
            if joins_seen == drop:
                summary["control_dropped"] = {"chain": chain, "tx": l["transactionHash"]}
                print("POSITIVE CONTROL: dropped BountyJoined", chain, l["transactionHash"], file=sys.stderr)
                continue
            joins_seen += 1
        ev.append((name, l["topics"][1:], decode(types, bytes.fromhex(l["data"][2:])), l))
    cnt = Counter(e[0] for e in ev)
    nb, B = S["bountyCounter"], S["bounties"]

    contrib = defaultdict(lambda: defaultdict(int))  # bounty -> wallet -> wei (live, replayed)
    is_open, status, accepted = {}, {}, {}
    tx_accept = {}
    vote_pass_tx = set()
    for name, top, d, l in ev:
        if name == "VotingResolved" and d[0]:
            vote_pass_tx.add((l["transactionHash"], topic_int(top[0])))
    for name, top, d, l in ev:
        if name == "BountyCreated":
            bid, iss = topic_int(top[0]), topic_addr(top[1])
            check(bid not in is_open, f"{chain}: bounty {bid} created twice")
            is_open[bid] = d[4]; status[bid] = "active"; contrib[bid][iss] += d[2]; known.add(iss); created_n[iss][chain] += 1
        elif name == "BountyJoined":
            bid, p = topic_int(top[0]), topic_addr(top[1])
            contrib[bid][p] += d[0]; known.add(p)
            check(sum(contrib[bid].values()) == d[1], f"{chain}: bounty {bid} balance after join {sum(contrib[bid].values())} != event {d[1]} (tx {l['transactionHash']})")
        elif name == "WithdrawFromOpenBounty":
            bid, p = topic_int(top[0]), topic_addr(top[1])
            check(contrib[bid][p] == d[0], f"{chain}: bounty {bid} withdraw by {p} {d[0]} != replayed {contrib[bid][p]} (tx {l['transactionHash']})")
            contrib[bid][p] = 0
            check(sum(contrib[bid].values()) == d[1], f"{chain}: bounty {bid} balance after withdraw mismatch (tx {l['transactionHash']})")
        elif name == "BountyCancelled":
            bid, iss = topic_int(top[0]), topic_addr(top[1])
            status[bid] = "cancelled"
            check(contrib[bid][iss] == d[0], f"{chain}: bounty {bid} cancel refund {d[0]} != issuer stake {contrib[bid][iss]}")
            contrib[bid][iss] = 0
        elif name == "RefundClaimed":
            bid, p = topic_int(top[0]), topic_addr(top[1])
            check(status.get(bid) == "cancelled", f"{chain}: refund on non-cancelled bounty {bid}")
            check(contrib[bid][p] == d[0], f"{chain}: bounty {bid} refund {d[0]} != replayed {contrib[bid][p]}")
            contrib[bid][p] = 0
        elif name == "ClaimCreated":
            known.add(topic_addr(top[1])); claims_n[topic_addr(top[1])][chain] += 1
        elif name == "ClaimAccepted":
            bid, cid, winner = topic_int(top[0]), topic_int(top[1]), topic_addr(top[2])
            biss, gross, payout, fee = d[0].lower(), d[1], d[2], d[3]
            check(status.get(bid) == "active", f"{chain}: bounty {bid} accepted while {status.get(bid)}")
            status[bid] = "completed"
            check(payout + fee == gross and fee == gross * 250 // 10000, f"{chain}: bounty {bid} payout+fee != gross")
            shares = {w: a for w, a in contrib[bid].items() if a > 0}
            ok = check(sum(shares.values()) == gross, f"{chain}: bounty {bid}: contributions {sum(shares.values())} != gross {gross}")
            via = "vote (resolveVote)" if (l["transactionHash"], bid) in vote_pass_tx else "acceptClaim (issuer)"
            accepted[bid] = {"bounty_id": bid, "claim_id": cid, "winner": winner, "issuer": biss, "gross_wei": gross, "payout_wei": payout,
                             "fee_wei": fee, "type": "open" if is_open[bid] else "solo", "contributors": len(shares), "via": via,
                             "tx": l["transactionHash"], "block": int(l["blockNumber"], 16), "reconciled": ok, "shares": shares}
            for w, a in shares.items():
                paid[w][chain] += a; funded_n[w][chain] += 1
            earned[winner][chain] += gross; won_n[winner][chain] += 1; known.add(winner)
    # ---- state cross-checks (state at the cutoff block, independent of the event replay)
    check(cnt["BountyCreated"] == nb, f"{chain}: BountyCreated {cnt['BountyCreated']} != bountyCounter {nb}")
    check(cnt["ClaimCreated"] == S["claimCounter"] - S["startClaimIndex"], f"{chain}: ClaimCreated count != claimCounter-start")
    st_completed = {b["id"] for b in B if b["claimer"] not in (ZERO, b["issuer"])}
    st_cancelled = {b["id"] for b in B if b["claimer"] == b["issuer"]}
    check(st_completed == set(accepted), f"{chain}: completed set (state) != ClaimAccepted set: {sorted(st_completed ^ set(accepted))[:10]}")
    check(st_cancelled == {b for b, s in status.items() if s == "cancelled"}, f"{chain}: cancelled set mismatch")
    for b in B:
        bid = b["id"]
        if bid in accepted:
            a = accepted[bid]
            check(b["claimer"] == a["winner"] and b["claimId"] == a["claim_id"] and b["amount"] == "0", f"{chain}: bounty {bid} state vs event winner/claim mismatch")
            c = S["claims"][a["claim_id"]]
            check(c["accepted"] and c["issuer"] == a["winner"] and c["bountyId"] == bid, f"{chain}: claim {a['claim_id']} state mismatch")
            if a["type"] == "open":
                st_sh = {p: int(x) for p, x in b["participants"] if int(x) > 0}
                check(st_sh == a["shares"], f"{chain}: bounty {bid}: state participantAmounts != replayed contributions")
            else:
                check(b["participants"] == [], f"{chain}: solo bounty {bid} has participants in state")
        elif status.get(bid) == "active":
            check(int(b["amount"]) == sum(contrib[bid].values()), f"{chain}: active bounty {bid} amount {b['amount']} != replayed {sum(contrib[bid].values())}")
        check(is_open.get(bid) == (len(b["participants"]) > 0), f"{chain}: bounty {bid} open/solo flag mismatch")
        known.add(b["issuer"])
    for c in S["claims"][S["startClaimIndex"]:]:
        known.add(c["issuer"])
    # ---- NFTs: Transfer replay vs ownerOf at the cutoff block for every token id
    owner = {}; mints = burns = 0
    for l in L["nft"]:
        assert l["topics"][0] == TRANSFER and l["address"].lower() == nftc
        f, t, tid = topic_addr(l["topics"][1]), topic_addr(l["topics"][2]), topic_int(l["topics"][3])
        if f == ZERO:
            mints += 1; check(t == core, f"{chain}: token {tid} minted to {t}, not the core contract")
        else:
            check(owner.get(tid) == f, f"{chain}: token {tid} transferred from non-owner")
        if t == ZERO: burns += 1
        owner[tid] = t
    so = {int(k): v for k, v in S["owners"].items()}
    check(set(owner) == set(so), f"{chain}: token id set from Transfers != ids [start, claimCounter)")
    mism = [t for t in so if so[t] != owner.get(t)]
    check(not mism, f"{chain}: {len(mism)} tokens where Transfer replay != ownerOf, e.g. {mism[:5]}")
    check(mints == len(so) and burns == 0 and None not in so.values(), f"{chain}: minted {mints} vs tokens {len(so)}, burns {burns}")
    hold = Counter(so.values())
    for h, n in hold.items():
        check(S["balanceOf"][h] == n, f"{chain}: balanceOf({h}) {S['balanceOf'][h]} != counted {n}")
    proto = {h: n for h, n in hold.items() if h in PROTOCOL}
    for h, n in hold.items():
        if h in PROTOCOL: protocol_rows.append({"chain": chain, "address": h, "label": PROTOCOL[h], "nfts_held": n})
        else: nfts[h][chain] += n; known.add(h)
    # accepted claim NFTs go to the bounty issuer; escrowed = claims never accepted
    escrow_expected = len(so) - len(accepted)
    check(proto.get(core, 0) <= escrow_expected, f"{chain}: escrow holds more NFTs than unaccepted claims")
    tot_paid = sum(paid[w][chain] for w in paid); tot_earned = sum(earned[w][chain] for w in earned)
    gross = sum(a["gross_wei"] for a in accepted.values())
    check(tot_paid == tot_earned == gross, f"{chain}: paid {tot_paid} / earned {tot_earned} / gross {gross} do not reconcile")
    nonrec = [a["bounty_id"] for a in accepted.values() if not a["reconciled"]]
    summary["chains"][chain] = {
        "core": core, "nft": nftc, "cutoff_block": S["block"], "cutoff_block_time_unix": S["block_time"],
        "log_source": L.get("source", "eth_getLogs (public JSON-RPC)"), "logs_from_block": L["from_block"],
        "core_events": dict(cnt), "bounties": nb, "solo_bounties": sum(1 for v in is_open.values() if not v), "open_bounties": sum(1 for v in is_open.values() if v),
        "completed": len(accepted), "completed_solo": sum(1 for a in accepted.values() if a["type"] == "solo"),
        "completed_open": sum(1 for a in accepted.values() if a["type"] == "open"),
        "completed_via_vote": sum(1 for a in accepted.values() if a["via"].startswith("vote")),
        "cancelled": len(st_cancelled), "active_at_cutoff": sum(1 for s in status.values() if s == "active"),
        "eth_paid_wei": str(tot_paid), "eth_earned_wei": str(tot_earned), "eth_paid": eth(tot_paid), "eth_earned": eth(tot_earned),
        "protocol_fee_eth": eth(sum(a["fee_wei"] for a in accepted.values())), "net_payout_eth": eth(sum(a["payout_wei"] for a in accepted.values())),
        "reconciled": tot_paid == tot_earned == gross and not nonrec, "bounties_not_reconciled": nonrec,
        "claims": S["claimCounter"] - S["startClaimIndex"], "nfts_minted": mints, "nfts_burned": burns,
        "nfts_in_user_wallets": sum(n for h, n in hold.items() if h not in PROTOCOL), "nfts_held_by_protocol": proto,
        "treasury": S["treasury"],
    }
    for a in sorted(accepted.values(), key=lambda a: a["bounty_id"]):
        per_bounty.append({"chain": chain, **{k: v for k, v in a.items() if k != "shares"},
                           "gross_eth": eth(a["gross_wei"]), "sum_contributions_eth": eth(sum(a["shares"].values()))})

# ---- consolidate
protocol_addrs = {r["address"] for r in protocol_rows} | {CHAINS[c]["core"].lower() for c in CH} | {CHAINS[c]["nft"].lower() for c in CH} | {ZERO}
wallets = sorted(w for w in known if w not in protocol_addrs)
cols = ["wallet_address"] + [f"eth_paid_{c}" for c in CH] + ["eth_paid_total"] + [f"eth_earned_{c}" for c in CH] + ["eth_earned_total"] + \
       [f"nfts_held_{c}" for c in CH] + ["nfts_held_total"]
rows = []
for w in wallets:
    r = {"wallet_address": w}
    for k, src in (("eth_paid", paid), ("eth_earned", earned)):
        for c in CH: r[f"{k}_{c}"] = src[w][c]
        r[f"{k}_total"] = sum(src[w][c] for c in CH)
    for c in CH: r[f"nfts_held_{c}"] = nfts[w][c]
    r["nfts_held_total"] = sum(nfts[w][c] for c in CH)
    rows.append(r)
rows.sort(key=lambda r: (-r["eth_paid_total"] - r["eth_earned_total"], -r["nfts_held_total"], r["wallet_address"]))
tot = {c: sum(r[c] for r in rows) for c in cols[1:]}
for k in ("eth_paid", "eth_earned"):
    check(tot[f"{k}_total"] == sum(tot[f"{k}_{c}"] for c in CH), f"{k} total != sum of chains")
check(tot["eth_paid_total"] == tot["eth_earned_total"], "overall paid != earned")
check(len(rows) == len({r["wallet_address"] for r in rows}), "duplicate wallet rows")
with open(f"{OUT}/poidh_v3_wallets.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(cols)
    for r in rows:
        wr.writerow([to_checksum_address(r["wallet_address"])] + [eth(r[c]) if c.startswith("eth_") else r[c] for c in cols[1:]])
with open(f"{OUT}/poidh_v3_wallets_detail.csv", "w", newline="") as f:
    dc = ["wallet_address"] + [f"{k}_{c}" for k in ("bounties_created", "bounties_funded_completed", "bounties_won", "claims_submitted") for c in CH]
    wr = csv.writer(f); wr.writerow(dc)
    for r in rows:
        w = r["wallet_address"]
        wr.writerow([to_checksum_address(w)] + [src[w][c] for src in (created_n, funded_n, won_n, claims_n) for c in CH])
with open(f"{OUT}/poidh_v3_protocol_nft_holdings.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["chain", "address", "label", "nfts_held"])
    for r in protocol_rows: wr.writerow([r["chain"], to_checksum_address(r["address"]), r["label"], r["nfts_held"]])
with open(f"{OUT}/completed_bounties.csv", "w", newline="") as f:
    pc = ["chain", "bounty_id", "type", "via", "claim_id", "issuer", "winner", "contributors", "gross_eth", "sum_contributions_eth", "reconciled", "block", "tx"]
    wr = csv.writer(f); wr.writerow(pc)
    for p in per_bounty: wr.writerow([p[c] for c in pc])
summary["overall"] = {"wallet_rows": len(rows), "eth_paid": eth(tot["eth_paid_total"]), "eth_earned": eth(tot["eth_earned_total"]),
                      "eth_paid_wei": str(tot["eth_paid_total"]), "eth_earned_wei": str(tot["eth_earned_total"]),
                      "reconciled": tot["eth_paid_total"] == tot["eth_earned_total"] and not failures,
                      "nfts_in_user_wallets": tot["nfts_held_total"], "nfts_held_by_protocol": sum(r["nfts_held"] for r in protocol_rows),
                      "completed_bounties": len(per_bounty),
                      "wallets_with_paid": sum(1 for r in rows if r["eth_paid_total"]), "wallets_with_earned": sum(1 for r in rows if r["eth_earned_total"]),
                      "wallets_with_nfts": sum(1 for r in rows if r["nfts_held_total"]),
                      "wallets_all_zero": sum(1 for r in rows if not (r["eth_paid_total"] or r["eth_earned_total"] or r["nfts_held_total"]))}
summary["checks_failed"] = failures
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1)
print(json.dumps(summary["overall"], indent=1))
for c, s in summary["chains"].items():
    print(c, "block", s["cutoff_block"], "completed", s["completed"], "paid", s["eth_paid"], "earned", s["eth_earned"], "reconciled", s["reconciled"],
          "nfts users", s["nfts_in_user_wallets"], "protocol", s["nfts_held_by_protocol"])
if failures:
    print(f"FAILED: {len(failures)} checks", file=sys.stderr); sys.exit(1)
print("ALL CHECKS PASSED")
