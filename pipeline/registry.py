import sqlite3
import json
import os
from datetime import datetime

class ModelRegistry:
    """
    Lightweight SQLite-backed Model Registry for tracking model lifecycles,
    champion/challenger promotions, metrics, and training lineage.
    """
    def __init__(self, db_path="model-store/registry.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    version TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    training_data_hash TEXT,
                    hyperparameters TEXT,      -- JSON string
                    metrics TEXT,              -- JSON string
                    feature_count INTEGER,
                    training_rows INTEGER,
                    random_seed INTEGER,
                    is_champion BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    promoted_at TIMESTAMP,
                    retired_at TIMESTAMP,
                    status TEXT DEFAULT 'staged'  -- staged | champion | retired
                )
            """)

    def register(self, version, model_type, artifact_path, data_hash, 
                 hyperparams, metrics, feature_count, training_rows, seed):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO models (
                    version, model_type, artifact_path, training_data_hash,
                    hyperparameters, metrics, feature_count, training_rows,
                    random_seed, is_champion, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'staged')
            """, (
                version, model_type, artifact_path, data_hash,
                json.dumps(hyperparams), json.dumps(metrics),
                feature_count, training_rows, seed,
                datetime.utcnow().isoformat()
            ))

    def promote_to_champion(self, version):
        """Demote current champion and promote the specified version to champion."""
        now = datetime.utcnow().isoformat()
        with self.conn:
            # Demote active champion
            self.conn.execute("""
                UPDATE models 
                SET is_champion = 0, status = 'retired', retired_at = ? 
                WHERE is_champion = 1
            """, (now,))
            # Promote new version
            self.conn.execute("""
                UPDATE models 
                SET is_champion = 1, status = 'champion', promoted_at = ? 
                WHERE version = ?
            """, (now, version))

    def get_champion(self):
        cur = self.conn.cursor()
        cur.execute("SELECT version, model_type, artifact_path, metrics FROM models WHERE is_champion = 1")
        row = cur.fetchone()
        if row:
            return {
                "version": row[0],
                "model_type": row[1],
                "artifact_path": row[2],
                "metrics": json.loads(row[3])
            }
        return None

    def get_version(self, version):
        cur = self.conn.cursor()
        cur.execute("SELECT version, model_type, artifact_path, metrics FROM models WHERE version = ?", (version,))
        row = cur.fetchone()
        if row:
            return {
                "version": row[0],
                "model_type": row[1],
                "artifact_path": row[2],
                "metrics": json.loads(row[3])
            }
        return None

    def get_all_versions(self):
        cur = self.conn.cursor()
        cur.execute("SELECT version, model_type, metrics, status, created_at FROM models ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [
            {
                "version": r[0],
                "model_type": r[1],
                "metrics": json.loads(r[2]),
                "status": r[3],
                "created_at": r[4]
            }
            for r in rows
        ]
