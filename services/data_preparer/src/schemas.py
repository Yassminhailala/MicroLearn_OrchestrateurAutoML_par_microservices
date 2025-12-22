from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any

class PipelineStep(BaseModel):
    operator: str  # e.g., "StandardScaler", "SimpleImputer"
    params: Optional[Dict[str, Any]] = {}

class DataLocation(BaseModel):
    bucket: str
    path: str

class PreparationRequest(BaseModel):
    input_data: DataLocation
    pipeline: List[PipelineStep]
    output_path: Optional[str] = None # Optional override

class PreparationResponse(BaseModel):
    job_id: str
    dataset_id: str
    status: str
    output_location: Optional[DataLocation] = None
