from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from chat_parade.soundboard import AUDIO_URL_PREFIX, TTS_URL_PREFIX, TtsCache
from chat_parade.viewer_store import ViewerEvent, ViewerStore

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def viewer_payload(store: ViewerStore, username: str) -> dict[str, Any]:
    viewer = store.get_or_create(username)
    status = store.status_for(username)
    return {
        "username": username,
        "nick": viewer.nick or username,
        "cor": viewer.cor,
        "chapeu": viewer.chapeu,
        "acessorio": viewer.acessorio,
        "is_mod": status.is_mod,
        "is_sub": status.is_sub,
        "is_broadcaster": status.is_broadcaster,
        # Seconds remaining, not a boolean: the client turns these into its own
        # deadlines and re-checks them every frame. A boolean computed here would
        # stay true on the client until the next broadcast happened to arrive.
        "dance_remaining": max(0.0, status.dancing_until - time.time()),
        "cheer_remaining": max(0.0, status.cheer_until - time.time()),
    }


def snapshot_payload(store: ViewerStore) -> dict[str, Any]:
    present = [
        viewer_payload(store, name)
        for name in store.usernames()
        if store.status_for(name).present
    ]
    return {"type": "snapshot", "viewers": present}


class OverlayBroadcaster:
    def __init__(self, store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"):
        self._store = store
        self._events = events
        self._connections: set[WebSocket] = set()

    async def register(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        await websocket.send_json(snapshot_payload(self._store))

    def unregister(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    @property
    def has_connections(self) -> bool:
        return bool(self._connections)

    async def run(self) -> None:
        while True:
            event = await self._events.get()
            # snapshot_payload only ever includes present viewers, so relaying an
            # update for an absent one would put an avatar on the overlay that
            # sync_present_chatters can never emit a "left" event for. !avatarmod
            # can name any username a mod types, including one never seen in chat.
            if event.type != "left" and not self._store.status_for(event.username).present:
                continue
            message = {
                "type": event.type,
                "username": event.username,
                "viewer": None if event.type == "left" else viewer_payload(self._store, event.username),
            }
            await self.broadcast(message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        stale = set()
        for connection in list(self._connections):
            try:
                await connection.send_json(message)
            except Exception:
                stale.add(connection)
        self._connections -= stale


def create_app(
    store: ViewerStore,
    events: "asyncio.Queue[ViewerEvent]",
    audio_dir: Path | None = None,
    tts_cache: TtsCache | None = None,
) -> tuple[FastAPI, OverlayBroadcaster]:
    app = FastAPI()
    broadcaster = OverlayBroadcaster(store, events)

    @app.middleware("http")
    async def _no_cache(request, call_next):
        # OBS's embedded browser (and regular browsers) cache the overlay
        # page/JS aggressively; without this, editing overlay.js and
        # reloading the Browser Source can silently keep serving the old file.
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/overlay")
    async def overlay_page() -> FileResponse:
        return FileResponse(WEB_DIR / "overlay.html")

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    # Soundboard clips and TTS are played by the overlay page itself (so OBS
    # captures them), which fetches them from here.
    if audio_dir is not None:
        # StaticFiles fails every request (HTTP 500) if its folder is missing,
        # so create it up front; it also shows the streamer where clips go.
        audio_dir.mkdir(parents=True, exist_ok=True)
        app.mount(AUDIO_URL_PREFIX, StaticFiles(directory=audio_dir), name="audios")

    if tts_cache is not None:
        @app.get(TTS_URL_PREFIX + "/{clip_id}")
        async def tts_clip(clip_id: str) -> Response:
            mp3 = tts_cache.get(clip_id)
            if mp3 is None:
                raise HTTPException(status_code=404)
            return Response(content=mp3, media_type="audio/mpeg")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await broadcaster.register(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            broadcaster.unregister(websocket)

    return app, broadcaster
