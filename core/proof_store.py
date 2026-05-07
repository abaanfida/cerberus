from __future__ import annotations
import json
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


    def save_to_file(self, path: str) -> None:
        data = {}
        for tx_id, entry in self._store.items():
            data[tx_id] = {
                "tx":           entry["tx"].to_dict(),
                "proof":        entry["proof"],      # list of {"sibling": hex, "position": str}
                "summary_hash": entry["summary_hash"],
                "block_id":     entry["block_id"],
            }
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)

    def load_from_file(self, path: str) -> None:
        with open(path, "r") as fh:
            data = json.load(fh)
        for tx_id, entry in data.items():
            self._store[tx_id] = {
                "tx":           Transaction.from_dict(entry["tx"]),
                "proof":        entry["proof"],
                "summary_hash": entry["summary_hash"],
                "block_id":     entry["block_id"],
            }

    def to_api_dict(self) -> dict:
        out = {}
        for tx_id, entry in self._store.items():
            out[tx_id] = {
                "tx":           entry["tx"].to_dict(),
                "proof":        entry["proof"],
                "summary_hash": entry["summary_hash"],
                "block_id":     entry["block_id"],
            }
        return out
