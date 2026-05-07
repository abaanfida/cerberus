import hashlib
from typing import Optional


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hash_pair(left: str, right: str) -> str:
    return sha256((left + right).encode())

def compute_block_hash(block) -> str:
    header = f"{block.block_id}|{block.prev_hash}|{block.summary_hash}|{block.epoch}"
    return sha256(header.encode())



try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    from cryptography.exceptions import InvalidSignature
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False


def generate_keypair():
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError("pip install cryptography  — required for Phase 3 signatures")
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key_bytes = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_key, public_key_bytes


def sign_transaction(tx_hash: str, private_key) -> bytes:
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError("pip install cryptography  — required for Phase 3 signatures")
    return private_key.sign(tx_hash.encode(), ec.ECDSA(hashes.SHA256()))


def verify_signature(tx_hash: str, signature: bytes, public_key_bytes: bytes) -> bool:
    if not _CRYPTO_AVAILABLE:
        return False
    try:
        pub = load_pem_public_key(public_key_bytes)
        pub.verify(signature, tx_hash.encode(), ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, Exception):
        return False
