import asyncio
import contextlib
import time

from fastapi.testclient import TestClient

from chat_parade.viewer_store import ViewerEvent, ViewerStore
from chat_parade.web_server import OverlayBroadcaster, create_app, viewer_payload


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


def test_payload_sends_remaining_seconds_not_booleans(tmp_path):
    """Regression test: the payload must carry how long the animation still has
    to run, not a boolean snapshot. A boolean is only true at broadcast time and
    the client has no way to expire it, so viewers danced forever."""
    store = ViewerStore(tmp_path / "v.json")
    store.trigger_dance("fulano")
    store.trigger_cheer("fulano")

    payload = viewer_payload(store, "fulano")

    assert "dancing" not in payload
    assert "cheering" not in payload
    assert 0 < payload["dance_remaining"] <= 4.0
    assert 0 < payload["cheer_remaining"] <= 4.0


def test_payload_remaining_is_zero_once_the_animation_expired(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    store.get_or_create("fulano")
    status = store.status_for("fulano")
    status.dancing_until = time.time() - 10
    status.cheer_until = time.time() - 10

    payload = viewer_payload(store, "fulano")

    assert payload["dance_remaining"] == 0.0
    assert payload["cheer_remaining"] == 0.0


def test_payload_sends_raw_cor_chapeu_acessorio_not_a_grid(tmp_path):
    """Regression test: the client now renders real sprites from these three
    raw fields directly; a pre-rendered pixel grid is no longer part of the
    contract, and re-adding one would be dead weight sent over every
    broadcast."""
    store = ViewerStore(tmp_path / "v.json")
    store.set_color("fulano", "#ff8800")
    store.set_chapeu("fulano", "coroa")
    store.set_acessorio("fulano", "asas")

    payload = viewer_payload(store, "fulano")

    assert payload["cor"] == "#ff8800"
    assert payload["chapeu"] == "coroa"
    assert payload["acessorio"] == "asas"
    assert "grid" not in payload


def test_overlay_page_is_served(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    app, _ = create_app(store, events)

    client = TestClient(app)
    response = client.get("/overlay")

    assert response.status_code == 200
    assert b"parade" in response.content


def test_overlay_page_and_script_are_never_cached(tmp_path):
    """Regression test: OBS's Browser Source (and regular browsers) cache the
    overlay page/JS aggressively. Without a no-store header, editing
    overlay.js and reloading can silently keep serving the old file."""
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    app, _ = create_app(store, events)

    client = TestClient(app)

    overlay_response = client.get("/overlay")
    script_response = client.get("/static/overlay.js")

    assert overlay_response.headers["cache-control"] == "no-store"
    assert script_response.headers["cache-control"] == "no-store"


async def _drain(broadcaster: OverlayBroadcaster, events: asyncio.Queue) -> None:
    """Run OverlayBroadcaster.run() long enough to consume the queued events.

    _FakeConnection.send_json never suspends, so a handful of event-loop turns is
    more than enough for run() to process everything already on the queue.
    """
    task = asyncio.create_task(broadcaster.run())
    try:
        for _ in range(10):
            await asyncio.sleep(0)
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    assert events.empty()


async def test_run_skips_updates_for_viewers_that_are_not_present(tmp_path):
    """Regression test: !avatarmod accepts any username a mod types, including
    one never seen in chat. get_or_create makes a ViewerStatus with
    present=False, and sync_present_chatters can never emit "left" for someone
    who was never present - so broadcasting the update stranded a ghost avatar
    on the overlay until the browser source was reloaded."""
    store = ViewerStore(tmp_path / "v.json")
    store.get_or_create("nunca-visto")  # never marked present
    events: asyncio.Queue = asyncio.Queue()
    broadcaster = OverlayBroadcaster(store, events)
    connection = _FakeConnection()
    broadcaster._connections.add(connection)

    await events.put(ViewerEvent(type="updated", username="nunca-visto"))
    await _drain(broadcaster, events)

    assert connection.received == []


async def test_run_broadcasts_updates_for_present_viewers(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    store.mark_status_from_message("presente", is_mod=False, is_sub=False, is_broadcaster=False)
    events: asyncio.Queue = asyncio.Queue()
    broadcaster = OverlayBroadcaster(store, events)
    connection = _FakeConnection()
    broadcaster._connections.add(connection)

    await events.put(ViewerEvent(type="updated", username="presente"))
    await _drain(broadcaster, events)

    assert len(connection.received) == 1
    assert connection.received[0]["type"] == "updated"
    assert connection.received[0]["viewer"]["username"] == "presente"


async def test_run_always_broadcasts_left_events(tmp_path):
    """A "left" event is emitted precisely when present has just flipped to
    False, so the presence guard must never suppress it."""
    store = ViewerStore(tmp_path / "v.json")
    store.get_or_create("saiu")
    events: asyncio.Queue = asyncio.Queue()
    broadcaster = OverlayBroadcaster(store, events)
    connection = _FakeConnection()
    broadcaster._connections.add(connection)

    await events.put(ViewerEvent(type="left", username="saiu"))
    await _drain(broadcaster, events)

    assert connection.received == [{"type": "left", "username": "saiu", "viewer": None}]


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
