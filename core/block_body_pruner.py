from core.blockchain import Blockchain
from core.state import State
from core.proof_store import ProofStore

class BlockBodyPruner:
    def __init__(self, state: State, proof_store: ProofStore, delay_epochs: int = 2):
        self.state = state
        self.proof_store = proof_store
        self.delay_epochs = delay_epochs

    def prune_chain(self, blockchain: Blockchain, current_epoch: int) -> int:
        total_pruned = 0
        for block in blockchain.chain:
            if not block.transactions:
                continue
            if (current_epoch - block.epoch) >= self.delay_epochs:
                # Never drop a block body if any tx in it hasn't been processed
                if all(self.state.is_processed(tx.tx_id) for tx in block.transactions):
                    for tx in block.transactions:
                        proof = block.merkle_tree.get_proof(tx.tx_id) if block.merkle_tree else []
                        if hasattr(self.proof_store, 'ttl_epochs'):
                            self.proof_store.save(tx, proof, block.summary_hash, block.block_id, current_epoch=current_epoch)
                        else:
                            self.proof_store.save(tx, proof, block.summary_hash, block.block_id)
                    total_pruned += len(block.transactions)
                    block.transactions = []
        return total_pruned
