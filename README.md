# Cerberus: A Self-Cleaning Ledger Protocol

Cerberus is a novel blockchain protocol designed to address the long-standing challenge of unbounded storage growth (state bloat) in distributed ledger systems. Traditional blockchains require nodes to maintain complete historical data, leading to scalability limitations and increasing barriers to decentralization. 

Building upon a pruning-enabled Merkle-DAG architecture, Cerberus introduces **Proof of Utility (PoU)**—a mechanism that evaluates transactions based on their economic and structural relevance. Instead of relying on arbitrary time-based pruning, the protocol selectively retains high-utility data while pruning low-utility data, preserving cryptographic proofs for verifiability.

Cerberus aims to evolve blockchain design from:
_"Store everything forever"_
to:
_"Retain what is useful, reward what is reused, and discard what is irrelevant."_

---

## Architecture & Layers

Cerberus extends a pruning-enabled blockchain by introducing a Utility Evaluation Layer and additional economic and incentive layers.

### Layer 1 — Storage Layer (Core)
*   **Merkle-DAG structure:** Ensures cross-epoch integrity and linkage.
*   **Proof of Utility (PoU) Pruning:** Transactions are scored based on value, access frequency, and recency. Low utility transactions are discarded.
*   **Cryptographic proof retention:** Merkle paths are stored for pruned data to ensure full verifiability.

### Layer 2 — Utility-Based Economic Layer (Conceptual)
*   **Utility-adjusted transaction fees:** Dynamic transaction fee adjustment based on utility. High-utility transactions incur lower fees, while low-utility transactions incur higher costs.

### Layer 3 — Incentive Layer (Conceptual)
*   **Proof of Reference:** A mechanism for rewarding useful data. Frequently referenced data generates rewards, incentivizing nodes to store high-utility data.

---

## Current Implementation (Prototype Phase 2)

The current prototype (Phase 2) focuses on formalizing the PoU model, system architecture, and mathematical design. Economic layers are proposed as conceptual extensions for future implementation.

### Repository Layout

```
project/
├── core/                   # Shared blockchain engine (all phases import from here)
│   ├── crypto.py           # SHA-256 primitives, block header hashing
│   ├── transaction.py      # Transaction model + utility scoring
│   ├── merkle.py           # Merkle tree (manual SHA-256, no external libs)
│   ├── block.py            # Block structure (summary_hash + block_hash)
│   ├── blockchain.py       # Blockchain class with chain integrity validation
│   ├── proof_store.py      # Stores Merkle proofs for pruned transactions
│   ├── pruning.py          # prune_chain() and prune_chain_epoch()
│   └── verification.py     # verify_transaction(), verify_all()
├── phase2/
│   ├── simulation.py       # Phase 2 demo: generates data, runs pruning, prints metrics
│   └── cerberus-doc.pdf    # Concept Documentation
└── README.md
```

### How to Run the Prototype

**Requirements:** Python 3.10+ (uses built-in `hashlib`, `dataclasses`, `random` — no external dependencies needed)

Always run from the **project root** so that `core/` is on the Python path:

```powershell
python phase2/simulation.py
```

### Simulation Output

The prototype simulates transaction generation and compares **PoU pruning** against traditional **Epoch-based pruning** (which blindly wipes all transactions in old blocks).

Output includes:
*   Total, pruned, and retained transactions
*   Storage reduction ratio (KB saved)
*   Proof Verification Rate (must remain at 100%)
*   Chain Integrity Validation

### Configuration

Edit the constants at the top of `phase2/simulation.py`:

| Parameter | Default | Effect |
|---|---|---|
| `NUM_TRANSACTIONS` | 100 | Total transactions to simulate |
| `BLOCK_SIZE` | 10 | Transactions per block |
| `PRUNE_THRESHOLD` | 0.5 | Utility score below this → pruned |
| `EPOCH_THRESHOLD` | 3 | Epoch age at which epoch-based pruning triggers |
| `WEIGHTS` | value=0.5, freq=0.3, recency=0.2 | Utility scoring weights |

---

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| **Phase 1** | Concept, architecture, design | ✅ Complete |
| **Phase 2** | Core engine prototype and Proof of Utility modeling | ✅ Complete |
| **Phase 3** | Full system implementation: stateless sync, P2P network, benchmarking | 🔲 Planned |
| **Cerberus Vision** | Utility-based fee market, Proof of Reference reward system, optimization | 🔲 Future |
