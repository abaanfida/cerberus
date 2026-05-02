from core.blockchain import Blockchain
from core.proof_store import ProofStore


def prune_chain(blockchain: Blockchain, threshold: float, proof_store: ProofStore) -> int:
    total_pruned = 0
    for block in blockchain:
        retained = []
        for tx in block.transactions:
            if tx.utility < threshold:
                proof = block.merkle_tree.get_proof(tx.tx_id) if block.merkle_tree else []
                proof_store.save(tx, proof, block.summary_hash, block.block_id)
                total_pruned += 1
            else:
                retained.append(tx)
        block.transactions = retained
    return total_pruned


def prune_chain_epoch(blockchain: Blockchain, epoch_thresh: int, proof_store: ProofStore) -> int:
    current_epoch = max(b.epoch for b in blockchain.chain) if blockchain.chain else 0
    total_pruned  = 0
    for block in blockchain:
        if (current_epoch - block.epoch) >= epoch_thresh:  # block is old enough to wipe
            for tx in block.transactions:
                proof = block.merkle_tree.get_proof(tx.tx_id) if block.merkle_tree else []
                proof_store.save(tx, proof, block.summary_hash, block.block_id)
            total_pruned += len(block.transactions)
            block.transactions = []
    return total_pruned
