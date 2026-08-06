import numpy as np

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP is not available. Using feature importance fallback for explanations.")

class PredictionExplainer:
    """
    Computes per-prediction explanations using SHAP TreeExplainer if available,
    falling back to feature importance analysis to guarantee service availability.
    """
    def __init__(self, model, feature_names):
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        
        if SHAP_AVAILABLE:
            try:
                # CatBoostClassifier, RandomForestClassifier, etc.
                self.explainer = shap.TreeExplainer(model)
            except Exception as e:
                print(f"Failed to initialize SHAP TreeExplainer: {e}. Falling back.")
                self.explainer = None

    def explain(self, features_dict):
        """
        Explain a single prediction.
        Returns base value and a list of top drivers with contribution direction.
        """
        # Convert single features dict to 2D numpy array/DataFrame matching expected shape
        features_array = np.array([[features_dict[col] for col in self.feature_names]])
        
        # 1. Try SHAP first
        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(features_array)
                # handle binary classifier output structure
                # shap_values can be a list [class0, class1] or just class1 array depending on model
                if isinstance(shap_values, list):
                    values = shap_values[1][0]  # Class 1 (trending)
                elif len(shap_values.shape) == 3:  # (inputs, features, classes)
                    values = shap_values[0, :, 1]
                else:
                    values = shap_values[0]
                    
                feature_impact = sorted(
                    zip(self.feature_names, values),
                    key=lambda x: abs(x[1]), reverse=True
                )
                
                base_value = self.explainer.expected_value
                if isinstance(base_value, list) or isinstance(base_value, np.ndarray):
                    base_value = base_value[1]
                    
                return {
                    "base_value": float(base_value),
                    "explanation_type": "SHAP",
                    "top_drivers": [
                        {
                            "feature": name,
                            "value": float(features_dict[name]),
                            "shap_value": float(val),
                            "direction": "increases_trending" if val > 0 else "decreases_trending"
                        }
                        for name, val in feature_impact[:5]
                    ]
                }
            except Exception as e:
                print(f"SHAP explanation failed: {e}. Running fallback.")
                
        # 2. Fallback Explanation using Feature Importance
        # If model has feature_importances_
        feature_importances = None
        if hasattr(self.model, "feature_importances_"):
            feature_importances = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            # Logistic Regression coefficients
            feature_importances = np.abs(self.model.coef_[0])
            
        if feature_importances is not None:
            # Normalize to sum to 1
            total_imp = np.sum(feature_importances)
            if total_imp > 0:
                normalized_imp = feature_importances / total_imp
            else:
                normalized_imp = feature_importances
                
            impacts = []
            for name, imp in zip(self.feature_names, normalized_imp):
                # Simple heuristic: positive if feature value is higher than average (roughly)
                # For this fallback, we just return the feature importance
                impacts.append({
                    "feature": name,
                    "value": float(features_dict[name]),
                    "importance": float(imp),
                    "direction": "influential"
                })
            # Sort by importance
            impacts = sorted(impacts, key=lambda x: x["importance"], reverse=True)
            
            return {
                "base_value": 0.5,
                "explanation_type": "FeatureImportanceFallback",
                "top_drivers": impacts[:5]
            }
            
        # 3. Last Resort fallback
        return {
            "base_value": 0.5,
            "explanation_type": "None",
            "top_drivers": []
        }
