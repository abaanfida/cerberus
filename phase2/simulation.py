import random
from core import (
    Transaction, Block, Blockchain,
    ProofStore, prune_chain, prune_chain_epoch, verify_all
)
from core.transaction import compute_utility

NUM_TRANSACTIONS = 100
BLOCK_SIZE       = 10
PRUNE_THRESHOLD  = 0.5

WEIGHTS = {
    "value":     0.5,
    "frequency": 0.3,
    "recency":   0.2,
}

EPOCH_THRESHOLD = 3
CURRENT_TIME    = 1000

SEP  = "─" * 62
SEP2 = "═" * 62


def generate_transactions(n: int) -> list[Transaction]:
    random.seed(42)
    return [
        Transaction(
            tx_id        = f"tx_{i:04d}",
            value        = random.uniform(0, 1),
            timestamp    = random.randint(0, CURRENT_TIME - 1),
            access_count = random.randint(0, 200),
        )
        for i in range(n)
    ]


def build_blockchain(txs: list[Transaction], block_size: int) -> Blockchain:
    bc        = Blockchain()
    prev_hash = Blockchain.GENESIS_HASH
    for epoch, i in enumerate(range(0, len(txs), block_size)):
        block = Block(
            block_id     = epoch,
            epoch        = epoch,
            prev_hash    = prev_hash,
            transactions = txs[i : i + block_size],
        )
        block.build_merkle()
        bc.add_block(block)
        prev_hash = block.block_hash  # each block links to previous
    return bc


def print_metrics(label, total, pruned, retained, size_before, size_after,
                  verify_pass, verify_total, chain_valid):
    rate      = (verify_pass / verify_total * 100) if verify_total else 0.0
    saved_kb  = (size_before - size_after) / 1024
    saved_pct = 100 * (size_before - size_after) / max(size_before, 1)
    print(SEP2)
    print(f"  {label}")
    print(SEP)
    print(f"  Total Transactions       : {total}")
    print(f"  Pruned Transactions      : {pruned}")
    print(f"  Retained Transactions    : {retained}")
    print(f"  Storage Before Pruning   : {size_before / 1024:.3f} KB")
    print(f"  Storage After Pruning    : {size_after / 1024:.3f} KB")
    print(f"  Storage Saved            : {saved_kb:.3f} KB  ({saved_pct:.1f}%)")
    print(f"  Proof Verification Rate  : {verify_pass}/{verify_total}  ({rate:.1f}%)")
    print(f"  Chain Integrity Valid    : {'YES' if chain_valid else 'NO'}")
    print(SEP2)


def run_simulation():
    txs = generate_transactions(NUM_TRANSACTIONS)
    for tx in txs:
        tx.utility = compute_utility(tx, WEIGHTS, CURRENT_TIME)

    bc_pou   = build_blockchain(txs, BLOCK_SIZE)
    bc_epoch = build_blockchain(txs, BLOCK_SIZE)  # separate chain for baseline comparison

    size_before = bc_pou.total_tx_size()

    proof_store_pou   = ProofStore()
    pruned_pou        = prune_chain(bc_pou, PRUNE_THRESHOLD, proof_store_pou)
    size_after_pou    = bc_pou.total_tx_size() + proof_store_pou.size_bytes()
    pass_pou, tot_pou = verify_all(proof_store_pou)

    proof_store_ep    = ProofStore()
    pruned_ep         = prune_chain_epoch(bc_epoch, EPOCH_THRESHOLD, proof_store_ep)
    size_after_ep     = bc_epoch.total_tx_size() + proof_store_ep.size_bytes()
    pass_ep, tot_ep   = verify_all(proof_store_ep)

    print("\n")
    print_metrics("UTILITY-BASED (PoU) PRUNING",
                  NUM_TRANSACTIONS, pruned_pou, NUM_TRANSACTIONS - pruned_pou,
                  size_before, size_after_pou, pass_pou, tot_pou, bc_pou.is_valid())
    print()
    print_metrics("EPOCH-BASED PRUNING  (baseline)",
                  NUM_TRANSACTIONS, pruned_ep, NUM_TRANSACTIONS - pruned_ep,
                  size_before, size_after_ep, pass_ep, tot_ep, bc_epoch.is_valid())
    print()

    print(SEP)
    print("  Per-Block Breakdown")
    print(f"  {'Blk':>3}  {'Ep':>3}  {'Kept':>4}  {'Pruned':>6}  "
          f"{'summary_hash[:12]':18}  block_hash[:12]")
    print(SEP)
    for b in bc_pou.chain:
        pruned_count = BLOCK_SIZE - len(b.transactions)
        print(f"  {b.block_id:>3}  {b.epoch:>3}  {len(b.transactions):>4}  "
              f"{pruned_count:>6}  {b.summary_hash[:12]}…  {b.block_hash[:12]}…")
    print(SEP)
    print()


if __name__ == "__main__":
    run_simulation()
