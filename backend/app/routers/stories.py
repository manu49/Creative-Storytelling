from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Story
from app.schemas import StoryCreate, StoryUpdate, StoryResponse, StoryDetailResponse
from uuid import uuid4

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("", response_model=List[StoryResponse])
async def list_stories(db: AsyncSession = Depends(get_db)):
    """List all stories"""
    result = await db.execute(select(Story))
    stories = result.scalars().all()
    return stories


@router.post("", response_model=StoryResponse, status_code=201)
async def create_story(story_data: StoryCreate, db: AsyncSession = Depends(get_db)):
    """Create a new story"""
    story = Story(
        id=str(uuid4()),
        title=story_data.title,
        genre=story_data.genre,
        logline=story_data.logline,
    )
    db.add(story)
    await db.commit()
    await db.refresh(story)
    return story


@router.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story(story_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific story with all scenes and characters"""
    result = await db.execute(
        select(Story)
        .filter(Story.id == story_id)
        .options(selectinload(Story.scenes), selectinload(Story.characters))
    )
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: str, story_data: StoryUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a story"""
    result = await db.execute(select(Story).filter(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if story_data.title:
        story.title = story_data.title
    if story_data.genre:
        story.genre = story_data.genre
    if story_data.logline:
        story.logline = story_data.logline
    if story_data.status:
        story.status = story_data.status

    await db.commit()
    await db.refresh(story)
    return story


@router.delete("/{story_id}", status_code=204)
async def delete_story(story_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a story"""
    result = await db.execute(select(Story).filter(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    await db.delete(story)
    await db.commit()
    return None
