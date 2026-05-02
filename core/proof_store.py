from typing import Optional
from core.transaction import Transaction


class ProofStore:
    def __init__(self):
        self._store: dict = {}

    def save(self, tx: Transaction, proof: list[dict], summary_hash: str, block_id: int):
        self._store[tx.tx_id] = {
            "proof":        proof,
            "tx":           tx,
            "summary_hash": summary_hash,
            "block_id":     block_id,
        }

    def get(self, tx_id: str) -> Optional[dict]:
        return self._store.get(tx_id)

    def count(self) -> int:
        return len(self._store)

    def all_entries(self) -> dict:
        return self._store

    def size_bytes(self) -> int:
        total = 0
        for entry in self._store.values():
            proof_bytes = sum(len(s["sibling"]) for s in entry["proof"]) if entry["proof"] else 0
            total += proof_bytes + entry["tx"].size_bytes()
        return total
