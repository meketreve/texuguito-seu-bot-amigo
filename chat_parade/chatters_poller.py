from __future__ import annotations

import asyncio

import requests

from chat_parade.config import Config
from chat_parade.viewer_store import ViewerEvent, ViewerStore

CHATTERS_URL = "https://api.twitch.tv/helix/chat/chatters"
POLL_INTERVAL_SECONDS = 45


def fetch_chatters(config: Config) -> set[str]:
    response = requests.get(
        CHATTERS_URL,
        params={
            "broadcaster_id": config.broadcaster_id,
            "moderator_id": config.broadcaster_id,
        },
        headers={
            "Client-Id": config.client_id,
            "Authorization": f"Bearer {config.token}",
        },
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Helix chatters falhou: {response.status_code} {response.text}")
    return {entry["user_name"].lower() for entry in response.json().get("data", [])}


async def poll_once(
    config: Config, store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"
) -> None:
    loop = asyncio.get_event_loop()
    try:
        chatters = await loop.run_in_executor(None, fetch_chatters, config)
    except Exception as exc:
        print(f"[chat-parade] erro ao buscar chatters: {exc}")
        return

    joined, left = store.sync_present_chatters(chatters)
    for username in joined:
        await events.put(ViewerEvent(type="joined", username=username))
    for username in left:
        await events.put(ViewerEvent(type="left", username=username))


async def run_chatters_poller(
    config: Config, store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"
) -> None:
    while True:
        await poll_once(config, store, events)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
