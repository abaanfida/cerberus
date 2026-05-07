from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Transaction:
    tx_id:        str
    value:        float
    timestamp:    int
    access_count: int
    utility:      float = 0.0
    sender_pubkey: Optional[bytes] = field(default=None, repr=False)
    signature:     Optional[bytes] = field(default=None, repr=False)

    def to_bytes(self) -> bytes:
        return f"{self.tx_id}:{self.value:.6f}:{self.timestamp}:{self.access_count}".encode()

    def size_bytes(self) -> int:
        base = len(self.to_bytes())
        sig_size = len(self.signature) if self.signature else 0
        key_size = len(self.sender_pubkey) if self.sender_pubkey else 0
        return base + sig_size + key_size


    def sign(self, private_key) -> None:
        from core.crypto import sign_transaction
        self.signature = sign_transaction(self.tx_id, private_key)

    def verify_sig(self) -> bool:
        if self.signature is None or self.sender_pubkey is None:
            return False
        from core.crypto import verify_signature
        return verify_signature(self.tx_id, self.signature, self.sender_pubkey)

    def to_dict(self) -> dict:
        return {
            "tx_id":        self.tx_id,
            "value":        self.value,
            "timestamp":    self.timestamp,
            "access_count": self.access_count,
            "utility":      self.utility,
            "sender_pubkey": self.sender_pubkey.decode() if self.sender_pubkey else None,
            "signature":    self.signature.hex() if self.signature else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        return cls(
            tx_id        = d["tx_id"],
            value        = d["value"],
            timestamp    = d["timestamp"],
            access_count = d["access_count"],
            utility      = d.get("utility", 0.0),
            sender_pubkey= d["sender_pubkey"].encode() if d.get("sender_pubkey") else None,
            signature    = bytes.fromhex(d["signature"]) if d.get("signature") else None,
        )


def compute_utility(tx: Transaction, weights: dict, current_time: int) -> float:
    a, b, c  = weights["value"], weights["frequency"], weights["recency"]
    recency  = 1.0 / (current_time - tx.timestamp + 1)
    acc_norm = min(tx.access_count / 100.0, 1.0)   # soft-cap so score stays ~[0,1]
    return a * tx.value + b * acc_norm + c * recency
