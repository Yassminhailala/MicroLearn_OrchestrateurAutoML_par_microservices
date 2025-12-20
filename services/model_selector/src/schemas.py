from pydantic import BaseModel
from typing import List, Optional

class DatasetMetadata(BaseModel):
    dataset_name: str
    task_type: str # "classification", "regression", "image"
    rows: int
    columns: int
    
class ModelCandidate(BaseModel):
    model_name: str
    justification: str
    priority: int

class SelectionResponse(BaseModel):
    recommended_models: List[ModelCandidate]
    selection_id: str
