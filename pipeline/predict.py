import os
import joblib
import json
from pipeline.encoders import load_feature_engineer
from pipeline.registry import ModelRegistry
from pipeline.explainability import PredictionExplainer

class TrendingPredictor:
    """
    Production inference engine with automatic cold-start routing
    and prediction calibration / confidence checks.
    """
    def __init__(self, version=None):
        self.registry = ModelRegistry()
        self.version = version
        self.fe = None
        self.model_content = None
        self.model_full = None
        self.model_baseline = None
        self.explainer_content = None
        self.explainer_full = None
        self.is_loaded = False
        
        self.load_active_models()

    def load_active_models(self):
        """Load the encoders and models for the designated version or current champion."""
        artifact_path = None
        
        if self.version is None:
            # 1. Look up active champion in SQLite registry and check physical directory
            champ = self.registry.get_champion()
            if champ and os.path.exists(champ["artifact_path"]):
                self.version = champ["version"]
                artifact_path = champ["artifact_path"]
            else:
                # 2. Check active_version.txt file fallback
                active_path = "model-store/active_version.txt"
                if os.path.exists(active_path):
                    with open(active_path) as f:
                        self.version = f.read().strip()
                    artifact_path = f"model-store/{self.version}"
                    if not os.path.exists(artifact_path):
                        self.version = None
                        artifact_path = None
                
                # 3. Fallback: Search all versions in registry for the first one that exists on disk
                if self.version is None:
                    all_versions = self.registry.get_all_versions()
                    for v_info in all_versions:
                        path = f"model-store/{v_info['version']}"
                        if os.path.exists(path):
                            self.version = v_info['version']
                            artifact_path = path
                            break
                            
                if self.version is None:
                    print("No active champion model found physically in registry or store.")
                    return
        else:
            version_info = self.registry.get_version(self.version)
            if version_info and os.path.exists(version_info["artifact_path"]):
                artifact_path = version_info["artifact_path"]
            else:
                artifact_path = f"model-store/{self.version}"
                if not os.path.exists(artifact_path):
                    print(f"Specified version '{self.version}' not found physically.")
                    return
                
        # Load from path
        encoders_path = f"{artifact_path}/encoders.joblib"
        model_content_path = f"{artifact_path}/model_content.joblib"
        model_full_path = f"{artifact_path}/model_full.joblib"
        model_baseline_path = f"{artifact_path}/model_baseline.joblib"
        
        if not (os.path.exists(encoders_path) and os.path.exists(model_content_path) and os.path.exists(model_full_path)):
            print(f"Model files missing at artifact path: {artifact_path}")
            return
            
        self.fe = load_feature_engineer(encoders_path)
        self.model_content = joblib.load(model_content_path)
        self.model_full = joblib.load(model_full_path)
        
        if os.path.exists(model_baseline_path):
            self.model_baseline = joblib.load(model_baseline_path)
            
        # Instantiate explainers
        self.explainer_content = PredictionExplainer(self.model_content, self.fe.content_feature_cols)
        self.explainer_full = PredictionExplainer(self.model_full, self.fe.full_feature_cols)
        
        self.is_loaded = True
        print(f"Successfully loaded model version: {self.version}")

    def predict(self, row_dict):
        """
        Execute prediction on a single input row.
        Routes to the correct model (Content-Only or Full) depending on cold-start status.
        """
        if not self.is_loaded:
            self.load_active_models()
            if not self.is_loaded:
                raise RuntimeError("Predictor cannot run because no model is loaded.")
                
        # 1. Transform raw inputs using feature pipeline
        feats, meta = self.fe.transform_row(row_dict)
        
        # 2. Check cold start routing
        is_cold_start = meta["cold_start"]
        
        if is_cold_start:
            # Route to Content-Only Model
            feature_cols = self.fe.content_feature_cols
            model = self.model_content
            explainer = self.explainer_content
            model_variant = "content_only"
        else:
            # Route to Full Model (includes channel historical statistics)
            feature_cols = self.fe.full_feature_cols
            model = self.model_full
            explainer = self.explainer_full
            model_variant = "full"
            
        # 3. Predict probability
        features_input = [[feats[col] for col in feature_cols]]
        proba = float(model.predict_proba(features_input)[0][1])
        label = "trending" if proba >= 0.50 else "not_trending"
        
        # 4. Generate SHAP/Feature Importance explanation
        explanation = explainer.explain(feats)
        
        # 5. Evaluate prediction honesty/grounded state
        # A prediction is NOT grounded if:
        # - The genre is completely unseen in training
        # - The language is completely unseen in training
        # - The probability is uncertain (confidence is close to boundary, e.g. 0.40 to 0.60)
        # Note: Unseen channel triggers cold-start, but it CAN still be grounded if the content is highly typical.
        is_uncertain = 0.40 <= proba <= 0.60
        unseen_categories = meta["genre_is_unseen"] or meta["language_is_unseen"]
        
        grounded = not (is_uncertain or unseen_categories)
        
        # Format the top features in output
        top_features_list = [d["feature"] for d in explanation["top_drivers"]]
        
        return {
            "trending_probability": round(proba, 4),
            "predicted_label": label if grounded else "uncertain",
            "model_version": f"{self.version}_{model_variant}",
            "top_features": top_features_list,
            "grounded": grounded,
            "cold_start": is_cold_start,
            "explanation": explanation
        }
