# Cerberus: A Self-Cleaning Ledger Protocol

Cerberus is a novel blockchain protocol designed to address the long-standing challenge of unbounded storage growth (state bloat) in distributed ledger systems. Traditional blockchains require nodes to maintain complete historical data, leading to scalability limitations and increasing barriers to decentralization.

Building upon a pruning-enabled Merkle-DAG architecture, Cerberus introduces **Proof of Utility (PoU)**—a mechanism that evaluates transactions based on their economic and structural relevance. Instead of relying on arbitrary time-based pruning, the protocol selectively retains high-utility data while pruning low-utility data, preserving cryptographic proofs for verifiability.

Cerberus aims to evolve blockchain design from:
_"Store everything forever"_
to:
_"Retain what is useful, reward what is reused, and discard what is irrelevant."_

---

## Architecture & Layers

### Layer 1 — Storage Layer (Core)
- **Merkle-DAG structure:** Ensures cross-epoch integrity and linkage.
- **Proof of Utility (PoU) Pruning:** Transactions are scored based on value, access frequency, and recency. Low-utility transactions are discarded.
- **Cryptographic proof retention:** Merkle paths are stored for pruned data to ensure full verifiability.

### Layer 2 — P2P Network (Phase 3)
- **Socket-based peer nodes:** Nodes propagate blocks and transactions over TCP sockets using no external libraries.
- **Stateless header sync:** New nodes join by downloading block headers only — no full transaction history required.
- **On-demand proof retrieval:** Any node can fetch a Merkle proof for a specific transaction on-demand.

### Layer 3 — Digital Signatures (Phase 3)
- **ECDSA on SECP256K1:** Transactions are signed with Elliptic Curve keys using the `cryptography` package.

### Layer 4 — Utility-Based Economic Layer (Conceptual)
- **Utility-adjusted transaction fees:** High-utility transactions incur lower fees; low-utility transactions incur higher costs.

### Layer 5 — Incentive Layer (Conceptual)
- **Proof of Reference:** Frequently referenced data generates rewards, incentivising nodes to retain high-utility data.

---

## Repository Layout

```
project/
├── core/                        # Shared blockchain engine (all phases)
│   ├── crypto.py                # SHA-256 primitives + ECDSA sign/verify (Phase 3)
│   ├── transaction.py           # Transaction model + utility scoring + sig fields
│   ├── merkle.py                # Merkle tree (stdlib SHA-256, no external libs)
│   ├── block.py                 # Block structure + to_dict/from_dict/to_header_dict
│   ├── blockchain.py            # Blockchain class + get_headers + sync_from_headers
│   ├── proof_store.py           # Merkle proofs + JSON persistence (Phase 3)
│   ├── pruning.py               # prune_chain() and prune_chain_epoch()
│   ├── verification.py          # verify_transaction(), verify_all()
│   └── sync.py                  # Stateless header sync protocol (Phase 3)
├── p2p/
│   ├── node.py                  # Socket-based P2P node (Phase 3)
│   └── p2p_simulation.py        # 3-node broadcast + joiner demo
├── phase2/
│   └── simulation.py            # Phase 2 demo (unchanged, still runs)
├── phase3/
│   ├── simulation.py            # Phase 3 full end-to-end demo
│   └── benchmark.py             # Metrics suite → benchmark_results.csv
├── tests/
│   ├── test_pruning.py          # Pruning unit tests
│   ├── test_verification.py     # Merkle proof verification tests
│   ├── test_signatures.py       # ECDSA signature tests
│   ├── test_sync.py             # Stateless sync tests
│   └── test_edge.py             # Edge case tests
└── README.md
```

---

## Requirements

- **Python 3.10+** — no system dependencies beyond Python itself
- **Phase 3 only:** `pip install cryptography`

---

## Quickstart

Always run from the **project root** so that `core/` is on the Python path.

### Install Phase 3 dependency
```powershell
pip install cryptography
```

### Run Phase 2 demo (unchanged)
```powershell
python phase2/simulation.py
```

### Run Phase 3 full demo
```powershell
python phase3/simulation.py
```

### Run benchmark suite
```powershell
python phase3/benchmark.py
```
Saves `benchmark_results.csv` in the project root.

### Run P2P multi-node demo
```powershell
python p2p/p2p_simulation.py
```

### Run test suite
```powershell
python -m pytest tests/ -v
```

---

## Configuration

All tuneable parameters live at the top of each script:

| Parameter | Default | Effect |
|---|---|---|
| `NUM_TRANSACTIONS` | 50–100 | Total transactions in simulation |
| `BLOCK_SIZE` | 10 | Transactions per block |
| `PRUNE_THRESHOLD` | 0.5 | Utility score below this → pruned |
| `EPOCH_THRESHOLD` | 3 | Epoch age for epoch-based baseline |
| `WEIGHTS` | value=0.5, freq=0.3, recency=0.2 | Utility scoring weight parameters |
| `P2P_PORTS` | 5010–5013 (sim) / 5000–5003 (demo) | Localhost ports for simulated nodes |
| `BENCHMARK_SIZES` | [100, 500, 1000, 5000] | Transaction counts for benchmarking |
| `THRESHOLDS` | [0.3, 0.5, 0.7] | Threshold sweep for benchmarking |

---

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| **Phase 1** | Concept, architecture, design | ✅ Complete |
| **Phase 2** | Core engine prototype and Proof of Utility modelling | ✅ Complete |
| **Phase 3** | P2P network, ECDSA signatures, stateless sync, benchmarking | ✅ Complete |
| **Phase 4** | Frontend dashboard, utility fee market, Proof of Reference | 🔲 Planned |
