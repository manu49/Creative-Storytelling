from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AgentTaskCreate(BaseModel):
    task_type: str
    priority: Optional[int] = 5
    input_context: Optional[str] = None
    scene_id: Optional[str] = None


class AgentTaskUpdate(BaseModel):
    status: Optional[str] = None
    suggestion: Optional[str] = None


class AgentTaskResponse(BaseModel):
    id: str
    story_id: str
    scene_id: Optional[str] = None
    task_type: str
    status: str
    priority: int
    input_context: Optional[str] = None
    suggestion: Optional[str] = None
    tool_calls_log: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
