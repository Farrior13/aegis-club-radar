
const INITIAL_BOUNTIES = [
  {
    id: 520,
    chain: 'base',
    chainLabel: 'Base Mainnet #520',
    name: 'Bring Your App to NPC Hackathon Bounty 2',
    amountEth: '0.004284 ETH',
    amountUsd: '$11.65 USD',
    issuer: '0x8be2...467f',
    status: 'OPEN · NPC SEASON ONE',
    highlight: true,
    desc: 'Apply to NPC Season One with an existing, working App or Mini App. Tell us how you bring your App and community together through a Club.',
    url: 'https://poidh.xyz/base/bounty/520'
  },
  {
    id: 519,
    chain: 'base',
    chainLabel: 'Base Mainnet #519',
    name: 'Bring Your App to NPC Hackathon',
    amountEth: '0.004284 ETH',
    amountUsd: '$11.65 USD',
    issuer: '0x8be2...467f',
    status: 'OPEN · NPC SEASON ONE',
    highlight: true,
    desc: 'NPC Season One is bringing together 25 Clubs for a two-week Club App Hackathon with $1,500 in prizes. Connect your existing App to a Club.',
    url: 'https://poidh.xyz/base/bounty/519'
  },
  {
    id: 514,
    chain: 'base',
    chainLabel: 'Base Mainnet #514',
    name: 'CC0 Halloween — 4-Panel Crypto Lore Comic',
    amountEth: '0.056500 ETH',
    amountUsd: '$153.10 USD',
    issuer: '0x149d...b13a',
    status: 'OPEN · CREATIVE CC0',
    highlight: false,
    desc: 'Create a 4-panel CC0 Halloween comic starring public-domain crypto characters (Nouns, CrypToadz, Chain Runners, Loot).',
    url: 'https://poidh.xyz/base/bounty/514'
  },
  {
    id: 511,
    chain: 'base',
    chainLabel: 'Base Mainnet #511',
    name: 'poidh v1 data — Arbitrum Historical Contract Audit',
    amountEth: '0.018500 ETH',
    amountUsd: '$50.10 USD',
    issuer: '0x10fc...96a8',
    status: 'OPEN · ON-CHAIN DATA',
    highlight: false,
    desc: 'On-chain audit of POIDH v1 contract on Arbitrum One reconciling ETH paid out, gross ETH earned, and v1 NFTs held per wallet.',
    url: 'https://poidh.xyz/base/bounty/511'
  },
  {
    id: 499,
    chain: 'base',
    chainLabel: 'Base Mainnet #499',
    name: 'Create a TikTok or Reel about POIDH',
    amountEth: '0.037000 ETH',
    amountUsd: '$100.20 USD',
    issuer: '0x10fc...96a8',
    status: 'OPEN · COMMUNITY',
    highlight: false,
    desc: 'Create an engaging short-form video showcasing live on-chain bounties and community quests on POIDH.',
    url: 'https://poidh.xyz/base/bounty/499'
  },
  {
    id: 342,
    chain: 'arbitrum',
    chainLabel: 'Arbitrum One #342',
    name: 'Arbitrum Ecosystem On-Chain Quest Tracker',
    amountEth: '0.037500 ETH',
    amountUsd: '$101.50 USD',
    issuer: '0x5555...1719',
    status: 'TRACKED · ARBITRUM',
    highlight: false,
    desc: 'Cross-chain POIDH v3 bounty feed indexed in real time for Aegis Club members.',
    url: 'https://poidh.xyz/arbitrum'
  }
];

const INITIAL_SQUADS = [
  {
    bounty: 'Base #519 & #520 — Bring Your App to NPC Hackathon',
    name: 'Aegis Club Core (@aegislabs)',
    roles: 'Mini-App Lead + On-Chain RPC Integrator + Club Host',
    split: '100% Club Activation Treasury · Verified Wallet 0x7152...4c07'
  },
  {
    bounty: 'Base #514 — CC0 Halloween 4-Panel Comic (0.0565 ETH)',
    name: 'CC0 Lore Artists & Storyboard Squad',
    roles: 'Illustrator + Nouns/CrypToadz Lore Writer',
    split: '70% Artist / 30% Lore & Metadata Verification'
  },
  {
    bounty: 'Base #511 — POIDH v1 Arbitrum Audit (0.0185 ETH)',
    name: 'On-Chain Forensics Squad',
    roles: 'Archive RPC Indexer + CSV Reconciler',
    split: '80% Data Engineer / 20% Peer Reviewer'
  }
];

let activeChain = 'all';
let searchQuery = '';

function renderBounties() {
  const grid = document.getElementById('bounty-grid');
  const filtered = INITIAL_BOUNTIES.filter(b => {
    const matchChain = activeChain === 'all' || b.chain === activeChain;
    const matchSearch = !searchQuery ||
      b.name.toLowerCase().includes(searchQuery) ||
      b.desc.toLowerCase().includes(searchQuery) ||
      String(b.id).includes(searchQuery);
    return matchChain && matchSearch;
  });

  grid.innerHTML = filtered.map(b => `
    <article class="bounty-card ${b.highlight ? 'highlight' : ''}">
      <div>
        <div class="b-top">
          <span class="b-chain">${b.chainLabel}</span>
          <span class="b-reward">${b.amountEth} (${b.amountUsd})</span>
        </div>
        <h3 class="b-title">${b.name}</h3>
        <p class="b-desc" style="margin-top:8px;">${b.desc}</p>
      </div>
      <div class="b-meta">
        <span>${b.status} · Issuer ${b.issuer}</span>
        <a class="b-link" href="${b.url}" target="_blank" rel="noopener">Inspect on POIDH →</a>
      </div>
    </article>
  `).join('');
}

function renderSquads() {
  const list = document.getElementById('squad-list');
  list.innerHTML = INITIAL_SQUADS.map(s => `
    <div class="squad-item">
      <h4>${s.name}</h4>
      <p><strong>Target:</strong> ${s.bounty}</p>
      <p><strong>Roles:</strong> ${s.roles}</p>
      <p><strong>Split:</strong> ${s.split}</p>
    </div>
  `).join('');
}

async function syncBaseRpcCounter() {
  const statusEl = document.getElementById('rpc-status');
  const cntEl = document.getElementById('m-base-cnt');
  try {
    statusEl.textContent = '↻ Syncing Base RPC...';
    const res = await fetch('https://mainnet.base.org', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'eth_call',
        params: [{ to: '0x5555fa783936c260f77385b4e153b9725fef1719', data: '0x77b67781' }, 'latest']
      })
    });
    const data = await res.json();
    if (data && data.result) {
      const counter = parseInt(data.result, 16);
      cntEl.textContent = String(counter);
      statusEl.textContent = `● Base RPC Live (#${counter})`;
    }
  } catch (e) {
    statusEl.textContent = '● Base / Arb / ETH Ready';
  }
}

document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  });
});

document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeChain = chip.dataset.chain;
    renderBounties();
  });
});

document.getElementById('bounty-search').addEventListener('input', e => {
  searchQuery = e.target.value.trim().toLowerCase();
  renderBounties();
});

document.getElementById('refresh-btn').addEventListener('click', syncBaseRpcCounter);

document.getElementById('squad-form').addEventListener('submit', e => {
  e.preventDefault();
  INITIAL_SQUADS.unshift({
    bounty: document.getElementById('squad-bounty').value,
    name: document.getElementById('squad-name').value,
    roles: document.getElementById('squad-roles').value,
    split: document.getElementById('squad-split').value
  });
  renderSquads();
});

renderBounties();
renderSquads();
syncBaseRpcCounter();
