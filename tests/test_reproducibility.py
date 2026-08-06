import pytest
import os
import shutil
from pipeline.training import run_training

def test_training_reproducibility():
    """Verify that training twice on the same dataset yields identical metrics."""
    dataset_path = "data/youtube_trending.csv"
    assert os.path.exists(dataset_path), "Mock training dataset does not exist!"
    
    # Run 1
    metrics1 = run_training(job_id="test_repr_1", csv_path=dataset_path, seed=42)
    # Run 2
    metrics2 = run_training(job_id="test_repr_2", csv_path=dataset_path, seed=42)
    
    # Assert F1 metrics match exactly for both Content-Only and Full models
    assert abs(metrics1["content_only"]["f1"] - metrics2["content_only"]["f1"]) < 1e-7, "Content-only model F1 differs!"
    assert abs(metrics1["full"]["f1"] - metrics2["full"]["f1"]) < 1e-7, "Full model F1 differs!"
    assert abs(metrics1["baseline_lr"]["f1"] - metrics2["baseline_lr"]["f1"]) < 1e-7, "Baseline LR F1 differs!"
    
    # Clean up test artifact runs
    for run in ["test_repr_1", "test_repr_2"]:
        dir_path = f"model-store/{run}"
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            
    print("Reproducibility test passed successfully.")
