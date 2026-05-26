from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Scene, Story
from app.schemas import SceneCreate, SceneUpdate, SceneResponse
from app.services.story_manager import StoryManager
from uuid import uuid4

router = APIRouter(prefix="/stories/{story_id}/scenes", tags=["scenes"])


@router.post("", response_model=SceneResponse, status_code=201)
async def create_scene(
    story_id: str,
    scene_data: SceneCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new scene"""
    # Verify story exists
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    if not story_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    scene = Scene(
        id=str(uuid4()),
        story_id=story_id,
        title=scene_data.title,
        content=scene_data.content or "",
        scene_type=scene_data.scene_type or "scene",
        order_index=scene_data.order_index or 0,
        location=scene_data.location,
        time_of_day=scene_data.time_of_day,
        characters_present=scene_data.characters_present,
        notes=scene_data.notes,
    )
    db.add(scene)
    await db.commit()
    await db.refresh(scene)

    # Enqueue agent tasks
    await StoryManager.enqueue_scene_tasks(db, story_id, scene.id)

    return scene


@router.put("/{scene_id}", response_model=SceneResponse)
async def update_scene(
    story_id: str,
    scene_id: str,
    scene_data: SceneUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a scene"""
    # Verify story exists
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    if not story_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    result = await db.execute(
        select(Scene).filter(Scene.id == scene_id).filter(Scene.story_id == story_id)
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    if scene_data.title is not None:
        scene.title = scene_data.title
    if scene_data.content is not None:
        scene.content = scene_data.content
        scene.version += 1
    if scene_data.scene_type is not None:
        scene.scene_type = scene_data.scene_type
    if scene_data.order_index is not None:
        scene.order_index = scene_data.order_index
    if scene_data.location is not None:
        scene.location = scene_data.location
    if scene_data.time_of_day is not None:
        scene.time_of_day = scene_data.time_of_day
    if scene_data.characters_present is not None:
        scene.characters_present = scene_data.characters_present
    if scene_data.notes is not None:
        scene.notes = scene_data.notes

    await db.commit()
    await db.refresh(scene)

    # Enqueue grammar_fix task if content changed
    if scene_data.content is not None:
        await StoryManager.enqueue_task(
            db, story_id, "grammar_fix", priority=3, scene_id=scene_id
        )

    return scene


@router.delete("/{scene_id}", status_code=204)
async def delete_scene(
    story_id: str,
    scene_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a scene"""
    # Verify story exists
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    if not story_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    result = await db.execute(
        select(Scene).filter(Scene.id == scene_id).filter(Scene.story_id == story_id)
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    await db.delete(scene)
    await db.commit()
    return None
