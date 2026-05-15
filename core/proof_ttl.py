from typing import Optional
from core.transaction import Transaction
from core.proof_store import ProofStore

class TTLProofStore(ProofStore):
    def __init__(self, ttl_epochs: int = 5):
        super().__init__()
        self.ttl_epochs = ttl_epochs
        self.metadata: dict[str, dict] = {}

    def save(self, tx: Transaction, proof: list[dict], summary_hash: str, block_id: int, current_epoch: int = 0):
        super().save(tx, proof, summary_hash, block_id)
        if tx.tx_id not in self.metadata:
            self.metadata[tx.tx_id] = {
                "last_requested": current_epoch,
                "request_count": 0
            }

    def get(self, tx_id: str, current_epoch: int = 0) -> Optional[dict]:
        entry = super().get(tx_id)
        if entry:
            self.metadata[tx_id]["last_requested"] = current_epoch
            self.metadata[tx_id]["request_count"] += 1
        return entry

    def get_prunable_proofs(self, current_epoch: int) -> list[str]:
        return [
            tx_id for tx_id, meta in self.metadata.items()
            if (current_epoch - meta["last_requested"]) >= self.ttl_epochs
        ]

    def drop_proof(self, tx_id: str):
        if tx_id in self._store:
            del self._store[tx_id]
        if tx_id in self.metadata:
            del self.metadata[tx_id]

    def size_bytes(self) -> int:
        total = 0
        for entry in self._store.values():
            total += 1024 + entry["tx"].size_bytes()
        return total
