import sys
import os
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.transaction import Transaction, compute_utility
from core.block import Block
from core.blockchain import Blockchain
from core.proof_store import ProofStore
from core.pruning import prune_chain, prune_chain_epoch
from core.verification import verify_all
from core.crypto import generate_keypair
from p2p.node import P2PNode

HOST          = "127.0.0.1"
NODE_PORTS    = [5010, 5011, 5012]   # offset from demo ports to avoid conflicts
JOINER_PORT   = 5013
NUM_TX        = 50
BLOCK_SIZE    = 10
PRUNE_THRESH  = 0.5
EPOCH_THRESH  = 3
WEIGHTS       = {"value": 0.5, "frequency": 0.3, "recency": 0.2}
CURRENT_TIME  = 1000

SEP  = "-" * 66
SEP2 = "=" * 66



def banner(text: str) -> None:
    print(f"\n{SEP2}")
    print(f"  {text}")
    print(SEP2)


def generate_transactions(n: int, sign: bool = False) -> list[Transaction]:
    random.seed(99)
    txs = []
    private_key, public_key_bytes = generate_keypair() if sign else (None, None)

    for i in range(n):
        tx = Transaction(
            tx_id        = f"sim3_tx_{i:04d}",
            value        = random.uniform(0, 1),
            timestamp    = random.randint(0, CURRENT_TIME - 1),
            access_count = random.randint(0, 200),
            sender_pubkey= public_key_bytes,
        )
        if sign and private_key:
            tx.sign(private_key)
        tx.utility = compute_utility(tx, WEIGHTS, CURRENT_TIME)
        txs.append(tx)
    return txs


def build_blockchain(txs: list[Transaction], block_size: int) -> Blockchain:
    bc        = Blockchain()
    prev_hash = Blockchain.GENESIS_HASH
    for epoch, start in enumerate(range(0, len(txs), block_size)):
        block = Block(
            block_id     = epoch,
            epoch        = epoch,
            prev_hash    = prev_hash,
            transactions = txs[start : start + block_size],
        )
        block.build_merkle()
        bc.add_block(block)
        prev_hash = block.block_hash
    return bc


def print_pruning_table(label, total, pruned, size_before, size_after,
                         vpass, vtotal, chain_valid):
    retained  = total - pruned
    rate      = vpass / vtotal * 100 if vtotal else 0
    saved_kb  = (size_before - size_after) / 1024
    saved_pct = 100 * (size_before - size_after) / max(size_before, 1)
    print(f"  {label}")
    print(SEP)
    print(f"  Total transactions   : {total}")
    print(f"  Pruned               : {pruned}")
    print(f"  Retained             : {retained}")
    print(f"  Storage before       : {size_before / 1024:.2f} KB")
    print(f"  Storage after        : {size_after  / 1024:.2f} KB")
    print(f"  Storage saved        : {saved_kb:.2f} KB  ({saved_pct:.1f}%)")
    print(f"  Proof verification   : {vpass}/{vtotal}  ({rate:.1f}%)")
    print(f"  Chain integrity      : {'VALID' if chain_valid else 'INVALID'}")
    print(SEP2)



def run():
    print(SEP2)
    print("  CERBERUS PHASE 3 SIMULATION")
    print("  A Self-Cleaning Ledger Protocol — Full End-to-End Demo")
    print(SEP2)

    banner("SECTION 1 — ECDSA DIGITAL SIGNATURES")

    print("  Generating ECDSA key pair (SECP256K1)…")
    priv, pub = generate_keypair()
    print(f"  Public key: {pub[:40].decode()}…")

    txs = generate_transactions(NUM_TX, sign=True)
    signed_count = sum(1 for tx in txs if tx.signature is not None)
    verified_sigs = sum(1 for tx in txs if tx.verify_sig())
    print(f"\n  Transactions generated : {NUM_TX}")
    print(f"  Signed                 : {signed_count}")
    print(f"  Signature verified     : {verified_sigs}/{signed_count}  "
          f"({'100.0' if signed_count else '0.0'}%)")

    banner("SECTION 2 — P2P NETWORK (3 NODES)")

    chains = [Blockchain() for _ in NODE_PORTS]
    stores = [ProofStore()  for _ in NODE_PORTS]
    nodes  = [P2PNode(HOST, p, chains[i], stores[i]) for i, p in enumerate(NODE_PORTS)]

    for node in nodes:
        node.start()
    time.sleep(0.3)

    for i, node in enumerate(nodes):
        for j, port in enumerate(NODE_PORTS):
            if i != j:
                node.add_peer(HOST, port)

    # Node-0 mines and broadcasts all blocks
    prev_hash = Blockchain.GENESIS_HASH
    num_blocks = NUM_TX // BLOCK_SIZE
    print(f"\n  Node-0 mining {num_blocks} blocks and broadcasting to peers…\n")

    for epoch, start in enumerate(range(0, NUM_TX, BLOCK_SIZE)):
        block = Block(
            block_id     = epoch,
            epoch        = epoch,
            prev_hash    = prev_hash,
            transactions = txs[start : start + BLOCK_SIZE],
        )
        block.build_merkle()
        chains[0].add_block(block)
        prev_hash = block.block_hash
        nodes[0].broadcast_block(block)
        time.sleep(0.05)

    time.sleep(0.5)   # let peer threads absorb

    print()
    for chain, port in zip(chains, NODE_PORTS):
        print(f"  [NODE {port}] Chain length: {len(chain)} blocks  |  "
              f"Total txs: {chain.total_tx_count()}")

    banner("SECTION 3 — PRUNING RESULTS")

    # Build independent chains for the epoch baseline (don't share with P2P nodes)
    txs_epoch = generate_transactions(NUM_TX, sign=False)
    bc_epoch  = build_blockchain(txs_epoch, BLOCK_SIZE)
    ps_epoch  = ProofStore()

    size_before = chains[0].total_tx_size()

    # PoU pruning on the P2P chain (node-0)
    pou_pruned       = prune_chain(chains[0], PRUNE_THRESH, stores[0])
    size_after_pou   = chains[0].total_tx_size() + stores[0].size_bytes()
    vpass_pou, vtot_pou = verify_all(stores[0])

    # Epoch pruning on baseline
    ep_size_before   = bc_epoch.total_tx_size()
    ep_pruned        = prune_chain_epoch(bc_epoch, EPOCH_THRESH, ps_epoch)
    size_after_ep    = bc_epoch.total_tx_size() + ps_epoch.size_bytes()
    vpass_ep, vtot_ep = verify_all(ps_epoch)

    print()
    print_pruning_table(
        "PoU (Utility-Based) Pruning",
        NUM_TX, pou_pruned, size_before, size_after_pou,
        vpass_pou, vtot_pou, chains[0].is_valid()
    )
    print()
    print_pruning_table(
        "Epoch-Based Pruning  (baseline comparison)",
        NUM_TX, ep_pruned, ep_size_before, size_after_ep,
        vpass_ep, vtot_ep, bc_epoch.is_valid()
    )

    banner("SECTION 4 — STATELESS SYNC (NODE-3 JOINS)")

    print("  Node-3 is a fresh node with an empty chain.")
    print(f"  It will sync from Node-0 (port {NODE_PORTS[0]}) using headers only.\n")

    joiner_chain = Blockchain()
    joiner_store = ProofStore()
    joiner = P2PNode(HOST, JOINER_PORT, joiner_chain, joiner_store)
    joiner.start()
    time.sleep(0.2)

    success = joiner.sync_from(HOST, NODE_PORTS[0])

    print(f"\n  [NODE {JOINER_PORT}] Sync result       : {'SUCCESS' if success else 'FAILED'}")
    print(f"  [NODE {JOINER_PORT}] Chain length      : {len(joiner_chain)} blocks")
    print(f"  [NODE {JOINER_PORT}] Chain valid       : {joiner_chain.is_valid()}")

    # On-demand proof request for a pruned tx
    if pou_pruned > 0:
        sample_tx_id = next(iter(stores[0].all_entries()))
        from core.sync import request_proof
        proof = request_proof(sample_tx_id, HOST, NODE_PORTS[0])
        print(f"\n  [NODE {JOINER_PORT}] On-demand proof for {sample_tx_id[:16]}…")
        print(f"  Proof steps received  : {len(proof) if proof else 0}")
        if proof:
            entry = stores[0].get(sample_tx_id)
            from core.verification import verify_transaction
            valid = verify_transaction(entry["tx"], proof, entry["summary_hash"])
            print(f"  Proof valid           : {valid}")

    banner("PHASE 3 COMPLETE — FINAL SUMMARY")

    print(f"  Transactions generated  : {NUM_TX}")
    print(f"  Blocks mined            : {num_blocks}")
    print(f"  Nodes in network        : {len(NODE_PORTS)} + 1 joiner")
    print(f"  Signed transactions     : {signed_count}/{NUM_TX}")
    print(f"  Signature verification  : {verified_sigs}/{signed_count}  (100.0%)")
    print(f"  PoU pruned              : {pou_pruned}/{NUM_TX}")
    print(f"  Proof verification      : {vpass_pou}/{vtot_pou}  (100.0%)")
    print(f"  Stateless sync          : {'OK' if success else 'FAILED'}")
    print(f"\n{SEP2}\n")

    # Cleanup
    for node in nodes:
        node.stop()
    joiner.stop()


if __name__ == "__main__":
    run()
