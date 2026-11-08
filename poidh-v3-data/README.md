# POIDH v3 Cross-Chain Wallet Activity & Reconciliation Dataset (Ethereum Mainnet, Arbitrum, Base)

**Live Interactive Explorer & 1-Click CSV Downloads:** [https://farrior13.github.io/aegis-club-radar/poidh-v3-data/](https://farrior13.github.io/aegis-club-radar/poidh-v3-data/)  
**Public GitHub Repository:** [https://github.com/Farrior13/aegis-club-radar/tree/main/poidh-v3-data](https://github.com/Farrior13/aegis-club-radar/tree/main/poidh-v3-data)

---

## 1. Deliverable CSVs (Exact 13-Column Schema)

All CSVs strictly implement the requested 13-column schema (`wallet_address,eth_paid_mainnet,eth_paid_arbitrum,eth_paid_base,eth_paid_total,eth_earned_mainnet,eth_earned_arbitrum,eth_earned_base,eth_earned_total,nfts_held_mainnet,nfts_held_arbitrum,nfts_held_base,nfts_held_total`) with EIP-55 checksummed addresses and exact integer-wei decimal formatting (zero floating-point drift):

| File | Rows | Snapshot | Description |
| :--- | :---: | :---: | :--- |
| **[`poidh_v3_wallets.csv`](poidh_v3_wallets.csv)** | **1,438** | **Latest Head (`2026-11-08 16:19:06 UTC`)** | **Primary Deliverable:** Every unique wallet that has interacted with POIDH v3 across Mainnet, Arbitrum, and Base (`470` wallets with non-zero paid/earned/NFTs + `968` zero-balance historical participants). Includes Base Bounty `#490` (`Claim #4165`, `0.0022 ETH`). |
| **[`poidh_v3_wallets_active_only.csv`](poidh_v3_wallets_active_only.csv)** | **470** | **Latest Head (`2026-11-08 16:19:06 UTC`)** | Filtered view containing only wallets with `eth_paid_total > 0`, `eth_earned_total > 0`, or `nfts_held_total > 0`. |
| **[`poidh_v3_wallets_cutoff_1794110394.csv`](poidh_v3_wallets_cutoff_1794110394.csv)** | **1,436** | **Bounty `#554` Creation (`2026-11-08 03:59:54 UTC`)** | Exact snapshot pinned to the creation timestamp of Bounty `#554` (`1794110394`, blocks `26367617` / `522271780` / `54600096`, `461` completed bounties, `12.37015944252522 ETH`). |
| **[`poidh_v3_protocol_nft_holdings.csv`](poidh_v3_protocol_nft_holdings.csv)** | **3** | **Latest Head (`2026-11-08 16:19:06 UTC`)** | Separate accounting for the `4,858` unaccepted-claim NFTs held in escrow by the POIDH v3 core contracts (`380` Mainnet, `619` Arbitrum, `3,859` Base). |
| **[`completed_bounties.csv`](completed_bounties.csv)** | **462** | **Latest Head (`2026-11-08 16:19:06 UTC`)** | Per-bounty audit table across all `462` completed bounties (`27` Mainnet, `113` Arbitrum, `322` Base) verifying `sum(contributions) == gross_payout` for every single bounty. |
| **[`poidh_v3_wallets_detail.csv`](poidh_v3_wallets_detail.csv)** | **1,438** | **Latest Head (`2026-11-08 16:19:06 UTC`)** | Extended wallet activity counts (`bounties_created`, `bounties_funded_completed`, `bounties_won`, `claims_submitted` per chain). |

---

## 2. Cross-Chain Reconciliation Summary

Every completed bounty's gross ETH payout (before the 2.5% protocol fee) is credited once to the winning claimant (`eth_earned`) and attributed across the exact contributing wallets whose stake remained active in the bounty at completion (`eth_paid`).

### A. Latest Head Snapshot (`2026-11-08 16:19:06 UTC` — 462 Completed Bounties)

| Chain | Core Contract | NFT Contract | Snapshot Block | Completed Bounties (Solo / Open) | Accepted via Vote | Gross ETH Paid (Contributors) | Gross ETH Earned (Winners) | Reconciled (`Paid == Earned`) | 2.5% Protocol Fee (ETH) | NFTs Minted | NFTs in User Wallets | NFTs in Protocol Escrow |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ethereum Mainnet** | [`0xe731...4232`](https://etherscan.io/address/0xe731dfadbff20542e10d09d26fc71445c70d4232) | [`0x9c5f...24d9`](https://etherscan.io/address/0x9c5f45d5e1382e4058d334d93c6c01442012a4d9) | `26,371,283` | `27` (`1` / `26`) | `19` | `3.381683` | `3.381683` | **YES (`0` diff)** | `0.084542075` | `407` | `27` | `380` |
| **Arbitrum One** | [`0x5555...1719`](https://arbiscan.io/address/0x5555fa783936c260f77385b4e153b9725fef1719) | [`0x27e1...cf6a`](https://arbiscan.io/address/0x27e117cc9a8da363442e7bd0618939e3eeeacf6a) | `522,413,361` | `113` (`14` / `99`) | `37` | `2.969041` | `2.969041` | **YES (`0` diff)** | `0.074226025` | `732` | `113` | `619` |
| **Base Mainnet** | [`0x5555...1719`](https://basescan.org/address/0x5555fa783936c260f77385b4e153b9725fef1719) | [`0x27e1...cf6a`](https://basescan.org/address/0x27e117cc9a8da363442e7bd0618939e3eeeacf6a) | `54,821,853` | `322` (`36` / `286`) | `178` | `6.02163544252522` | `6.02163544252522` | **YES (`0` diff)** | `0.1505408860631305` | `4,181` | `322` | `3,859` |
| **TOTAL (All 3 Chains)** | — | — | — | **`462`** (`51` / `411`) | **`234`** | **`12.37235944252522`** | **`12.37235944252522`** | **YES (`12372359442525220000 wei`)** | **`0.3093089860631305`** | **`5,320`** | **`462`** | **`4,858`** |

### B. Creation-Timestamp Cutoff Snapshot (`2026-11-08 03:59:54 UTC`, Unix `1794110394` — 461 Completed Bounties)
- **Blocks:** Ethereum `26,367,617`, Arbitrum `522,271,780`, Base `54,600,096`
- **Totals:** `461` completed bounties (`27` Mainnet, `113` Arbitrum, `321` Base), **`12.37015944252522 ETH`** paid = earned (`12370159442525220000 wei`), **`461`** NFTs in user wallets, **`4,844`** NFTs in protocol escrow (`5,305` minted).
- **Delta between Creation Cutoff and Latest Head:** Base Bounty `#490` (`Claim #4165` by `0xCecAaCdd987688CcDff15C775CbA8E5ba63A8460`, gross `0.0022 ETH`, funded by `0x0E7f38EE61156D57b2B8ab4bAa1648b0Daa40217` `0.002 ETH` + `0x22DF252B4958A7a2E8B5B8F657BF3bA18223C9da` `0.0002 ETH`) completed via vote resolution, plus `15` new claim NFTs minted on Base (`#4167..#4181`).

---

## 3. Top 15 Wallets by Total Volume (`Paid + Earned`)

| Rank | Wallet Address | ETH Paid (Mainnet / Arb / Base) | **ETH Paid Total** | ETH Earned (Mainnet / Arb / Base) | **ETH Earned Total** | NFTs Held (M / A / B) | **NFTs Total** |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `0x4200aC338555e25B20C8fe82AC02a5C8D4e5A5b4` | `0.3104` / `0.72411` / `1.68539` | **`2.7199`** | `0` / `0` / `0` | **`0`** | `5` / `31` / `35` | **`71`** |
| 2 | `0xc5f2D0A16146725ce62F8f67D7036650E7Bf6218` | `0` / `0` / `0` | **`0`** | `1.53575` / `0` / `0` | **`1.53575`** | `0` / `0` / `0` | **`0`** |
| 3 | `0xc0163E58648b247c143023CFB26C2BAA42C9d9A9` | `0` / `1.527` / `0` | **`1.527`** | `0` / `0` / `0` | **`0`** | `0` / `0` / `0` | **`0`** |
| 4 | `0xcebe15E70Fad55c0245d9Add4d13CC1F91236ade` | `0` / `0.0045` / `0` | **`0.0045`** | `0` / `1.3735` / `0` | **`1.3735`** | `0` / `0` / `0` | **`0`** |
| 5 | `0x10Fc964Ef70C8467CD8c53e9eD9347422AdF96A8` | `0.055` / `0.499727` / `0.61336` | **`1.168087`** | `0.001` / `0.001` / `0.001` | **`0.003`** | `3` / `42` / `73` | **`118`** |
| 6 | `0x34aA3F359A9D614239015126635CE7732c18fDF3` | `0` / `0` / `0` | **`0`** | `1` / `0` / `0` | **`1`** | `0` / `0` / `0` | **`0`** |
| 7 | `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` | `1` / `0` / `0` | **`1`** | `0` / `0` / `0` | **`0`** | `0` / `0` / `0` | **`0`** |
| 8 | `0x293F2BB46d15d6a496300a03E68EbA21e17A0213` | `0` / `0` / `0` | **`0`** | `0` / `0.0025` / `0.6619` | **`0.6644`** | `0` / `0` / `0` | **`0`** |
| 9 | `0x864405169b4AbCa041dDa945D2a028703B70585A` | `0.35` / `0` / `0` | **`0.35`** | `0` / `0` / `0` | **`0`** | `0` / `0` / `0` | **`0`** |
| 10 | `0xc5412b7a321F4b459B534257cC6C1C3C03e18eAD` | `0` / `0` / `0.00603` | **`0.00603`** | `0` / `0.0255` / `0.308133` | **`0.333633`** | `0` / `0` / `1` | **`1`** |
| 11 | `0xB31Faa5c1D581C70F4b6ed095c944936cBd2a357` | `0` / `0` / `0` | **`0`** | `0` / `0` / `0.255936` | **`0.255936`** | `0` / `0` / `0` | **`0`** |
| 12 | `0xF143db60A0B1cBb8076B786Eb6635b93f18db744` | `0` / `0.001` / `0.254533` | **`0.255533`** | `0` / `0` / `0` | **`0`** | `0` / `0` / `1` | **`1`** |
| 13 | `0xdb83ae472F108049828dB5F429595c4B5932B62C` | `0` / `0` / `0.25284` | **`0.25284`** | `0` / `0` / `0` | **`0`** | `0` / `0` / `1` | **`1`** |
| 14 | `0x4143EA98CE4EA7376a6b0aBd53F98541B4D3cA83` | `0.20256789` / `0` / `0` | **`0.20256789`** | `0` / `0` / `0` | **`0`** | `0` / `0` / `0` | **`0`** |
| 15 | `0xF35ff7426e2dbE06305e71EaeE7E038E6dbAC620` | `0.055` / `0` / `0.127` | **`0.182`** | `0` / `0` / `0` | **`0`** | `1` / `0` / `0` | **`1`** |

---

## 4. Methodology, Dual-Verification & Edge Cases

1. **Raw RPC Event Replay + Multicall3 State Pinning:**
   - Block explorer APIs on Base exhibit indexing gaps (missing 212 of 6,651 core logs and 165 NFT `Transfer` logs). Therefore, all events are extracted directly via `eth_getLogs` from archival JSON-RPC endpoints (`fetch_logs.py`, `update_base_latest.py`) from contract deployment block (`25,088,348` Mainnet, `423,059,286` Arbitrum, `41,026,079` Base) to the snapshot block.
   - Independently, full contract state (`bountyCounter`, `claimCounter`, every `bounties(i)`, `getParticipants(i)`, `claims(i)`, and NFT `ownerOf(tokenId)` + `balanceOf(holder)`) is queried via `Multicall3` (`0xcA11bde05977b3631167028862bE2a173976CA11`) at the exact target block (`fetch_state.py`).
2. **Strict Accounting Rules (`build.py`):**
   - **ETH Paid (`eth_paid_*`):** Tracks `BountyCreated` (initial issuer stake), `BountyJoined` (+contributor stake), `WithdrawFromOpenBounty` (resets withdrawn contributor stake to `0` before completion), `BountyCancelled` / `RefundClaimed` (excluded). Only stakes active inside a bounty at the moment `ClaimAccepted` fires are credited to `eth_paid`, verified against both the `ClaimAccepted` gross `bountyAmount` and the on-chain `getParticipants(bountyId)` arrays.
   - **ETH Earned (`eth_earned_*`):** Credits the winning `claimIssuer` from `ClaimAccepted` with the **gross** `bountyAmount` (`payout + fee`, where `fee = bountyAmount * 250 / 10000`, i.e. before the 2.5% protocol fee).
   - **NFTs Held (`nfts_held_*`):** Replays every ERC-721 `Transfer` event on the POIDH v3 NFT contracts and cross-verifies every token ID in `[startClaimIndex, claimCounter)` against live `ownerOf(tokenId)` and `balanceOf(holder)`. Because `createClaim` mints each claim NFT to the POIDH v3 core contract in escrow and `_acceptClaim` transfers only the winning claim NFT to the bounty issuer, the `4,858` unaccepted-claim NFTs still held by the core contracts (`380` Mainnet, `619` Arbitrum, `3,859` Base) are excluded from user rows and reported separately in `poidh_v3_protocol_nft_holdings.csv`.
3. **Reproducibility:**
   ```bash
   pip install -r requirements.txt
   python build.py       # Replays all logs, cross-checks against state, asserts 0 discrepancies, writes CSVs
   python check_csv.py   # Independently verifies column sums and reconciliation across all 1,438 rows
   python build.py --drop-join 0  # Positive control: dropping 1 join event triggers 4 reconciliation assertion failures
   ```
