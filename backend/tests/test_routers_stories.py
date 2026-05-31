"""Tests for /stories CRUD endpoints."""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_list_stories_empty(client: AsyncClient):
    resp = await client.get("/stories")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_story(client: AsyncClient):
    payload = {"title": "My Epic Tale", "genre": "novel", "logline": "A hero's journey."}
    resp = await client.post("/stories", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My Epic Tale"
    assert data["genre"] == "novel"
    assert data["status"] == "draft"
    assert "id" in data


async def test_create_story_minimal(client: AsyncClient):
    resp = await client.post("/stories", json={"title": "Minimal Story"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Minimal Story"
    assert data["genre"] is None


async def test_create_story_missing_title(client: AsyncClient):
    resp = await client.post("/stories", json={"genre": "novel"})
    assert resp.status_code == 422


async def test_list_stories_after_create(client: AsyncClient):
    await client.post("/stories", json={"title": "Story A"})
    await client.post("/stories", json={"title": "Story B"})
    resp = await client.get("/stories")
    assert resp.status_code == 200
    titles = [s["title"] for s in resp.json()]
    assert "Story A" in titles
    assert "Story B" in titles


async def test_get_story(client: AsyncClient):
    create_resp = await client.post("/stories", json={"title": "Get Me"})
    story_id = create_resp.json()["id"]

    resp = await client.get(f"/stories/{story_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == story_id
    assert data["title"] == "Get Me"
    assert "scenes" in data
    assert "characters" in data


async def test_get_story_not_found(client: AsyncClient):
    resp = await client.get("/stories/nonexistent-id")
    assert resp.status_code == 404


async def test_update_story(client: AsyncClient):
    create_resp = await client.post("/stories", json={"title": "Old Title"})
    story_id = create_resp.json()["id"]

    resp = await client.put(f"/stories/{story_id}", json={"title": "New Title", "status": "active"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New Title"
    assert data["status"] == "active"


async def test_update_story_not_found(client: AsyncClient):
    resp = await client.put("/stories/bad-id", json={"title": "X"})
    assert resp.status_code == 404


async def test_delete_story(client: AsyncClient):
    create_resp = await client.post("/stories", json={"title": "Delete Me"})
    story_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/stories/{story_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/stories/{story_id}")
    assert get_resp.status_code == 404


async def test_delete_story_not_found(client: AsyncClient):
    resp = await client.delete("/stories/nonexistent")
    assert resp.status_code == 404
