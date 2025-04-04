# models.py
from pydantic import BaseModel
from typing import List, Optional

class SingleDescriptionRequest(BaseModel):
    description: str

class ItemResult(BaseModel):
    id_level: Optional[str] = None
    item_description: str
    selected_pdm: str
    filtered_pdms: List[str]
    confidence: Optional[float] = None

class PdmSelectResult(BaseModel):
    description: str
    pdms: str
    pdm_score: dict[str, float]

class ProcessRequest(BaseModel):
    file_id: str
    sample_size: int = 20
    similarity_threshold: float = 0.3
    llm_model: str = ""

class ProcessResponse(BaseModel):
    response: List[ItemResult]

class ProcessSingleResponse(BaseModel):
    response: ItemResult

class ProcessSingleResponseN8n(BaseModel):
    response: PdmSelectResult


