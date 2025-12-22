from pydantic import BaseModel
from typing import List, Optional

class SelectionRequest(BaseModel):
    dataset_id: str
    target_column: str
    metrics: List[str]
    
class DatasetMetadata(BaseModel):
    dataset_name: str
    task_type: str
    rows: int
    columns: int
    
class ModelInfo(BaseModel):
    name: str
    framework: str = "Unknown"
    default_params: dict = {}

class SelectionResponse(BaseModel):
    recommendation_id: str # Standardized name
    dataset_id: str
    task_type: str
    models: List[ModelInfo]
    # Legacy support if needed, or remove
    selection_id: str

class RecommendationResponse(BaseModel):
    recommendation_id: str
    dataset_id: str
    target_column: str
    metrics: List[str]
    task_type: str
    models: List[ModelInfo]
