from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict


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
    scenes: List = []
    characters: List = []
