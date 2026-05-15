from __future__ import annotations
import socket
import threading
import json
import time
from core.blockchain import Blockchain
from core.block import Block
from core.transaction import Transaction
from core.proof_store import ProofStore
from p2p.proof_registry import ProofRegistry



def _send_msg(sock: socket.socket, payload: dict) -> None:
    data = json.dumps(payload).encode()
    sock.sendall(len(data).to_bytes(4, "big") + data)


def _recv_msg(sock: socket.socket) -> dict:
    raw_len = _recv_exact(sock, 4)
    msg_len = int.from_bytes(raw_len, "big")
    raw     = _recv_exact(sock, msg_len)
    return json.loads(raw)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed prematurely")
        data += chunk
    return data



class P2PNode:

    def __init__(self, host: str, port: int, blockchain: Blockchain,
                 proof_store: ProofStore | None = None):
        self.host        = host
        self.port        = port
        self.blockchain  = blockchain
        self.proof_store = proof_store or ProofStore()
        self.proof_registry = ProofRegistry()
        self.peers: list[tuple[str, int]] = []
        self.running     = False
        self._server_thread: threading.Thread | None = None
        self._lock = threading.Lock()   # protects blockchain writes


    def start(self) -> None:
        self.running = True
        self._server_thread = threading.Thread(
            target=self._listen, daemon=True, name=f"node-{self.port}"
        )
        self._server_thread.start()
        print(f"[NODE {self.port}] Listening on {self.host}:{self.port}")

    def stop(self) -> None:
        self.running = False


    def add_peer(self, host: str, port: int) -> None:
        if (host, port) not in self.peers and port != self.port:
            self.peers.append((host, port))


    def broadcast_block(self, block: Block) -> None:
        payload = {"type": "block", "data": block.to_dict()}
        self._broadcast(payload, label=f"block#{block.block_id}")

    def broadcast_tx(self, tx: Transaction) -> None:
        payload = {"type": "tx", "data": tx.to_dict()}
        self._broadcast(payload, label=f"tx:{tx.tx_id[:8]}")

    def broadcast_proof_update(self, tx_id: str, has_proof: bool) -> None:
        payload = {"type": "proof_update", "data": {"tx_id": tx_id, "node_id": str(self.port), "has_proof": has_proof}}
        self._broadcast(payload, label=f"proof_update:{tx_id[:8]}")

    def _broadcast(self, payload: dict, label: str = "") -> None:
        for host, port in self.peers:
            try:
                with socket.create_connection((host, port), timeout=2) as s:
                    _send_msg(s, payload)
                    print(f"[NODE {self.port}] -> {port}: sent {label}")
            except Exception as e:
                print(f"[NODE {self.port}] Peer {port} unreachable: {e}")


    def _listen(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(10)
            srv.settimeout(1.0)   # so we can check self.running periodically
            while self.running:
                try:
                    conn, addr = srv.accept()
                    threading.Thread(
                        target=self._handle, args=(conn,), daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except Exception:
                    if self.running:
                        raise

    def _handle(self, conn: socket.socket) -> None:
        try:
            with conn:
                msg = _recv_msg(conn)
                response = self._dispatch(msg)
                if response is not None:
                    _send_msg(conn, response)
        except Exception as e:
            print(f"[NODE {self.port}] Handler error: {e}")

    def _dispatch(self, msg: dict) -> dict | None:
        mtype = msg.get("type")

        if mtype == "block":
            self._on_block(msg["data"])
            return None

        elif mtype == "tx":
            self._on_tx(msg["data"])
            return None

        elif mtype == "get_headers":
            headers = self.blockchain.get_headers()
            return {"headers": headers}

        elif mtype == "get_proof":
            tx_id = msg.get("tx_id")
            entry = self.proof_store.get(tx_id)
            proof = entry["proof"] if entry else None
            return {"proof": proof}

        elif mtype == "proof_update":
            self._on_proof_update(msg["data"])
            return None

        else:
            print(f"[NODE {self.port}] Unknown message type: {mtype}")
            return None

    def _on_block(self, data: dict) -> None:
        block = Block.from_dict(data)
        with self._lock:
            # Only add if we don't already have this block
            existing_ids = {b.block_id for b in self.blockchain.chain}
            if block.block_id not in existing_ids:
                # Re-seal to recompute block_hash (avoids trusting peer hash directly)
                block.build_merkle()
                self.blockchain.add_block(block)
                print(f"[NODE {self.port}] Received block #{block.block_id} "
                      f"({len(block.transactions)} txs)")

    def _on_tx(self, data: dict) -> None:
        tx = Transaction.from_dict(data)
        print(f"[NODE {self.port}] Received tx {tx.tx_id[:12]}…")

    def _on_proof_update(self, data: dict) -> None:
        tx_id = data["tx_id"]
        node_id = data["node_id"]
        has_proof = data["has_proof"]
        self.proof_registry.update_proof(tx_id, node_id, has_proof)


    def sync_from(self, peer_host: str, peer_port: int) -> bool:
        from core.sync import sync_headers
        return sync_headers(self.blockchain, peer_host, peer_port)
