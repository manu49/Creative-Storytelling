from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Story
from io import BytesIO

router = APIRouter(prefix="/stories/{story_id}/export", tags=["export"])


@router.get("")
async def export_story(
    story_id: str,
    format: str = "markdown",
    db: AsyncSession = Depends(get_db),
):
    """Export story as Markdown or PDF"""
    result = await db.execute(select(Story).filter(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if format == "markdown":
        return export_markdown(story)
    elif format == "pdf":
        return export_pdf(story)
    else:
        raise HTTPException(status_code=400, detail="Invalid format")


def export_markdown(story) -> StreamingResponse:
    """Export story as Markdown"""
    lines = []

    # Title
    lines.append(f"# {story.title}\n")

    # Metadata
    if story.genre:
        lines.append(f"**Genre:** {story.genre}\n")
    if story.logline:
        lines.append(f"**Logline:** {story.logline}\n")
    lines.append("")

    # Table of contents
    if story.scenes:
        lines.append("## Table of Contents\n")
        for idx, scene in enumerate(story.scenes, 1):
            title = scene.title or f"Scene {idx}"
            lines.append(f"{idx}. {title}")
        lines.append("")

    # Scenes
    for idx, scene in enumerate(story.scenes, 1):
        title = scene.title or f"Scene {idx}"
        lines.append(f"## {idx}. {title}\n")

        if scene.location:
            lines.append(f"**Location:** {scene.location}\n")
        if scene.time_of_day:
            lines.append(f"**Time:** {scene.time_of_day}\n")

        lines.append(scene.content)
        lines.append("\n---\n")

    markdown = "\n".join(lines)
    content = markdown.encode("utf-8")

    return StreamingResponse(
        iter([content]),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={story.title}.md"},
    )


def export_pdf(story) -> StreamingResponse:
    """Export story as PDF (simple text-based)"""
    # For simplicity, return a markdown-like text file with .pdf extension
    # In production, use a proper PDF library like reportlab or weasyprint
    lines = []

    lines.append(f"{'=' * 60}")
    lines.append(f"{story.title.upper()}")
    lines.append(f"{'=' * 60}\n")

    if story.genre:
        lines.append(f"Genre: {story.genre}")
    if story.logline:
        lines.append(f"Logline: {story.logline}\n")

    for idx, scene in enumerate(story.scenes, 1):
        title = scene.title or f"Scene {idx}"
        lines.append(f"\n{'-' * 40}")
        lines.append(f"SCENE {idx}: {title}")
        lines.append(f"{'-' * 40}\n")

        if scene.location:
            lines.append(f"Location: {scene.location}")
        if scene.time_of_day:
            lines.append(f"Time: {scene.time_of_day}\n")

        lines.append(scene.content)
        lines.append("")

    content = "\n".join(lines).encode("utf-8")

    return StreamingResponse(
        iter([content]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={story.title}.pdf"},
    )
