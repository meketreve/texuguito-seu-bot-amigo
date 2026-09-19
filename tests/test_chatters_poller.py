import asyncio
from unittest.mock import Mock, patch

import pytest

from texuguito.chatters_poller import fetch_chatters, poll_once
from texuguito.config import Config
from texuguito.viewer_store import ViewerStore


def _config(tmp_path) -> Config:
    return Config(
        client_id="id",
        client_secret="secret",
        token="tok",
        refresh_token="reftok",
        broadcaster_id="1",
        channel="canal",
        data_dir=tmp_path,
        overlay_port=8901,
        env_path=tmp_path / ".env",
    )


def test_fetch_chatters_parses_usernames(tmp_path):
    fake_response = Mock(status_code=200)
    fake_response.json.return_value = {
        "data": [{"user_name": "Ana"}, {"user_name": "BRUNO"}]
    }
    with patch("texuguito.chatters_poller.requests.get", return_value=fake_response):
        result = fetch_chatters(_config(tmp_path))

    assert result == {"ana", "bruno"}


def test_fetch_chatters_raises_on_error_status(tmp_path):
    fake_response = Mock(status_code=401, text="unauthorized")
    with patch("texuguito.chatters_poller.requests.get", return_value=fake_response):
        with pytest.raises(RuntimeError):
            fetch_chatters(_config(tmp_path))


async def test_poll_once_enqueues_joined_events(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    with patch("texuguito.chatters_poller.fetch_chatters", return_value={"ana"}):
        await poll_once(_config(tmp_path), store, events)

    event = events.get_nowait()
    assert event.type == "joined"
    assert event.username == "ana"


async def test_poll_once_swallows_fetch_errors(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    with patch(
        "texuguito.chatters_poller.fetch_chatters",
        side_effect=RuntimeError("boom"),
    ):
        await poll_once(_config(tmp_path), store, events)

    assert events.empty()
