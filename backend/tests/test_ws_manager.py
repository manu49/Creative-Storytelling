"""Tests for the WebSocket ConnectionManager."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.ws.manager import ConnectionManager


pytestmark = pytest.mark.asyncio


def _make_ws():
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


async def test_connect_registers_websocket():
    manager = ConnectionManager()
    ws = _make_ws()
    await manager.connect("story-1", ws)
    assert ws in manager.active_connections["story-1"]
    ws.accept.assert_called_once()


async def test_connect_multiple_clients_same_story():
    manager = ConnectionManager()
    ws1, ws2 = _make_ws(), _make_ws()
    await manager.connect("story-1", ws1)
    await manager.connect("story-1", ws2)
    assert len(manager.active_connections["story-1"]) == 2


async def test_disconnect_removes_websocket():
    manager = ConnectionManager()
    ws = _make_ws()
    await manager.connect("story-1", ws)
    await manager.disconnect("story-1", ws)
    assert "story-1" not in manager.active_connections


async def test_disconnect_story_removed_when_empty():
    manager = ConnectionManager()
    ws = _make_ws()
    await manager.connect("story-1", ws)
    await manager.disconnect("story-1", ws)
    assert "story-1" not in manager.active_connections


async def test_disconnect_partial_removes_only_one():
    manager = ConnectionManager()
    ws1, ws2 = _make_ws(), _make_ws()
    await manager.connect("story-1", ws1)
    await manager.connect("story-1", ws2)
    await manager.disconnect("story-1", ws1)
    assert ws1 not in manager.active_connections["story-1"]
    assert ws2 in manager.active_connections["story-1"]


async def test_disconnect_nonexistent_story_is_safe():
    manager = ConnectionManager()
    ws = _make_ws()
    # Should not raise
    await manager.disconnect("no-such-story", ws)


async def test_broadcast_sends_to_all():
    manager = ConnectionManager()
    ws1, ws2 = _make_ws(), _make_ws()
    await manager.connect("story-1", ws1)
    await manager.connect("story-1", ws2)

    msg = {"type": "agent_update", "data": "hello"}
    await manager.broadcast_to_story("story-1", msg)

    expected = json.dumps(msg)
    ws1.send_text.assert_called_once_with(expected)
    ws2.send_text.assert_called_once_with(expected)


async def test_broadcast_no_connections_is_noop():
    manager = ConnectionManager()
    # Should not raise even with no subscribers
    await manager.broadcast_to_story("story-X", {"msg": "hi"})


async def test_broadcast_removes_dead_connections():
    manager = ConnectionManager()
    ws_dead = _make_ws()
    ws_dead.send_text = AsyncMock(side_effect=Exception("connection closed"))
    ws_live = _make_ws()

    await manager.connect("story-1", ws_dead)
    await manager.connect("story-1", ws_live)

    await manager.broadcast_to_story("story-1", {"msg": "test"})

    # Dead connection should have been cleaned up
    assert ws_dead not in manager.active_connections.get("story-1", set())
    # Live connection still present
    assert ws_live in manager.active_connections["story-1"]


async def test_send_personal():
    manager = ConnectionManager()
    ws = _make_ws()
    msg = {"type": "ping"}
    await manager.send_personal(ws, msg)
    ws.send_text.assert_called_once_with(json.dumps(msg))


async def test_send_personal_error_is_silent():
    manager = ConnectionManager()
    ws = _make_ws()
    ws.send_text = AsyncMock(side_effect=Exception("send failed"))
    # Should not raise
    await manager.send_personal(ws, {"type": "ping"})
