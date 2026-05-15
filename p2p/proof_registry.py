class ProofRegistry:
    def __init__(self):
        self.registry: dict[str, set[str]] = {}

    def update_proof(self, tx_id: str, node_id: str, has_proof: bool):
        if has_proof:
            self.registry.setdefault(tx_id, set()).add(node_id)
        else:
            if tx_id in self.registry:
                self.registry[tx_id].discard(node_id)
                if not self.registry[tx_id]:
                    del self.registry[tx_id]

    def has_other_owners(self, tx_id: str, my_node_id: str) -> bool:
        owners = self.registry.get(tx_id, set())
        return len(owners - {my_node_id}) > 0
