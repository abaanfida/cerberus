from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from core.crypto import compute_block_hash
from core.transaction import Transaction
from core.merkle import MerkleTree


@dataclass
class Block:
    block_id:     int
    epoch:        int
    prev_hash:    str
    transactions: list[Transaction]
    summary_hash: str = ""                # Merkle root — connects Phase 1 concept
    merkle_tree:  Optional[MerkleTree] = field(default=None, repr=False)
    block_hash:   str = ""               # SHA-256 of header fields

    def build_merkle(self):
        self.merkle_tree  = MerkleTree(self.transactions)
        self.summary_hash = self.merkle_tree.get_root()

    def seal(self):
        self.block_hash = compute_block_hash(self)  # must call after build_merkle

    def raw_size(self) -> int:
        return sum(tx.size_bytes() for tx in self.transactions)


    def to_dict(self) -> dict:
        return {
            "block_id":     self.block_id,
            "epoch":        self.epoch,
            "prev_hash":    self.prev_hash,
            "summary_hash": self.summary_hash,
            "block_hash":   self.block_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Block":
        txs = [Transaction.from_dict(t) for t in d.get("transactions", [])]
        b = cls(
            block_id     = d["block_id"],
            epoch        = d["epoch"],
            prev_hash    = d["prev_hash"],
            transactions = txs,
            summary_hash = d.get("summary_hash", ""),
            block_hash   = d.get("block_hash", ""),
        )
        return b

    def to_header_dict(self) -> dict:
        return {
            "index":        self.block_id,
            "summary_hash": self.summary_hash,
            "prev_hash":    self.prev_hash,
            "block_hash":   self.block_hash,
            "epoch":        self.epoch,
            "tx_count":     len(self.transactions),
        }
