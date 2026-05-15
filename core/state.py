from core.transaction import Transaction

class State:
    def __init__(self):
        self.balances: dict[str, float] = {}
        self.processed_txs: set[str] = set()

    def apply_tx(self, tx: Transaction):
        account = tx.sender_pubkey.decode() if tx.sender_pubkey else tx.tx_id
        self.balances[account] = self.balances.get(account, 1000.0) - tx.value
        self.processed_txs.add(tx.tx_id)

    def size_bytes(self) -> int:
        return len(self.balances) * 64

    def is_processed(self, tx_id: str) -> bool:
        return tx_id in self.processed_txs
