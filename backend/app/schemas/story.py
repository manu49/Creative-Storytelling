from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict


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


class CharacterResponse(BaseModel):
    id: str
    story_id: str
    name: str
    role: Optional[str] = None
    traits: Optional[str] = None
    backstory: Optional[str] = None
    arc_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoryCreate(BaseModel):
    title: str
    genre: Optional[str] = None
    logline: Optional[str] = None


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    logline: Optional[str] = None
    status: Optional[str] = None


class StoryResponse(BaseModel):
    id: str
    title: str
    genre: Optional[str] = None
    logline: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoryDetailResponse(StoryResponse):
    """Story with all nested scenes and characters"""
    scenes: List[SceneResponse] = []
    characters: List[CharacterResponse] = []
