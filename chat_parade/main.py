from __future__ import annotations

import asyncio

import twitchio.errors
import uvicorn

from chat_parade.chatters_poller import run_chatters_poller
from chat_parade.config import Config, load_config
from chat_parade.twitch_chat import ChatParadeBot
from chat_parade.viewer_store import ViewerEvent, ViewerStore
from chat_parade.web_server import create_app


def build_components(config: Config):
    store = ViewerStore(config.data_dir / "viewers.json")
    events: "asyncio.Queue[ViewerEvent]" = asyncio.Queue()
    app, broadcaster = create_app(store, events)
    bot = ChatParadeBot(config, store, events)
    return store, events, app, broadcaster, bot


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
        print("[chat-parade] token da Twitch invalido ou expirado.")
        print("[chat-parade] gere um token novo (veja 'Se o token expirar' no README) e tente de novo.")


async def main() -> None:
    config = load_config()
    store, events, app, broadcaster, bot = build_components(config)

    print(f"[chat-parade] overlay pronto em: http://localhost:{config.overlay_port}/overlay")
    print("[chat-parade] cole essa URL como Browser Source no OBS.")

    await _run_until_error(
        bot.start(),
        run_chatters_poller(config, store, events),
        broadcaster.run(),
        _run_web_server(app, config.overlay_port),
    )


if __name__ == "__main__":
    asyncio.run(main())
