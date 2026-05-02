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
