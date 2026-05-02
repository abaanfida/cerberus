from dataclasses import dataclass


@dataclass
class Transaction:
    tx_id:        str
    value:        float
    timestamp:    int
    access_count: int
    utility:      float = 0.0

    def to_bytes(self) -> bytes:
        return f"{self.tx_id}:{self.value:.6f}:{self.timestamp}:{self.access_count}".encode()

    def size_bytes(self) -> int:
        return len(self.to_bytes())


def compute_utility(tx: Transaction, weights: dict, current_time: int) -> float:
    a, b, c  = weights["value"], weights["frequency"], weights["recency"]
    recency  = 1.0 / (current_time - tx.timestamp + 1)
    acc_norm = min(tx.access_count / 100.0, 1.0)  # soft-cap so score stays ~[0,1]
    return a * tx.value + b * acc_norm + c * recency
