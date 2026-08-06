import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

from pipeline.feature_engineering import FeatureEngineer
from pipeline.encoders import save_feature_engineer
from pipeline.registry import ModelRegistry

# Try importing CatBoost dynamically
try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("CatBoost is not available. Using Random Forest as primary model.")

def evaluate_model(model, X, y):
    """Compute standard metrics for binary classification."""
    y_pred = model.predict(X)
    # Check if predict_proba is available
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X)[:, 1]
    else:
        y_proba = y_pred.astype(float)
        
    return {
        "precision": float(precision_score(y, y_pred, zero_division=0)),
        "recall": float(recall_score(y, y_pred, zero_division=0)),
        "f1": float(f1_score(y, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, y_proba)),
        "pr_auc": float(average_precision_score(y, y_proba))
    }

def run_training(job_id=None, csv_path="data/youtube_trending.csv", seed=42):
    """
    Train Content-Only and Full model architectures.
    Performs train/val/test splits, handles imbalance, runs evaluations,
    and registers artifacts inside ModelRegistry.
    """
    if job_id is None:
        job_id = datetime.utcnow().strftime("run_%Y%m%d_%H%M%S")
        
    print(f"[{job_id}] Starting training run from: {csv_path}")
    
    # 1. Load raw data
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Training dataset not found: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # 2. Train/val/test split (70/15/15 split, fixed seed)
    train_df, test_val_df = train_test_split(df, test_size=0.30, random_state=seed, stratify=df['is_trending'])
    val_df, test_df = train_test_split(test_val_df, test_size=0.50, random_state=seed, stratify=test_val_df['is_trending'])
    
    # 3. Fit feature pipeline on train split
    fe = FeatureEngineer()
    fe.fit(train_df)
    
    # 4. Transform splits
    X_train_raw, y_train, _ = fe.transform_df(train_df)
    X_val_raw, y_val, _ = fe.transform_df(val_df)
    X_test_raw, y_test, _ = fe.transform_df(test_df)
    
    # Slice features for Content-Only vs Full models
    X_train_content = X_train_raw[fe.content_feature_cols]
    X_val_content = X_val_raw[fe.content_feature_cols]
    X_test_content = X_test_raw[fe.content_feature_cols]
    
    X_train_full = X_train_raw[fe.full_feature_cols]
    X_val_full = X_val_raw[fe.full_feature_cols]
    X_test_full = X_test_raw[fe.full_feature_cols]
    
    # Imbalance weights
    pos_count = int(np.sum(y_train == 1))
    neg_count = int(np.sum(y_train == 0))
    scale_pos_weight = neg_count / max(pos_count, 1)
    
    # 5. Model Selection & Training
    model_store_dir = f"model-store/{job_id}"
    os.makedirs(model_store_dir, exist_ok=True)
    
    metrics = {}
    
    # CONTENT-ONLY MODEL
    if CATBOOST_AVAILABLE:
        model_content = CatBoostClassifier(
            iterations=250,
            learning_rate=0.05,
            depth=6,
            random_seed=seed,
            scale_pos_weight=scale_pos_weight,
            verbose=0
        )
        model_content.fit(X_train_content, y_train, eval_set=(X_val_content, y_val), early_stopping_rounds=30)
        model_type = "catboost"
    else:
        model_content = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            random_state=seed,
            class_weight="balanced"
        )
        model_content.fit(X_train_content, y_train)
        model_type = "random_forest"
        
    metrics["content_only"] = evaluate_model(model_content, X_test_content, y_test)
    
    # FULL MODEL
    if CATBOOST_AVAILABLE:
        model_full = CatBoostClassifier(
            iterations=250,
            learning_rate=0.05,
            depth=6,
            random_seed=seed,
            scale_pos_weight=scale_pos_weight,
            verbose=0
        )
        model_full.fit(X_train_full, y_train, eval_set=(X_val_full, y_val), early_stopping_rounds=30)
    else:
        model_full = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            random_state=seed,
            class_weight="balanced"
        )
        model_full.fit(X_train_full, y_train)
        
    metrics["full"] = evaluate_model(model_full, X_test_full, y_test)
    
    # 6. Baseline: Logistic Regression (for comparison)
    lr = LogisticRegression(class_weight="balanced", random_state=seed, max_iter=1000)
    # Fit on full feature set (impute NaNs if any)
    lr.fit(X_train_full.fillna(0), y_train)
    metrics["baseline_lr"] = evaluate_model(lr, X_test_full.fillna(0), y_test)
    
    # 7. Save Encoders and Models
    save_feature_engineer(fe, f"{model_store_dir}/encoders.joblib")
    
    import joblib
    joblib.dump(model_content, f"{model_store_dir}/model_content.joblib")
    joblib.dump(model_full, f"{model_store_dir}/model_full.joblib")
    joblib.dump(lr, f"{model_store_dir}/model_baseline.joblib")
    
    # Save provenance hash chain
    from pipeline.provenance import compute_provenance, save_provenance
    prov = compute_provenance(
        model_path=f"{model_store_dir}/model_full.joblib",
        data_path=csv_path,
        seed=seed,
        version=job_id
    )
    save_provenance(prov, f"{model_store_dir}/provenance.json")
    
    # Save active pointer and metrics.json
    with open(f"{model_store_dir}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    # 8. Register in SQLite model registry
    registry = ModelRegistry()
    registry.register(
        version=job_id,
        model_type=model_type,
        artifact_path=model_store_dir,
        data_hash=job_id,  # Using job_id as simple data hash for mock
        hyperparams={"seed": seed, "scale_pos_weight": scale_pos_weight},
        metrics=metrics,
        feature_count=len(fe.full_feature_cols),
        training_rows=len(df),
        seed=seed
    )
    
    # Auto-promote to champion if F1 score of full model is > 0.4
    if metrics["full"]["f1"] > 0.4:
        registry.promote_to_champion(job_id)
        with open("model-store/active_version.txt", "w") as f:
            f.write(job_id)
            
    print(f"[{job_id}] Training completed successfully! Full F1: {metrics['full']['f1']:.3f}")
    return metrics

if __name__ == "__main__":
    run_training()
