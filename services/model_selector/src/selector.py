from typing import List
from pydantic import BaseModel

# Internal model for selection logic (not exposed via API)
class ModelCandidate(BaseModel):
    model_name: str
    justification: str
    priority: int

class ModelSelector:
    @staticmethod
    def select_models(task_type: str, rows: int, cols: int, metrics: List[str]) -> List[ModelCandidate]:
        candidates = []
        
        # 1. Image Data
        if task_type.lower() == "image":
            candidates.append(ModelCandidate(
                model_name="Recall CNN",
                justification="Image data detected. CNNs are state-of-the-art for visual tasks.",
                priority=1
            ))
            candidates.append(ModelCandidate(
                model_name="ResNet50",
                justification="ResNet50 is a powerful deep learning model for image classification with residual learning.",
                priority=2
            ))
            return candidates

        # 2. Tabular Data
        is_small = rows < 1000
        is_medium = 1000 <= rows < 50000
        is_large = rows >= 50000
        
        # Determine prefix based on task
        suffix = "Classifier" if task_type == "Classification" else "Regressor"
        
        # Logic Table
        if is_small:
            # Small Dataset
            candidates.append(ModelCandidate(
                model_name=f"SVM {suffix}",
                justification=f"Dataset is small ({rows} rows). SVMs work well in high-dimensional spaces with limited samples.",
                priority=1
            ))
            candidates.append(ModelCandidate(
                model_name=f"RandomForest {suffix}",
                justification="Robust baseline that resists overfitting on small data.",
                priority=2
            ))
            
        elif is_medium:
             # Medium Dataset
            candidates.append(ModelCandidate(
                model_name=f"RandomForest {suffix}",
                justification=f"Dataset is medium sized ({rows} rows). RandomForest offers a great balance of accuracy and interpretability.",
                priority=1
            ))
            candidates.append(ModelCandidate(
                model_name=f"XGBoost {suffix}",
                justification="Gradient Boosting often provides state-of-the-art performance on structured data.",
                priority=2
            ))
            
        elif is_large:
            # Large Dataset
            candidates.append(ModelCandidate(
                model_name=f"XGBoost {suffix}",
                justification=f"Dataset is large ({rows} rows). XGBoost is highly optimized for performance and speed on large datasets.",
                priority=1
            ))
            candidates.append(ModelCandidate(
                model_name=f"LightGBM {suffix}",
                justification="Faster training speed and lower memory usage for very large datasets.",
                priority=2
            ))

        return candidates

selector = ModelSelector()
