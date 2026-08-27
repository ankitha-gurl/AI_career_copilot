from typing import Optional
from pydantic import BaseModel


class RoadmapRequest(BaseModel):
    target_role: str
    job_id: Optional[int] = None


class RoadmapItemOut(BaseModel):
    order_index: int
    phase_title: str
    skill: Optional[str] = None
    priority: Optional[str] = None
    difficulty: Optional[str] = None
    prerequisites: Optional[str] = None
    project_task: Optional[str] = None
    success_criteria: Optional[str] = None

    class Config:
        from_attributes = True


class RoadmapOut(BaseModel):
    id: int
    target_role: Optional[str] = None
    items: list[RoadmapItemOut]

    class Config:
        from_attributes = True
