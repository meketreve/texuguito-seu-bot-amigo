import asyncio

from fastapi.testclient import TestClient

from chat_parade.viewer_store import ViewerStore
from chat_parade.web_server import OverlayBroadcaster, create_app


class _FakeConnection:
    """Minimal stand-in for a WebSocket: just needs send_json + set membership."""

    def __init__(self, release_event: asyncio.Event | None = None):
        self._release_event = release_event
        self.received: list[dict] = []

    async def send_json(self, message: dict) -> None:
        if self._release_event is not None:
            await self._release_event.wait()
        self.received.append(message)


def test_websocket_sends_initial_snapshot(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    store.get_or_create("fulano")
    store.status_for("fulano").present = True
    events: asyncio.Queue = asyncio.Queue()
    app, _ = create_app(store, events)

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()

    assert data["type"] == "snapshot"
    assert data["viewers"][0]["username"] == "fulano"


def test_websocket_snapshot_excludes_absent_viewers(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    store.get_or_create("ausente")  # never marked present
    events: asyncio.Queue = asyncio.Queue()
    app, _ = create_app(store, events)

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()

    assert data["viewers"] == []


def test_overlay_page_is_served(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    app, _ = create_app(store, events)

    client = TestClient(app)
    response = client.get("/overlay")

    assert response.status_code == 200
    assert b"parade" in response.content


async def test_broadcast_survives_connection_registered_mid_broadcast(tmp_path):
    """Regression test: a new websocket connecting while _broadcast is mid-await
    on another (slow) connection must not raise 'Set changed size during
    iteration' and must not stop the broadcast to the other connections."""
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    broadcaster = OverlayBroadcaster(store, events)

    release = asyncio.Event()
    slow = _FakeConnection(release_event=release)
    broadcaster._connections.add(slow)

    broadcast_task = asyncio.create_task(broadcaster._broadcast({"type": "test"}))
    await asyncio.sleep(0)  # let _broadcast start iterating and suspend on slow.send_json

    # Simulate a new client connecting concurrently (register() mutates the
    # same set) while _broadcast's for-loop still has a live iterator.
    newcomer = _FakeConnection()
    broadcaster._connections.add(newcomer)

    release.set()
    await broadcast_task  # must not raise RuntimeError

    assert slow.received == [{"type": "test"}]
