"""Read-only JSON-RPC helper (no keys). Rotates over public endpoints per chain; retries with backoff.
Batch items that revert come back as None."""
import json, sys, time, urllib.request

RPCS = {
    "mainnet": ["https://eth.drpc.org", "https://ethereum-rpc.publicnode.com"],
    "arbitrum": ["https://arb1.arbitrum.io/rpc", "https://arbitrum.drpc.org"],
    "base": ["https://base.drpc.org", "https://mainnet.base.org"],
}
UA = {"Content-Type": "application/json", "User-Agent": "poidh-v3-data/1.0"}
_i = {k: 0 for k in RPCS}


def post(chain, body, timeout=90):
    for attempt in range(10):
        url = RPCS[chain][_i[chain] % len(RPCS[chain])]
        try:
            r = urllib.request.Request(url, data=json.dumps(body).encode(), headers=UA)
            return json.load(urllib.request.urlopen(r, timeout=timeout))
        except Exception as e:
            print(f"rpc retry {attempt} {url} {str(e)[:100]}", file=sys.stderr, flush=True)
            _i[chain] += 1
            time.sleep(1 + attempt * 2)
    raise SystemExit(f"rpc failed on {chain}")


def call(chain, method, params):
    for attempt in range(6):
        out = post(chain, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        if isinstance(out, dict) and "error" in out:
            err = str(out["error"])
            if "revert" in err.lower():
                raise RuntimeError(f"{method}: {err}")
            print(f"rpc error {attempt} {err[:160]}", file=sys.stderr, flush=True)
            _i[chain] += 1
            time.sleep(1 + attempt * 2)
            continue
        return out["result"]
    raise RuntimeError(f"{method} failed: {out}")


def batch(chain, reqs, size=50):
    """reqs: list of (method, params). Returns results in order; 'execution reverted' -> None."""
    res = []
    for s in range(0, len(reqs), size):
        chunk = reqs[s:s + size]
        body = [{"jsonrpc": "2.0", "id": i, "method": m, "params": p} for i, (m, p) in enumerate(chunk)]
        for attempt in range(10):
            out = post(chain, body)
            if isinstance(out, dict) or len(out) != len(body):
                print("batch err", str(out)[:200], file=sys.stderr, flush=True); _i[chain] += 1; time.sleep(2 + attempt * 2); continue
            out = sorted(out, key=lambda x: x["id"])
            bad = [o["error"] for o in out if "error" in o and "revert" not in str(o["error"]).lower()]
            if bad:
                print("batch item err", str(bad[:2])[:200], file=sys.stderr, flush=True); _i[chain] += 1; time.sleep(2 + attempt * 2); continue
            res += [o.get("result") for o in out]
            break
        else:
            raise SystemExit("batch failed")
    return res
