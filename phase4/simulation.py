import sys
import os
import json
import random
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.transaction import Transaction, compute_utility
from core.block import Block
from core.blockchain import Blockchain
from core.state import State
from core.proof_ttl import TTLProofStore
from core.block_body_pruner import BlockBodyPruner
from core.storage_meter import measure_node_storage
from core.pruning import prune_chain
from p2p.node import P2PNode

WEIGHTS = {"value": 0.5, "frequency": 0.3, "recency": 0.2}

def generate_txs(n: int, current_time: int) -> list[Transaction]:
    txs = []
    for _ in range(n):
        tx_id = f"tx_{random.randint(1000000, 9999999)}"
        r = random.random()
        if r < 0.7:
            value = random.uniform(0.1, 10)
            access = random.randint(1, 5)
        elif r < 0.9:
            value = random.uniform(10, 100)
            access = random.randint(5, 50)
        else:
            value = random.uniform(100, 10000)
            access = random.randint(50, 500)
            
        tx = Transaction(
            tx_id=tx_id,
            value=value,
            timestamp=current_time,
            access_count=access
        )
        tx.utility = compute_utility(tx, WEIGHTS, current_time)
        txs.append(tx)
    return txs


class SimNode:
    def __init__(self, node_id: str, port: int, pruning_threshold: float):
        self.node_id = node_id
        self.port = port
        self.threshold = pruning_threshold
        self.blockchain = Blockchain()
        self.state = State()
        self.proof_store = TTLProofStore(ttl_epochs=5)
        self.p2p = P2PNode("127.0.0.1", port, self.blockchain, self.proof_store)
        self.body_pruner = BlockBodyPruner(self.state, self.proof_store, delay_epochs=3)


def run_simulation(epochs: int, txs_per_epoch: int, log_file: str, base_port: int) -> list:
    nodes = [
        SimNode("node_0_cons", base_port + 0, 0.3),
        SimNode("node_1_cons", base_port + 1, 0.3),
        SimNode("node_2_mod", base_port + 2, 0.5),
        SimNode("node_3_mod", base_port + 3, 0.5),
        SimNode("node_4_agg", base_port + 4, 0.7),
    ]

    for node in nodes:
        node.p2p.start()
    
    for i, node in enumerate(nodes):
        for j, peer in enumerate(nodes):
            if i != j:
                node.p2p.add_peer("127.0.0.1", peer.port)

    time.sleep(0.5)

    all_generated_txs = set()
    guarantees_log = []

    with open(log_file, "a") as fh:
        for epoch in range(epochs):
            new_txs = generate_txs(txs_per_epoch, epoch * 10)
            for tx in new_txs:
                all_generated_txs.add(tx.tx_id)

            for node in nodes:
                block = Block(
                    block_id=epoch,
                    epoch=epoch,
                    prev_hash=node.blockchain.chain[-1].block_hash if node.blockchain.chain else Blockchain.GENESIS_HASH,
                    transactions=[Transaction.from_dict(t.to_dict()) for t in new_txs] # Deep copy txs
                )
                block.build_merkle()
                node.blockchain.add_block(block)

                for tx in new_txs:
                    node.state.apply_tx(tx)

            for node in nodes:
                prune_chain(node.blockchain, node.threshold, node.proof_store)
                node.body_pruner.prune_chain(node.blockchain, epoch)

            for node in nodes:
                for tx_id in node.proof_store._store.keys():
                    node.p2p.broadcast_proof_update(tx_id, True)

            time.sleep(0.1)

            for node in nodes:
                prunable = node.proof_store.get_prunable_proofs(epoch)
                for tx_id in prunable:
                    if node.p2p.proof_registry.has_other_owners(tx_id, str(node.port)):
                        node.proof_store.drop_proof(tx_id)
                        node.p2p.broadcast_proof_update(tx_id, False)

            time.sleep(0.1)

            guarantee_violations = 0
            proofs_held = sum(node.proof_store.count() for node in nodes)
            all_pruned_txs = set()

            for tx_id in all_generated_txs:
                missing_in_some_node = False
                for node in nodes:
                    found = any(tx.tx_id == tx_id for b in node.blockchain.chain for tx in b.transactions)
                    if not found:
                        missing_in_some_node = True
                        break
                
                if missing_in_some_node:
                    all_pruned_txs.add(tx_id)
                    proof_found = any(node.proof_store.get(tx_id) is not None for node in nodes)
                    if not proof_found:
                        guarantee_violations += 1

            guarantees_log.append({
                "epoch": epoch,
                "proofs_held": proofs_held,
                "proofs_guaranteed_by_network": len(all_pruned_txs),
                "guarantee_violations": guarantee_violations,
                "baseline_bytes": (epoch + 1) * 80 + len(all_generated_txs) * 250 + 5 * 64 # Approximation for baseline
            })

            for node in nodes:
                metrics = measure_node_storage(node.node_id, epoch, node.blockchain, node.state, node.proof_store)
                fh.write(json.dumps(metrics) + "\n")

    for node in nodes:
        node.p2p.stop()
        
    return guarantees_log
