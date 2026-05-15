from core.blockchain import Blockchain
from core.state import State
from core.proof_store import ProofStore

def measure_node_storage(node_id: str, epoch: int, blockchain: Blockchain, state: State, proof_store: ProofStore) -> dict:
    headers_bytes = len(blockchain.chain) * 80
    block_bodies_bytes = 0
    transaction_bytes = 0

    for b in blockchain.chain:
        if b.transactions:
            # The block body overhead itself is something small
            block_bodies_bytes += 32
            for tx in b.transactions:
                transaction_bytes += tx.size_bytes()

    proof_bytes = proof_store.size_bytes()
    state_bytes = state.size_bytes()

    total_bytes = headers_bytes + block_bodies_bytes + transaction_bytes + proof_bytes + state_bytes

    return {
        "epoch": epoch,
        "node_id": node_id,
        "headers_bytes": headers_bytes,
        "block_bodies_bytes": block_bodies_bytes,
        "transaction_bytes": transaction_bytes,
        "proof_bytes": proof_bytes,
        "state_bytes": state_bytes,
        "total_bytes": total_bytes
    }
