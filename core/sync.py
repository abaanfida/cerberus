from __future__ import annotations
import socket
import json
from core.blockchain import Blockchain



def _send_recv(host: str, port: int, payload: dict, buf: int = 1 << 20) -> dict:
    msg = json.dumps(payload).encode()
    with socket.create_connection((host, port), timeout=5) as s:
        # Prefix the message length so the receiver knows when it is complete
        s.sendall(len(msg).to_bytes(4, "big") + msg)
        raw = _recv_all(s, buf)
    return json.loads(raw)


def _recv_all(sock: socket.socket, buf: int) -> bytes:
    raw_len = _recv_exact(sock, 4)
    msg_len = int.from_bytes(raw_len, "big")
    return _recv_exact(sock, msg_len)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed prematurely")
        data += chunk
    return data



def request_headers(peer_host: str, peer_port: int) -> list[dict]:
    resp = _send_recv(peer_host, peer_port, {"type": "get_headers"})
    return resp["headers"]


def sync_headers(local_chain: Blockchain, peer_host: str, peer_port: int) -> bool:
    headers = request_headers(peer_host, peer_port)
    print(f"[SYNC] Received {len(headers)} headers from {peer_host}:{peer_port}")

    if not headers:
        print("[SYNC] No headers received — peer chain is empty")
        return False

    # Validate DAG linkage
    for i, h in enumerate(headers):
        if i == 0:
            continue
        if h["prev_hash"] != headers[i - 1]["block_hash"]:
            print(f"[SYNC] Chain integrity FAILED at block {i}")
            print(f"       expected prev_hash: {headers[i-1]['block_hash'][:16]}…")
            print(f"       got      prev_hash: {h['prev_hash'][:16]}…")
            return False

    # Rebuild lightweight chain skeleton
    local_chain.sync_from_headers(headers)
    print(f"[SYNC] Chain integrity: VALID")
    print(f"[SYNC] Sync complete. Chain length: {len(headers)} blocks")
    return True


def request_proof(tx_id: str, peer_host: str, peer_port: int) -> list | None:
    resp = _send_recv(peer_host, peer_port, {"type": "get_proof", "tx_id": tx_id})
    return resp.get("proof")
