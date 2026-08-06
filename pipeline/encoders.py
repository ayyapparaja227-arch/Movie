import joblib
import os

def save_feature_engineer(fe, filepath):
    """Serialize the fitted FeatureEngineer instance containing all encodings and vocabularies."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(fe, filepath)

def load_feature_engineer(filepath):
    """Load the serialized FeatureEngineer instance."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"FeatureEngineer file not found at: {filepath}")
    return joblib.load(filepath)
