import asyncio

import pytest
import twitchio.errors

from chat_parade.config import Config
from chat_parade.main import _run_until_error, build_components


async def test_run_until_error_prints_friendly_message_on_auth_failure(capsys):
    async def raise_auth_error():
        raise twitchio.errors.AuthenticationError("bad token")

    async def never_finishes():
        await asyncio.sleep(10)

    await _run_until_error(raise_auth_error(), never_finishes())

    captured = capsys.readouterr()
    assert "token da Twitch invalido ou expirado" in captured.out


async def test_run_until_error_cancels_other_tasks_on_auth_failure():
    was_cancelled = asyncio.Event()

    async def raise_auth_error():
        raise twitchio.errors.AuthenticationError("bad token")

    async def never_finishes():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            was_cancelled.set()
            raise

    await _run_until_error(raise_auth_error(), never_finishes())

    assert was_cancelled.is_set()


async def test_run_until_error_propagates_other_exceptions():
    async def raise_value_error():
        raise ValueError("something else broke")

    with pytest.raises(ValueError):
        await _run_until_error(raise_value_error())


async def test_build_components_wires_everything_without_network(tmp_path):
    config = Config(
        client_id="id",
        token="tok",
        broadcaster_id="1",
        channel="canal",
        data_dir=tmp_path,
        overlay_port=8901,
    )

    store, events, app, broadcaster, bot = build_components(config)

    assert store is not None
    assert events.empty()
    assert app is not None
    assert broadcaster is not None
    assert bot is not None
