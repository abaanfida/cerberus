import sys
import os
import time
import csv
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.transaction import Transaction, compute_utility
from core.block import Block
from core.blockchain import Blockchain
from core.proof_store import ProofStore
from core.pruning import prune_chain, prune_chain_epoch
from core.verification import verify_all

BENCHMARK_SIZES = [100, 500, 1000, 5000]
THRESHOLDS      = [0.3, 0.5, 0.7]
BLOCK_SIZE      = 10
WEIGHTS         = {"value": 0.5, "frequency": 0.3, "recency": 0.2}
CURRENT_TIME    = 10_000
OUTPUT_CSV      = "benchmark_results.csv"

SEP = "-" * 78



def build_test_chain(n: int, seed: int = 42) -> tuple[Blockchain, int]:
    random.seed(seed)
    txs = []
    for i in range(n):
        tx = Transaction(
            tx_id        = f"bm_tx_{i:06d}",
            value        = random.uniform(0, 1),
            timestamp    = random.randint(0, CURRENT_TIME - 1),
            access_count = random.randint(0, 200),
        )
        tx.utility = compute_utility(tx, WEIGHTS, CURRENT_TIME)
        txs.append(tx)

    bc        = Blockchain()
    prev_hash = Blockchain.GENESIS_HASH
    for epoch, start in enumerate(range(0, n, BLOCK_SIZE)):
        block = Block(
            block_id     = epoch,
            epoch        = epoch,
            prev_hash    = prev_hash,
            transactions = txs[start : start + BLOCK_SIZE],
        )
        block.build_merkle()
        bc.add_block(block)
        prev_hash = block.block_hash

    return bc, bc.total_tx_size()


def compute_storage_ratio(chain_after: Blockchain, proof_store: ProofStore,
                           size_before: int) -> float:
    size_after = chain_after.total_tx_size() + proof_store.size_bytes()
    return size_after / max(size_before, 1)


def measure_tps(n: int) -> float:
    t0 = time.perf_counter()
    build_test_chain(n)
    elapsed = time.perf_counter() - t0
    return n / elapsed if elapsed > 0 else float("inf")



def run():
    print("=" * 78)
    print("  CERBERUS PHASE 3 — BENCHMARK SUITE")
    print("=" * 78)
    print(f"  Sizes: {BENCHMARK_SIZES}")
    print(f"  Thresholds: {THRESHOLDS}")
    print(f"  Block size: {BLOCK_SIZE}")
    print()

    results = []
    header = ["N", "threshold", "pou_ms", "epoch_ms", "verify_rate_pou",
              "verify_rate_epoch", "storage_ratio_pou", "storage_ratio_epoch", "tps"]

    print(f"{'N':>6}  {'theta':>6}  {'PoU ms':>9}  {'Epoch ms':>9}  "
          f"{'Verify%':>8}  {'E-Vfy%':>7}  {'StorPOU%':>9}  {'StorEP%':>8}  {'TPS':>8}")
    print(SEP)

    for N in BENCHMARK_SIZES:
        tps = measure_tps(N)

        for theta in THRESHOLDS:
            # Build two independent chains (same data, different pruning strategies)
            bc_pou,  size_before_pou  = build_test_chain(N)
            bc_ep,   size_before_ep   = build_test_chain(N)

            ps_pou = ProofStore()
            t0 = time.perf_counter()
            prune_chain(bc_pou, theta, ps_pou)
            pou_ms = (time.perf_counter() - t0) * 1000

            vpass_pou, vtot_pou = verify_all(ps_pou)
            verify_rate_pou = vpass_pou / vtot_pou if vtot_pou else 1.0
            storage_ratio_pou = compute_storage_ratio(bc_pou, ps_pou, size_before_pou)

            ps_ep = ProofStore()
            t0 = time.perf_counter()
            prune_chain_epoch(bc_ep, 3, ps_ep)
            epoch_ms = (time.perf_counter() - t0) * 1000

            vpass_ep, vtot_ep = verify_all(ps_ep)
            verify_rate_ep = vpass_ep / vtot_ep if vtot_ep else 1.0
            storage_ratio_ep = compute_storage_ratio(bc_ep, ps_ep, size_before_ep)

            row = [N, theta, round(pou_ms, 3), round(epoch_ms, 3),
                   round(verify_rate_pou, 4), round(verify_rate_ep, 4),
                   round(storage_ratio_pou, 4), round(storage_ratio_ep, 4),
                   round(tps, 1)]
            results.append(row)

            print(f"{N:>6}  {theta:>6.1f}  {pou_ms:>9.2f}  {epoch_ms:>9.2f}  "
                  f"{verify_rate_pou:>8.1%}  {verify_rate_ep:>7.1%}  "
                  f"{storage_ratio_pou:>9.1%}  {storage_ratio_ep:>8.1%}  {tps:>8.1f}")

        print(SEP)

    with open(OUTPUT_CSV, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(results)

    print(f"\n  Results saved to: {OUTPUT_CSV}")
    print("=" * 78)


if __name__ == "__main__":
    run()
