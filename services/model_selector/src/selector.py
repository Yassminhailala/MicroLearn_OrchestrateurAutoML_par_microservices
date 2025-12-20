from typing import List
from .schemas import DatasetMetadata, ModelCandidate

class ModelSelector:
    @staticmethod
    def select_models(metadata: DatasetMetadata) -> List[ModelCandidate]:
        candidates = []
        
        # 1. Image Data
        if metadata.task_type.lower() == "image":
            candidates.append(ModelCandidate(
                model_name="Recall CNN (Custom)",
                justification="Image data detected. CNNs are state-of-the-art for visual tasks.",
                priority=1
            ))
            return candidates

        # 2. Tabular Data (Classification/Regression assumed for now if not image)
        # Size definitions
        is_small = metadata.rows < 1000
        is_medium = 1000 <= metadata.rows < 50000
        is_large = metadata.rows >= 50000
        
        # Rule 1: Small Dataset -> SVM
        if is_small:
            candidates.append(ModelCandidate(
                model_name="SVM (Support Vector Machine)",
                justification="Dataset is small (<1k rows). SVMs are efficient and effective for small, high-dimensional spaces.",
                priority=1
            ))
            # Also suggest Random Forest as a robust alternative
            candidates.append(ModelCandidate(
                model_name="RandomForest",
                justification="Robust baseline for tabular data.",
                priority=2
            ))

        # Rule 2: Medium Dataset -> Random Forest
        elif is_medium:
            candidates.append(ModelCandidate(
                model_name="RandomForest",
                justification="Dataset is medium sized (1k-50k rows). RandomForest balances performance and interpretability well here.",
                priority=1
            ))
            candidates.append(ModelCandidate(
                model_name="XGBoost",
                justification="Boosting often outperforms bagging on structured data, worth trying.",
                priority=2
            ))

        # Rule 3: Large Dataset -> XGBoost
        elif is_large:
            candidates.append(ModelCandidate(
                model_name="XGBoost",
                justification="Dataset is large (>50k rows). Gradient boosting scales well and provides high accuracy.",
                priority=1
            ))
            # Neural Net for large tabular is also an option, but let's stick to the requested list
            candidates.append(ModelCandidate(
                model_name="RandomForest",
                justification="Parallelizable training makes it a viable candidate for large datasets too.",
                priority=2
            ))
            
        return candidates

selector = ModelSelector()
