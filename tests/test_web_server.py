import asyncio

from fastapi.testclient import TestClient

from chat_parade.viewer_store import ViewerStore
from chat_parade.web_server import create_app


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
