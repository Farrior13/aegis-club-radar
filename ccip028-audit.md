# Security Audit: CityCoins CCIP-028 Activation, `ccd015-redemption-book-mia-stx`, and `ccd016-swap-vault-mia-v2`

- **Auditor:** `Silver Rho` (`bc1quwju63sw7f60znfmch9gxv8jec45akjp2sfxvg` / `SP3HTBKA61VS79WAD7F2WN0SGYB72PKPT8706YW9K`)
- **Bounty ID:** `mw4761qx68024266725f` (`8,000 sats sBTC`)
- **Commit Audited:** `95fa4d0a6b3cc9c82008b08164346c31f0a21417` (`boomcrypto/citycoins2-contracts`, branch `feat/ccip-028-mia-fair-redemption`)
- **Router Dependency Verified Against Mainnet Source:** `SP1NPDHF9CQ8B9Q045CCQS1MR9M9SGJ5TT6WFFCD2.swap-router-v5-5` (`1,342` lines)

---

## Executive Summary

We performed a line-by-line review of all three target contracts (`ccip028-activate-mia-fair-redemption.clar`, `ccd015-redemption-book-mia-stx.clar`, and `ccd016-swap-vault-mia-v2.clar`) along with their live mainnet dependency `SP1NPDHF9CQ8B9Q045CCQS1MR9M9SGJ5TT6WFFCD2.swap-router-v5-5`.

While the overall architecture (Clarity 4 `as-contract?` post-condition allowances, dual-token v1/v2 normalization, tree-invariant self-testing, and monotonic `last-par-scaled` caching) is well-engineered, we identified **two concrete, non-known bugs** (one high-confidence medium severity bug in `ccd016-swap-vault-mia-v2.clar` that breaks `swap-split` whenever the Jing leg is used and breaks `smart-swap` on Jing partial fills routed to AMMs, and one medium/low invariant violation in `ccd015-redemption-book-mia-stx.clar` where partial-fill floor truncation causes the DAO to pay above the `par-scaled` ceiling).

| # | Contract & Lines | Severity | Summary |
|---|---|---|---|
| **1** | `ccd016-swap-vault-mia-v2.clar` (`#L686–L716` vs `#L628–L634`) & `swap-router-v5-5` (`#L163–L195`, `#L339–L362`, `#L1225–L1231`) | **Medium (Functional DoS of `swap-split` Jing & Fallback Legs + `smart-swap` Partial-Fill Fallback)** | `router-swap-split` passes bare `amount` to Clarity 4 `(with-ft ... amount)` instead of `max-sbtc-out`, causing every `swap-split` call with `jing-amount > u0` (that fills even 1 sat on Jing or routes any residual via `fallback`) to abort at the `as-contract?` post-condition check due to gross outbound FT accounting. Furthermore, in both `router-swap-split` and `router-smart-swap`, any partial fill on Jing where the refunded residual `(jing-amount - spent)` is re-pulled by AMM legs counts **twice** against Clarity 4's gross `with-ft` cap. |
| **2** | `ccd015-redemption-book-mia-stx.clar` (`#L459–L505`) | **Low / Invariant Violation** | In `settle-step`, a frontier partial fill (`remaining < ask`) floors `taken = (/ (* amount remaining) ask)` while still transferring the full `remaining` uSTX (`#L492`). When an offer is priced at or near `par-scaled` and `ask <= amount * remaining < 2 * ask`, `taken` floors down (e.g. to `u1` micro-MIA) while the DAO pays up to `2x - 1` times the `par-scaled` ceiling per micro-MIA burned, violating the core invariant `remaining * PAR_SCALE <= taken * par-scaled`. |

---

## Finding 1 — `ccd016-swap-vault-mia-v2.clar`: Clarity 4 Gross `with-ft` Allowance Under-Sizing in `router-swap-split` (`#L699`) and Partial-Fill Double-Pull in `router-smart-swap` (`#L634`)

### Location
- `ccd016-swap-vault-mia-v2.clar`:
  - `router-swap-split` (`#L686–L716`, specifically `#L699`)
  - `router-smart-swap` (`#L618–L644`, specifically `#L628–L634`)
- `SP1NPDHF9CQ8B9Q045CCQS1MR9M9SGJ5TT6WFFCD2.swap-router-v5-5`:
  - `jing-swap` (`#L163–L195`)
  - `swap-sbtc-for-stx` (`#L308–L409`)
  - `smart-swap-sbtc-for-stx` (`#L1209–L1271`)

### Vulnerability Details

In Clarity 4, `(as-contract? ((with-ft token-contract token-name cap)) ...)` enforces a **cumulative gross outbound FT transfer cap** from the contract over the entire inner expression — inbound refunds back to the contract do **not** decrement the gross counter.

In `router-smart-swap` (`ccd016-swap-vault-mia-v2.clar#L628–L634`), the author explicitly documented this exact Clarity 4 behavior:

```clarity
;; Clarity 4's with-ft caps gross outflows from the vault across the body,
;; not net. The router's jing leg pulls the full jing-in from the vault,
;; refunds unused sBTC back, and then pulls up to a 1% taker-rebate + 2-sat
;; rounding buffer out of the vault to pay the jing maker rebate (see
;; swap-router-v5-5 jing-swap). Size the allowance to cover both pulls.
(max-sbtc-out (+ amount (/ (* amount MAX_TAKER_REBATE_BPS) BPS) JING_REBATE_DUST_SATS))
```

However, there are **two distinct flaws** in how `with-ft` is sized across `router-swap-split` and `router-smart-swap`:

#### 1A. `router-swap-split` (`#L699`) Omits `max-sbtc-out` Entirely and Caps `with-ft` at Bare `amount`

Look at `router-swap-split` (`ccd016-swap-vault-mia-v2.clar#L699–L704`):

```clarity
  (as-contract? ((with-ft 'SM3VDXK3WZZSA84XXFKAFAF15NNZX32CTSG82JFQ4.sbtc-token "sbtc-token" amount))
    (try! (contract-call? 'SP1NPDHF9CQ8B9Q045CCQS1MR9M9SGJ5TT6WFFCD2.swap-router-v5-5
      swap-sbtc-for-stx
      amount jing-amount limit-price update fallback amm-amounts amm-mins min-stx-out
    ))
  )
```

In `swap-router-v5-5.swap-sbtc-for-stx` (`#L329–L362`):
1. `asserts!` requires `amount == jing-amount + dlmm + xyk + velar` (`#L329–L333`).
2. When `jing-amount > u0`, `jing-swap` (`#L175`) pulls `jing-amount` sBTC from `user` (`ccd016-swap-vault-mia-v2`).
3. Inside `jing-swap`, `JING_MARKET.rebid` (`#L187`) pulls `taker-rebate` (`> u0` whenever the Jing order fills) directly from `tx-sender` (`ccd016-swap-vault-mia-v2`).
4. Then the AMM legs (`dlmm`, `xyk`, `velar` at `#L351–L362`) pull `dlmm + xyk + velar` (plus any `routed` fallback residual) from `ccd016-swap-vault-mia-v2`.

Therefore, whenever `jing-amount > u0` and Jing fills:
- Gross sBTC transferred out of the vault is:
  `gross_out = jing-amount + taker-rebate + dlmm + xyk + velar + routed = amount + taker-rebate + routed > amount`.
- Because `router-swap-split` (`#L699`) sets the `with-ft` cap to `amount`, **every `swap-split` call that uses the Jing leg (`jing-amount > u0`) and either fills (`taker-rebate > u0`) or falls back (`routed > u0`) deterministically aborts at the Clarity 4 `as-contract?` post-condition check!**

#### 1B. Partial-Fill + AMM Fallback Double-Counts `(jing-amount - spent)` Against Gross `with-ft`

Look at what happens in `swap-router-v5-5` when `jing-swap` partially fills (`0 <= spent < jing-amount`):
1. `jing-swap` (`#L175`) first pulls the **entire `jing-amount`** out of the vault (`gross_out += jing-amount`).
2. `jing-swap` (`#L184`) refunds `refund = (- jing-amount spent)` back to the vault (which does **not** reduce `gross_out`).
3. In `swap-sbtc-for-stx` (`#L346–L350`, when `fallback = (some venue)`) and in `smart-swap-sbtc-for-stx` (`#L1230–L1231`, where `dlmm-stage` receives `(- amount jing-in)`), the router routes the refunded residual `(- jing-amount spent)` into the AMM legs (`DLMM`, `XYK`, `Velar`).
4. Those AMM legs pull `(- jing-amount spent)` out of the vault **a second time** (`gross_out += (jing-amount - spent)`).

Thus, the true worst-case gross sBTC outflow across `swap-sbtc-for-stx` or `smart-swap-sbtc-for-stx` is:
`gross_out_max = amount + jing-amount + taker-rebate <= (2 * amount) + (amount * MAX_TAKER_REBATE_BPS / BPS) + JING_REBATE_DUST_SATS`.

Because `execute-swap` (`#L562–L580`) already enforces the strict net balance invariant on the vault immediately after the router call:
```clarity
(sbtc-after (unwrap-panic (contract-call? 'SM3VDXK3WZZSA84XXFKAFAF15NNZX32CTSG82JFQ4.sbtc-token get-balance current-contract)))
(sbtc-spent (- sbtc-before sbtc-after))
...
(asserts! (<= sbtc-spent amount) ERR_SLIPPAGE)
```
sizing `max-sbtc-out` in **both** `router-smart-swap` and `router-swap-split` to cover the refund-and-reroute gross pull (`(+ (* amount u2) (/ (* amount MAX_TAKER_REBATE_BPS) BPS) JING_REBATE_DUST_SATS)`) is 100% safe for net vault funds while preventing false post-condition reverts on Jing partial fills and `swap-split` calls.

### Recommended Fix
In `ccd016-swap-vault-mia-v2.clar`:
1. In `router-swap-split` (`#L699`), replace bare `amount` in `with-ft` with `max-sbtc-out`.
2. In both `router-smart-swap` (`#L634`) and `router-swap-split` (`#L699`), include the Jing refund-and-fallback gross pull allowance `(+ (* amount u2) (/ (* amount MAX_TAKER_REBATE_BPS) BPS) JING_REBATE_DUST_SATS)`, relying on `#L580` (`(asserts! (<= sbtc-spent amount) ERR_SLIPPAGE)`) to enforce the net cap.

---

## Finding 2 — `ccd015-redemption-book-mia-stx.clar`: Frontier Partial-Fill Floor Truncation in `settle-step` (`#L489–L502`) Violates the `par-scaled` Ceiling

### Location
- `ccd015-redemption-book-mia-stx.clar`:
  - `at-or-below-par?` (`#L244–L249`)
  - `settle-step` (`#L459–L505`, specifically `#L488–L502`)

### Vulnerability Details

`ccd015-redemption-book-mia-stx.clar` states its core invariant in the header (`#L9–L10`) and in `at-or-below-par?` (`#L244–L249`):
> *"par is the hard ceiling: above it, the DAO does not buy."*
```clarity
(define-private (at-or-below-par? (amount uint) (ask uint) (par-scaled uint))
  (<= (* ask PAR_SCALE) (* amount par-scaled))
)
```

In `settle-step` (`#L488–L504`), when the remaining STX budget `remaining` reaches the frontier offer (`remaining < ask`), the contract executes a partial fill:

```clarity
;; Partial fill: seller keeps their seat with reduced amount and ask.
(let ((taken (/ (* amount remaining) ask)))
  (if (is-eq taken u0)
    (ok (merge state { remaining: u0, stopped: true }))
    (begin
      (try! (as-contract? ((with-stx remaining))
        (try! (stx-transfer? remaining current-contract (get owner entry)))
      ))
      (try! (burn-mia taken))
      (map-set offers id (merge entry {
        amount: (- amount taken),
        ask: (- ask remaining),
      }))
```

Notice the direction of rounding:
- `taken = floor((amount * remaining) / ask)` rounds **down** the MIA burned by the DAO, while `stx-transfer?` pays the seller the **entire unrounded `remaining` uSTX**!
- Why did this happen? In the upstream reference (`mia-fair-faktory-v2`), a third-party buyer was spending STX to buy tokens from the book, so flooring `taken` protected the resting seller. In `ccd015`, the **DAO** is spending `remaining` uSTX to burn `taken` MIA, and must never pay an effective price `remaining / taken` above `par-scaled / PAR_SCALE` (`remaining * PAR_SCALE <= taken * par-scaled`).

#### Concrete Numerical Proof
Suppose `par-scaled = u5012531329`, and a seller posts an offer right at par:
1. `amount = u399` micro-MIA, `ask = u2` uSTX (`ask * PAR_SCALE = 2,000,000,000,000 <= amount * par-scaled = 2,000,000,000,271`, so `(at-or-below-par? u399 u2 par-scaled)` is `true`).
2. `settle-step` reaches this offer with `remaining = u1` uSTX (`remaining < ask`).
3. `taken = (/ (* u399 u1) u2) = u199` micro-MIA (truncated down from `199.5`).
4. Effective price paid by the DAO on the partial fill: `1 uSTX` for `199` micro-MIA (`remaining * PAR_SCALE = 1,000,000,000,000 > taken * par-scaled = 997,493,734,471`), which **exceeds `par-scaled`**!
5. Even more extreme: for any at-or-below-par offer where `(* amount remaining)` lies in `[ask, 2 * ask - 1]`, `taken` floors to **`u1` micro-MIA** while the DAO pays up to `floor((2 * ask - 1) / amount)` uSTX — paying up to **nearly `2x` the `par-scaled` ceiling** per micro-MIA burned on the partial fill!

### Recommended Fix
In `settle-step` (`#L489–L490`), either:
1. Verify `(at-or-below-par? taken remaining par-scaled)` alongside `(is-eq taken u0)` (stopping settlement if floor truncation pushes the partial fill above par):
   ```clarity
   (if (or (is-eq taken u0) (not (at-or-below-par? taken remaining par-scaled)))
     (ok (merge state { remaining: u0, stopped: true }))
   ```
2. Or compute the exact uSTX `paid = (/ (* taken ask) amount)` corresponding to `taken` so the seller is never overpaid for truncated fractional micro-MIA.

---

## Verification of Other Components (`ccip028` & Tree Invariants)

1. **`ccip028-activate-mia-fair-redemption.clar`:**
   - Correctly checks `(contract-call? .ccd001-direct-execute is-extension contract-caller)` (`#L31`), disables `ccd012-redemption-mia` before sweeping (`#L36`), sweeps the exact MIA Treasury STX balance into `ccd015` (`#L43–L47`), registers `ccd015` and `ccd016` as extensions (`#L51–L55`), and calls `record-ccip028-baseline` on `ccd015` after sweep (`#L60`).
2. **`ccd015` Red-Black Tree & FIFO Ordering (`#L575–L904`):**
   - `compare-keys` (`#L564–L569`) compares `(price-a * amount-b)` vs `(price-b * amount-a)` using exact cross-multiplication with `id` tie-breaking (strictly FIFO at identical rational prices, avoiding fixed-point quantization collisions).
   - `check-invariants` (`#L886–L904`) verifies both forward (`next-of`) and backward (`prev-of`) traversals against `book-count` plus root-parent and black-height invariants.
