import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from phase4.simulation import run_simulation

def run():
    print("Running Cerberus Phase 4 Simulation...")
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    log_file = "storage_log.jsonl"
    csv_file = "storage_results.csv"

    if os.path.exists(log_file):
        os.remove(log_file)

    scales = [
        {"name": "Small", "epochs": 10, "txs": 50, "port": 8100},
        {"name": "Medium", "epochs": 50, "txs": 100, "port": 8200},
        {"name": "Large", "epochs": 200, "txs": 500, "port": 8300},
    ]

    all_results = []
    
    for scale in scales:
        print(f"\n--- Running {scale['name']} Scale ({scale['epochs']} epochs, {scale['txs']} txs/epoch) ---")
        guarantees = run_simulation(scale['epochs'], scale['txs'], log_file, scale['port'])
        
        # We need to map guarantees back to the storage log
        with open(log_file, "r") as f:
            lines = f.readlines()
            
        # Extract the metrics for this scale
        for line in lines[-len(guarantees) * 5:]: # 5 nodes per epoch
            metrics = json.loads(line)
            epoch = metrics["epoch"]
            g = guarantees[epoch]
            
            baseline = g["baseline_bytes"]
            savings_pct = max(0, (baseline - metrics["total_bytes"]) / baseline * 100)
            
            row = {
                "scale": scale['name'],
                "epoch": epoch,
                "node_id": metrics["node_id"],
                "headers_bytes": metrics["headers_bytes"],
                "block_bodies_bytes": metrics["block_bodies_bytes"],
                "transaction_bytes": metrics["transaction_bytes"],
                "proof_bytes": metrics["proof_bytes"],
                "state_bytes": metrics["state_bytes"],
                "total_bytes": metrics["total_bytes"],
                "baseline_bytes": baseline,
                "savings_pct": savings_pct,
                "proofs_held": g["proofs_held"],
                "proofs_guaranteed_by_network": g["proofs_guaranteed_by_network"],
                "guarantee_violations": g["guarantee_violations"]
            }
            all_results.append(row)

    with open(csv_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)
        
    print(f"\nSimulation complete. Results saved to {log_file} and {csv_file}.")

if __name__ == "__main__":
    run()
