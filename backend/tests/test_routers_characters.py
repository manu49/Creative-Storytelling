"""Tests for /stories/{story_id}/characters endpoints."""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def _create_story(client: AsyncClient) -> str:
    resp = await client.post("/stories", json={"title": "Character Test Story"})
    return resp.json()["id"]


async def test_create_character(client: AsyncClient):
    story_id = await _create_story(client)
    payload = {
        "name": "Alice",
        "role": "protagonist",
        "traits": "brave, curious",
        "backstory": "Grew up in a small village.",
    }
    resp = await client.post(f"/stories/{story_id}/characters", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alice"
    assert data["story_id"] == story_id
    assert data["role"] == "protagonist"


async def test_create_character_story_not_found(client: AsyncClient):
    resp = await client.post("/stories/bad-id/characters", json={"name": "Bob"})
    assert resp.status_code == 404


async def test_create_character_missing_name(client: AsyncClient):
    story_id = await _create_story(client)
    resp = await client.post(f"/stories/{story_id}/characters", json={"role": "villain"})
    assert resp.status_code == 422


async def test_update_character(client: AsyncClient):
    story_id = await _create_story(client)
    create_resp = await client.post(
        f"/stories/{story_id}/characters",
        json={"name": "Charlie", "role": "mentor"},
    )
    char_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/stories/{story_id}/characters/{char_id}",
        json={"arc_summary": "Teaches the hero and sacrifices himself."},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["arc_summary"] == "Teaches the hero and sacrifices himself."


async def test_update_character_not_found(client: AsyncClient):
    story_id = await _create_story(client)
    resp = await client.put(
        f"/stories/{story_id}/characters/bad-id",
        json={"name": "X"},
    )
    assert resp.status_code == 404


async def test_delete_character(client: AsyncClient):
    story_id = await _create_story(client)
    create_resp = await client.post(
        f"/stories/{story_id}/characters", json={"name": "Doomed"}
    )
    char_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/stories/{story_id}/characters/{char_id}")
    assert del_resp.status_code == 204


async def test_delete_character_not_found(client: AsyncClient):
    story_id = await _create_story(client)
    resp = await client.delete(f"/stories/{story_id}/characters/nonexistent")
    assert resp.status_code == 404


async def test_character_appears_in_story_detail(client: AsyncClient):
    story_id = await _create_story(client)
    await client.post(
        f"/stories/{story_id}/characters", json={"name": "Eve", "role": "sidekick"}
    )
    detail_resp = await client.get(f"/stories/{story_id}")
    assert detail_resp.status_code == 200
    chars = detail_resp.json()["characters"]
    assert any(c["name"] == "Eve" for c in chars)
