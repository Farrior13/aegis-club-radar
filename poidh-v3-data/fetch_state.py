#!/usr/bin/env python3
"""Dump poidh v3 contract state at the cutoff block: every bounty, its participants/amounts, every claim, and the
current owner (ownerOf) of every claim NFT id. Read-only eth_call via Multicall3, pinned to the cutoff block. No keys.
Usage: fetch_state.py <mainnet|arbitrum|base>  -> data/<chain>_state.json"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc
from eth_abi import encode, decode
from eth_utils import keccak, to_checksum_address
from config import CHAINS

chain = sys.argv[1]
C, N = CHAINS[chain]["core"], CHAINS[chain]["nft"]
BLOCK = json.load(open("data/cutoff.json"))[chain]["block"]
TAG = hex(BLOCK)
BATCH = {"mainnet": 1, "base": 1, "arbitrum": 4}  # drpc free plan rejects JSON-RPC batches of more than 3
MC3 = "0xcA11bde05977b3631167028862bE2a173976CA11"  # Multicall3, same address on all three chains
def sel(s): return keccak(text=s)[:4]

def calls(to, sig, argtypes, argss, chunk=60):
    """Many view calls via Multicall3.aggregate3(allowFailure=true) at the pinned block; failed sub-calls -> None."""
    res = []
    datas = [sel(sig) + encode(argtypes, a) for a in argss]
    reqs = []
    for s in range(0, len(datas), chunk):
        cd = "0x" + (sel("aggregate3((address,bool,bytes)[])") + encode(["(address,bool,bytes)[]"], [[(to, True, d) for d in datas[s:s + chunk]]])).hex()
        reqs.append(("eth_call", [{"to": MC3, "data": cd}, TAG]))
    for r in rpc.batch(chain, reqs, size=BATCH[chain]):
        assert r is not None, "multicall reverted"
        for ok, data in decode(["(bool,bytes)[]"], bytes.fromhex(r[2:]))[0]:
            res.append(data if ok else None)
    print(chain, sig, len(res), "/", len(argss), file=sys.stderr, flush=True)
    assert len(res) == len(argss)
    return res

def one(to, sig, out):
    return decode(out, calls(to, sig, [], [[]])[0])[0]

nb = one(C, "bountyCounter()", ["uint256"]); nc = one(C, "claimCounter()", ["uint256"])
assert one(C, "getBountiesLength()", ["uint256"]) == nb
assert one(N, "poidh()", ["address"]).lower() == C.lower(), "NFT minter is not this core contract"
assert one(C, "poidhNft()", ["address"]).lower() == N.lower(), "core points at another NFT"
treasury = one(C, "treasury()", ["address"])
fee_bps = one(C, "FEE_BPS()", ["uint256"])
print(chain, "block", BLOCK, "bounties", nb, "claimCounter", nc, file=sys.stderr)

BT = ["uint256", "address", "string", "string", "uint256", "address", "uint256", "uint256"]
bounties = []
for i, r in enumerate(calls(C, "bounties(uint256)", ["uint256"], [[i] for i in range(nb)], chunk=25)):
    v = decode(BT, r)
    assert v[0] == i
    bounties.append({"id": i, "issuer": v[1].lower(), "name": v[2][:100], "amount": str(v[4]), "claimer": v[5].lower(),
                     "createdAt": v[6], "claimId": v[7]})
for i, r in enumerate(calls(C, "getParticipants(uint256)", ["uint256"], [[i] for i in range(nb)])):
    ps, am = decode(["address[]", "uint256[]"], r)
    bounties[i]["participants"] = [[p.lower(), str(a)] for p, a in zip(ps, am)]
for i, r in enumerate(calls(C, "everHadExternalContributor(uint256)", ["uint256"], [[i] for i in range(nb)])):
    bounties[i]["everHadExternalContributor"] = decode(["bool"], r)[0]

CT = ["uint256", "address", "uint256", "address", "string", "string", "uint256", "bool"]
claims = []
for i, r in enumerate(calls(C, "claims(uint256)", ["uint256"], [[i] for i in range(nc)], chunk=25)):
    v = decode(CT, r)
    claims.append({"id": v[0], "issuer": v[1].lower(), "bountyId": v[2], "bountyIssuer": v[3].lower(), "accepted": v[7]})
start = next(c["id"] for c in claims if c["issuer"] != "0x0000000000000000000000000000000000000000")
assert all(c["id"] == i for i, c in enumerate(claims))
assert all(c["issuer"] == "0x0000000000000000000000000000000000000000" for c in claims[:start])
owners = {}
ids = list(range(start, nc))
for t, r in zip(ids, calls(N, "ownerOf(uint256)", ["uint256"], [[t] for t in ids])):
    owners[str(t)] = decode(["address"], r)[0].lower() if r is not None else None
# ids just outside the range must not exist (proves the id range is complete)
probe = calls(N, "ownerOf(uint256)", ["uint256"], [[start - 1], [nc], [nc + 1]])
assert all(p is None for p in probe), "token exists outside [start, claimCounter)"
holders = sorted({o for o in owners.values() if o})
bal = {h: decode(["uint256"], r)[0] for h, r in zip(holders, calls(N, "balanceOf(address)", ["address"], [[h] for h in holders]))}
blk = rpc.call(chain, "eth_getBlockByNumber", [TAG, False])
json.dump({"chain": chain, "core": C, "nft": N, "block": BLOCK, "block_time": int(blk["timestamp"], 16), "treasury": treasury.lower(),
           "fee_bps": fee_bps, "bountyCounter": nb, "claimCounter": nc, "startClaimIndex": start, "bounties": bounties,
           "claims": claims, "owners": owners, "balanceOf": {h: v for h, v in bal.items()}}, open(f"data/{chain}_state.json", "w"))
print("wrote", chain, file=sys.stderr)
