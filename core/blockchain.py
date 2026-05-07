from __future__ import annotations
from core.block import Block
from core.crypto import compute_block_hash
from core.transaction import Transaction


class Blockchain:
    GENESIS_HASH = "0" * 64

    def __init__(self):
        self.chain: list[Block] = []

    def add_block(self, block: Block):
        block.seal()
        self.chain.append(block)

    def is_valid(self) -> bool:
        for i, block in enumerate(self.chain):
            if compute_block_hash(block) != block.block_hash:  # header tampered?
                return False
            expected_prev = self.GENESIS_HASH if i == 0 else self.chain[i - 1].block_hash
            if block.prev_hash != expected_prev:               # chain broken?
                return False
        return True

    def total_tx_size(self) -> int:
        return sum(b.raw_size() for b in self.chain)

    def total_tx_count(self) -> int:
        return sum(len(b.transactions) for b in self.chain)

    def __len__(self):
        return len(self.chain)

    def __iter__(self):
        return iter(self.chain)


    def get_headers(self) -> list[dict]:
        return [block.to_header_dict() for block in self.chain]

    def sync_from_headers(self, headers: list[dict]) -> None:
        self.chain = []
        for h in headers:
            b = Block(
                block_id     = h["index"],
                epoch        = h["epoch"],
                prev_hash    = h["prev_hash"],
                transactions = [],
                summary_hash = h["summary_hash"],
                block_hash   = h["block_hash"],
            )
            self.chain.append(b)

    def to_api_dict(self) -> list[dict]:
        return [b.to_dict() for b in self.chain]
