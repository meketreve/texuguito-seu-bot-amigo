from __future__ import annotations

import asyncio

import twitchio.errors
import uvicorn

from chat_parade.chatters_poller import run_chatters_poller
from chat_parade.config import Config, load_config
from chat_parade.points import PointsStore, run_points_loop
from chat_parade.soundboard import Soundboard, TtsCache
from chat_parade.token_manager import refresh_token, update_env_file
from chat_parade.twitch_chat import ChatParadeBot
from chat_parade.viewer_store import ViewerEvent, ViewerStore
from chat_parade.web_server import create_app


def build_components(config: Config):
    store = ViewerStore(config.data_dir / "viewers.json")
    points = PointsStore(config.data_dir / "points.json")
    events: "asyncio.Queue[ViewerEvent]" = asyncio.Queue()
    tts_cache = TtsCache()
    app, broadcaster = create_app(store, events, audio_dir=config.audio_dir, tts_cache=tts_cache)
    soundboard = Soundboard(config.audio_dir, tts_cache, broadcaster, volume=config.audio_volume)
    bot = ChatParadeBot(config, store, events, points, soundboard)
    return store, points, events, app, broadcaster, bot


async def _run_web_server(app, port: int) -> None:
    server_config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(server_config)
    serve_task = asyncio.ensure_future(server.serve())
    try:
        await asyncio.shield(serve_task)
    except asyncio.CancelledError:
        # Ask uvicorn to shut down on its own terms instead of cancelling it
        # mid-lifespan, which otherwise logs a spurious CancelledError traceback.
        server.should_exit = True
        await serve_task
        raise


async def _run_until_error(*coroutines) -> None:
    tasks = [asyncio.ensure_future(coro) for coro in coroutines]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            exc = task.exception()
            if exc is not None:
                raise exc
    except twitchio.errors.AuthenticationError:
        print("[texuguito] token da Twitch invalido ou expirado.")
        print("[texuguito] rode o run.bat de novo: ele refaz a conexao com a Twitch sozinho.")


def _load_and_refresh_config() -> Config:
    config = load_config()

    refreshed = refresh_token(config)
    if refreshed is None:
        print("[texuguito] não foi possível renovar o token, tentando conectar com o token atual...")
        return config

    update_env_file(refreshed.env_path, refreshed.token, refreshed.refresh_token)
    return refreshed


async def main() -> None:
    config = _load_and_refresh_config()
    store, points, events, app, broadcaster, bot = build_components(config)

    print(f"[texuguito] overlay pronto em: http://localhost:{config.overlay_port}/overlay")
    print("[texuguito] cole essa URL como Browser Source no OBS.")

    await _run_until_error(
        bot.start(),
        run_chatters_poller(config, store, events),
        run_points_loop(store, points),
        broadcaster.run(),
        _run_web_server(app, config.overlay_port),
    )


def run() -> None:
    """Entry point. Ctrl+C is the normal way to stop the app from a terminal,
    so it ends with a short message instead of a KeyboardInterrupt traceback."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("[texuguito] encerrado.")


if __name__ == "__main__":
    run()
