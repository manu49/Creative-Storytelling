from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CharacterCreate(BaseModel):
    name: str
    role: Optional[str] = None
    traits: Optional[str] = None
    backstory: Optional[str] = None
    arc_summary: Optional[str] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    traits: Optional[str] = None
    backstory: Optional[str] = None
    arc_summary: Optional[str] = None


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
