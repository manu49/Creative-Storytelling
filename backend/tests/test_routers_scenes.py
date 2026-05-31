"""Tests for /stories/{story_id}/scenes endpoints."""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def _create_story(client: AsyncClient, title: str = "Test Story") -> str:
    resp = await client.post("/stories", json={"title": title})
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_create_scene(client: AsyncClient):
    story_id = await _create_story(client)
    payload = {
        "title": "Opening Scene",
        "content": "The sun rose over the mountains.",
        "location": "Mountain pass",
    }
    resp = await client.post(f"/stories/{story_id}/scenes", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Opening Scene"
    assert data["story_id"] == story_id
    assert data["version"] == 1


async def test_create_scene_story_not_found(client: AsyncClient):
    resp = await client.post("/stories/bad-id/scenes", json={"title": "X", "content": "Y"})
    assert resp.status_code == 404


async def test_create_scene_minimal(client: AsyncClient):
    story_id = await _create_story(client)
    resp = await client.post(f"/stories/{story_id}/scenes", json={"title": "Minimal"})
    assert resp.status_code == 201
    assert resp.json()["content"] == ""


async def test_update_scene_content_increments_version(client: AsyncClient):
    story_id = await _create_story(client)
    create_resp = await client.post(
        f"/stories/{story_id}/scenes",
        json={"title": "Scene 1", "content": "Original content."},
    )
    scene_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/stories/{story_id}/scenes/{scene_id}",
        json={"content": "Revised content."},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["version"] == 2


async def test_update_scene_title_only_no_version_bump(client: AsyncClient):
    story_id = await _create_story(client)
    create_resp = await client.post(
        f"/stories/{story_id}/scenes",
        json={"title": "Scene", "content": "Content."},
    )
    scene_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/stories/{story_id}/scenes/{scene_id}",
        json={"title": "Better Title"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["version"] == 1  # no content change


async def test_update_scene_not_found(client: AsyncClient):
    story_id = await _create_story(client)
    resp = await client.put(
        f"/stories/{story_id}/scenes/bad-scene-id",
        json={"title": "X"},
    )
    assert resp.status_code == 404


async def test_update_scene_wrong_story(client: AsyncClient):
    story_id = await _create_story(client)
    other_story_id = await _create_story(client, "Other Story")
    scene_resp = await client.post(
        f"/stories/{story_id}/scenes", json={"title": "S", "content": "C"}
    )
    scene_id = scene_resp.json()["id"]

    # Try to update via the wrong story
    resp = await client.put(
        f"/stories/{other_story_id}/scenes/{scene_id}",
        json={"title": "X"},
    )
    assert resp.status_code == 404


async def test_delete_scene(client: AsyncClient):
    story_id = await _create_story(client)
    scene_resp = await client.post(
        f"/stories/{story_id}/scenes", json={"title": "Bye", "content": "Bye."}
    )
    scene_id = scene_resp.json()["id"]

    del_resp = await client.delete(f"/stories/{story_id}/scenes/{scene_id}")
    assert del_resp.status_code == 204


async def test_delete_scene_not_found(client: AsyncClient):
    story_id = await _create_story(client)
    resp = await client.delete(f"/stories/{story_id}/scenes/no-such-scene")
    assert resp.status_code == 404
