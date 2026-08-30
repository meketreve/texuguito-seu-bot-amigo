import asyncio

from chat_parade.config import Config
from chat_parade.twitch_chat import ChatParadeBot
from chat_parade.viewer_store import ViewerStore


def _config(tmp_path) -> Config:
    return Config(
        client_id="id",
        token="tok",
        broadcaster_id="1",
        channel="meucanal",
        data_dir=tmp_path,
        overlay_port=8901,
    )


async def test_bot_constructs_without_touching_the_network(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    bot = ChatParadeBot(_config(tmp_path), store, events)

    assert bot is not None
    assert bot._store is store
    assert bot._events is events
