from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TestCase(BaseModel):
    title: str = Field(description="A descriptive title for the test case")
    steps: List[str] = Field(description="A step-by-step list of actions to perform the test")
    expected_result: str = Field(description="The expected outcome if the device is behaving correctly")

class TestCaseList(BaseModel):
    test_cases: List[TestCase]

# API Schemas

class NodeResponse(BaseModel):
    id: int
    logical_node_id: str
    heading: str
    level: int
    body_text: str
    content_hash: str
    children: List['NodeResponse'] = []
    
    class Config:
        from_attributes = True

class SelectionRequest(BaseModel):
    name: str
    node_ids: List[int]

class SelectionResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DiffResponse(BaseModel):
    status: str # "changed", "unchanged", "added"
    diff: str
    match_confidence: str # "high", "low"

class GenerationResponse(BaseModel):
    id: int
    selection_id: int
    generated_at: str
    generation_status: str
    parsed_test_cases: List[dict]
