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
