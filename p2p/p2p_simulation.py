import sys
import os
import time
import random

# Make sure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.transaction import Transaction, compute_utility
from core.block import Block
from core.blockchain import Blockchain
from core.proof_store import ProofStore
from core.pruning import prune_chain
from p2p.node import P2PNode

HOST          = "127.0.0.1"
PORTS         = [5000, 5001, 5002]
JOINER_PORT   = 5003
NUM_TX        = 30
BLOCK_SIZE    = 10
PRUNE_THRESH  = 0.5
WEIGHTS       = {"value": 0.5, "frequency": 0.3, "recency": 0.2}
CURRENT_TIME  = 1000

SEP = "-" * 64


def make_transactions(n: int, seed: int = 7) -> list[Transaction]:
    random.seed(seed)
    txs = []
    for i in range(n):
        tx = Transaction(
            tx_id        = f"p2p_tx_{i:04d}",
            value        = random.uniform(0, 1),
            timestamp    = random.randint(0, CURRENT_TIME - 1),
            access_count = random.randint(0, 200),
        )
        tx.utility = compute_utility(tx, WEIGHTS, CURRENT_TIME)
        txs.append(tx)
    return txs


def main():
    print("=" * 64)
    print("  CERBERUS P2P DEMO")
    print("=" * 64)

    chains  = [Blockchain() for _ in PORTS]
    stores  = [ProofStore()  for _ in PORTS]
    nodes   = [P2PNode(HOST, port, chains[i], stores[i]) for i, port in enumerate(PORTS)]

    for node in nodes:
        node.start()
    time.sleep(0.3)   # let sockets bind

    # Wire up peer mesh (each node knows all others)
    for i, node in enumerate(nodes):
        for j, port in enumerate(PORTS):
            if i != j:
                node.add_peer(HOST, port)

    txs       = make_transactions(NUM_TX)
    prev_hash = Blockchain.GENESIS_HASH

    print(f"\n[CHAIN] Mining {NUM_TX} transactions across {NUM_TX // BLOCK_SIZE} blocks on Node-0")
    print(SEP)

    for epoch, start in enumerate(range(0, NUM_TX, BLOCK_SIZE)):
        block_txs = txs[start : start + BLOCK_SIZE]
        block = Block(
            block_id     = epoch,
            epoch        = epoch,
            prev_hash    = prev_hash,
            transactions = block_txs,
        )
        block.build_merkle()
        chains[0].add_block(block)
        prev_hash = block.block_hash

        nodes[0].broadcast_block(block)
        time.sleep(0.1)   # let receiver threads process

    print(f"\n[NODE 5000] Chain length: {len(chains[0])} blocks")

    # Give peer nodes time to absorb all broadcasts
    time.sleep(0.5)

    for i, (chain, port) in enumerate(zip(chains, PORTS)):
        print(f"[NODE {port}] Chain length: {len(chain)} blocks")

    print(f"\n{SEP}")
    print("  RUNNING PoU PRUNING ON ALL NODES")
    print(SEP)

    for i, (chain, store, port) in enumerate(zip(chains, stores, PORTS)):
        pruned = prune_chain(chain, PRUNE_THRESH, store)
        print(f"[NODE {port}] Pruned {pruned} txs  |  Proof store: {store.count()} entries")

    print(f"\n{SEP}")
    print("  NODE-3 JOINING NETWORK via STATELESS SYNC")
    print(SEP)

    joiner_chain = Blockchain()
    joiner_store = ProofStore()
    joiner = P2PNode(HOST, JOINER_PORT, joiner_chain, joiner_store)
    joiner.start()
    time.sleep(0.2)

    success = joiner.sync_from(HOST, PORTS[0])
    print(f"[NODE {JOINER_PORT}] Sync {'succeeded' if success else 'FAILED'}")
    print(f"[NODE {JOINER_PORT}] Chain length after sync: {len(joiner_chain)} blocks")

    print(f"\n{'=' * 64}")
    print("  P2P DEMO COMPLETE")
    print(f"{'=' * 64}")

    # Stop all nodes
    for node in nodes:
        node.stop()
    joiner.stop()


if __name__ == "__main__":
    main()
