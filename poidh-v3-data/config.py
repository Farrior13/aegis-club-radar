"""Contract addresses, deploy blocks (from Sourcify deployment records) and the snapshot cutoff."""
CUTOFF_TS = 1794110394  # 2026-11-08T03:59:54Z = creation of poidh bounty #1540 (Base)
CHAINS = {
    "mainnet": {"core": "0xe731dfadbff20542e10d09d26fc71445c70d4232", "nft": "0x9c5f45d5e1382e4058d334d93c6c01442012a4d9",
                "deploy_block": 25088348},
    "arbitrum": {"core": "0x5555fa783936c260f77385b4e153b9725fef1719", "nft": "0x27e117cc9a8da363442e7bd0618939e3eeeacf6a",
                 "deploy_block": 423059286},
    "base": {"core": "0x5555fa783936c260f77385b4e153b9725fef1719", "nft": "0x27e117cc9a8da363442e7bd0618939e3eeeacf6a",
             "deploy_block": 41026079},
}
# max getLogs span per request on the free public endpoints used (drpc free tier: 10,000 blocks)
SPAN = {"mainnet": 1_000, "arbitrum": 100_000, "base": 1_000}  # arb1.arbitrum.io: 100k blocks for a 2-address query; Base: tenderly 1k
