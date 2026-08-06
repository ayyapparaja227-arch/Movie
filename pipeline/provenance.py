import hashlib
import json
import os
from datetime import datetime

def compute_provenance(model_path, data_path, seed, version):
    """
    Computes a cryptographic provenance record for auditability.
    Links the hash of the model binaries with the hash of the training dataset.
    """
    model_hash = "not_found"
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            model_hash = hashlib.sha256(f.read()).hexdigest()
            
    data_hash = "not_found"
    if os.path.exists(data_path):
        with open(data_path, "rb") as f:
            data_hash = hashlib.sha256(f.read()).hexdigest()
            
    provenance = {
        "version": version,
        "model_sha256": model_hash,
        "training_data_sha256": data_hash,
        "random_seed": seed,
        "timestamp": datetime.utcnow().isoformat(),
        "chain_hash": hashlib.sha256(f"{model_hash}:{data_hash}:{seed}".encode()).hexdigest()
    }
    
    return provenance

def save_provenance(provenance, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(provenance, f, indent=2)
