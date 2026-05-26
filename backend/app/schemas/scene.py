from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SceneCreate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = ""
    scene_type: Optional[str] = "scene"
    order_index: Optional[int] = 0
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    characters_present: Optional[str] = None
    notes: Optional[str] = None


class SceneUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    scene_type: Optional[str] = None
    order_index: Optional[int] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    characters_present: Optional[str] = None
    notes: Optional[str] = None


class SceneResponse(BaseModel):
    id: str
    story_id: str
    title: Optional[str] = None
    content: str
    scene_type: str
    order_index: int
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    characters_present: Optional[str] = None
    notes: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
