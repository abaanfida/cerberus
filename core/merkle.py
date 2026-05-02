from typing import Optional
from core.crypto import sha256, hash_pair
from core.transaction import Transaction


class MerkleTree:
    def __init__(self, transactions: list[Transaction]):
        self._leaves = [sha256(tx.to_bytes()) for tx in transactions]
        self._tx_ids = [tx.tx_id for tx in transactions]
        self._tree: list[list[str]] = []
        self._root  = ""
        if self._leaves:
            self._build()

    def _build(self):
        level = list(self._leaves)
        self._tree = [level]
        while len(level) > 1:
            if len(level) % 2 == 1:       # duplicate last leaf when count is odd
                level = level + [level[-1]]
            level = [hash_pair(level[i], level[i + 1]) for i in range(0, len(level), 2)]
            self._tree.append(level)
        self._root = self._tree[-1][0]

    def get_root(self) -> str:
        return self._root

    def get_proof(self, tx_id: str) -> Optional[list[dict]]:
        if tx_id not in self._tx_ids:
            return None
        idx   = self._tx_ids.index(tx_id)
        proof = []
        for level in self._tree[:-1]:     # skip root level
            padded = level + ([level[-1]] if len(level) % 2 == 1 else [])
            if idx % 2 == 0:
                proof.append({"sibling": padded[idx + 1], "position": "right"})
            else:
                proof.append({"sibling": padded[idx - 1], "position": "left"})
            idx //= 2                     # move up one level
        return proof
