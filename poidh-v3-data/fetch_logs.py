#!/usr/bin/env python3
"""Download every log emitted by the poidh v3 core contract and every ERC-721 Transfer of the v3 NFT contract,
from the deploy block to the cutoff block (inclusive), via keyless public JSON-RPC eth_getLogs in fixed windows.
Usage: fetch_logs.py <chain> [--rpc URL --span N --threads T]
  arbitrum: https://arb1.arbitrum.io/rpc accepts 400k-block windows (default).
  base:     no free endpoint serves wide historical getLogs; https://base.gateway.tenderly.co serves 1,000-block windows
            (~13.6k requests, run with --threads 6), or use fetch_logs_blockscout.py.
Writes data/<chain>_logs.json; resumable via data/<chain>_logs.windows.json (finished windows are kept)."""
import json, os, sys, time, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CHAINS, SPAN

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
chain = sys.argv[1]
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
DEFAULT_RPC = {"arbitrum": "https://arb1.arbitrum.io/rpc", "base": "https://base.gateway.tenderly.co", "mainnet": "https://mainnet.gateway.tenderly.co"}
URL = arg("--rpc", DEFAULT_RPC[chain]); span = int(arg("--span", SPAN[chain])); threads = int(arg("--threads", 1))
cfg = CHAINS[chain]
core, nft = cfg["core"].lower(), cfg["nft"].lower()
cut = json.load(open("data/cutoff.json"))[chain]["block"]
wins = [(a, min(a + span - 1, cut)) for a in range(cfg["deploy_block"], cut + 1, span)]
WF = f"data/{chain}_logs.windows.json"
done = json.load(open(WF)) if os.path.exists(WF) else {}
lock = threading.Lock()

def get(a, b):
    body = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{"address": [core, nft], "fromBlock": hex(a), "toBlock": hex(b)}]}
    for attempt in range(30):
        try:
            r = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": "poidh-v3-data/1.0"})
            o = json.load(urllib.request.urlopen(r, timeout=60))
            if "result" in o and isinstance(o["result"], list):
                return o["result"]
            err = str(o.get("error"))[:120]
        except Exception as e:
            err = str(e)[:120]
        if attempt % 3 == 2: print(f"window {a}-{b} retry {attempt}: {err}", flush=True)
        time.sleep(min(30, 1 + attempt * 2))
    raise SystemExit(f"window {a}-{b} failed: {err}")

t0 = time.time(); n = [0]
def work(w):
    k = f"{w[0]}-{w[1]}"
    if k in done: return
    res = get(*w)
    with lock:
        done[k] = res; n[0] += 1
        if n[0] % 200 == 0:
            json.dump(done, open(WF, "w"))
            print(f"{chain} {len(done)}/{len(wins)} windows {time.time()-t0:.0f}s", flush=True)
with ThreadPoolExecutor(threads) as ex:
    list(ex.map(work, wins))
json.dump(done, open(WF, "w"))
assert len(done) == len(wins) and all(f"{a}-{b}" in done for a, b in wins), "missing windows"
allg = {}
for res in done.values():
    for l in res:
        assert not l.get("removed"), "removed log"
        allg[(l["transactionHash"], int(l["logIndex"], 16))] = l
logs = sorted(allg.values(), key=lambda l: (int(l["blockNumber"], 16), int(l["logIndex"], 16)))
out = {"chain": chain, "source": f"eth_getLogs {URL} ({span}-block windows)", "from_block": cfg["deploy_block"], "to_block": cut,
       "core": [l for l in logs if l["address"].lower() == core],
       "nft": [l for l in logs if l["address"].lower() == nft and l["topics"][0] == TRANSFER]}
json.dump(out, open(f"data/{chain}_logs.json", "w"))
print("done", chain, len(out["core"]), len(out["nft"]), f"{time.time()-t0:.0f}s", flush=True)
