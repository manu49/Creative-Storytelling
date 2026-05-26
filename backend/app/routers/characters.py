from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Character, Story
from app.schemas import CharacterCreate, CharacterUpdate, CharacterResponse
from uuid import uuid4

router = APIRouter(prefix="/stories/{story_id}/characters", tags=["characters"])


@router.post("", response_model=CharacterResponse, status_code=201)
async def create_character(
    story_id: str,
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new character"""
    # Verify story exists
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    if not story_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    character = Character(
        id=str(uuid4()),
        story_id=story_id,
        name=character_data.name,
        role=character_data.role,
        traits=character_data.traits,
        backstory=character_data.backstory,
        arc_summary=character_data.arc_summary,
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    story_id: str,
    character_id: str,
    character_data: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a character"""
    # Verify story exists
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    if not story_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    result = await db.execute(
        select(Character)
        .filter(Character.id == character_id)
        .filter(Character.story_id == story_id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if character_data.name is not None:
        character.name = character_data.name
    if character_data.role is not None:
        character.role = character_data.role
    if character_data.traits is not None:
        character.traits = character_data.traits
    if character_data.backstory is not None:
        character.backstory = character_data.backstory
    if character_data.arc_summary is not None:
        character.arc_summary = character_data.arc_summary

    await db.commit()
    await db.refresh(character)

    # TODO: Enqueue character_arc task

    return character


@router.delete("/{character_id}", status_code=204)
async def delete_character(
    story_id: str,
    character_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a character"""
    # Verify story exists
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    if not story_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    result = await db.execute(
        select(Character)
        .filter(Character.id == character_id)
        .filter(Character.story_id == story_id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    await db.delete(character)
    await db.commit()
    return None
