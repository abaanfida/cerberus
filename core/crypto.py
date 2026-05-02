import hashlib

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hash_pair(left: str, right: str) -> str:
    return sha256((left + right).encode())

def compute_block_hash(block) -> str:
    header = f"{block.block_id}|{block.prev_hash}|{block.summary_hash}|{block.epoch}"
    return sha256(header.encode())
