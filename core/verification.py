from core.crypto import sha256, hash_pair
from core.transaction import Transaction
from core.proof_store import ProofStore


def verify_transaction(tx: Transaction, proof: list[dict], summary_hash: str) -> bool:
    current_hash = sha256(tx.to_bytes())
    for step in proof:
        if step["position"] == "right":
            current_hash = hash_pair(current_hash, step["sibling"])
        else:
            current_hash = hash_pair(step["sibling"], current_hash)
    return current_hash == summary_hash  # must match block's Merkle root


def verify_all(proof_store: ProofStore) -> tuple[int, int]:
    passed = 0
    total  = proof_store.count()
    for entry in proof_store.all_entries().values():
        if verify_transaction(entry["tx"], entry["proof"], entry["summary_hash"]):
            passed += 1
    return passed, total
