import asyncio
import dataclasses

import pytest
import twitchio.errors

import chat_parade.main as main_module
from chat_parade.config import Config
from chat_parade.main import (
    _load_and_refresh_config,
    _run_until_error,
    _run_web_server,
    build_components,
)


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


async def test_web_server_shuts_down_gracefully_instead_of_raw_cancel(monkeypatch):
    class FakeServer:
        def __init__(self, config):
            self.should_exit = False
            self.was_cancelled = False

        async def serve(self):
            try:
                while not self.should_exit:
                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                self.was_cancelled = True
                raise

    fake_servers = []

    def fake_server_factory(config):
        server = FakeServer(config)
        fake_servers.append(server)
        return server

    monkeypatch.setattr(main_module.uvicorn, "Server", fake_server_factory)

    task = asyncio.ensure_future(_run_web_server(app=None, port=1234))
    await asyncio.sleep(0.03)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert len(fake_servers) == 1
    assert fake_servers[0].should_exit is True
    assert fake_servers[0].was_cancelled is False


async def test_run_until_error_propagates_other_exceptions():
    async def raise_value_error():
        raise ValueError("something else broke")

    with pytest.raises(ValueError):
        await _run_until_error(raise_value_error())


async def test_build_components_wires_everything_without_network(tmp_path):
    config = Config(
        client_id="id",
        client_secret="secret",
        token="tok",
        refresh_token="reftok",
        broadcaster_id="1",
        channel="canal",
        data_dir=tmp_path,
        overlay_port=8901,
        env_path=tmp_path / ".env",
        audio_dir=tmp_path / "audios",
    )

    store, points, events, app, broadcaster, bot = build_components(config)

    assert store is not None
    assert points is not None
    assert events.empty()
    assert app is not None
    assert broadcaster is not None
    assert bot is not None


def test_load_and_refresh_config_uses_refreshed_token_and_updates_env(monkeypatch, tmp_path):
    original = Config(
        client_id="id",
        client_secret="secret",
        token="old-token",
        refresh_token="old-refresh",
        broadcaster_id="1",
        channel="canal",
        data_dir=tmp_path,
        overlay_port=8901,
        env_path=tmp_path / ".env",
    )
    refreshed = dataclasses.replace(original, token="new-token", refresh_token="new-refresh")

    monkeypatch.setattr(main_module, "load_config", lambda env_path=None: original)
    monkeypatch.setattr(main_module, "refresh_token", lambda config: refreshed)

    update_calls = []
    monkeypatch.setattr(
        main_module,
        "update_env_file",
        lambda env_path, token, refresh_token: update_calls.append((env_path, token, refresh_token)),
    )

    result = _load_and_refresh_config()

    assert result == refreshed
    assert update_calls == [(refreshed.env_path, "new-token", "new-refresh")]


def test_load_and_refresh_config_falls_back_when_refresh_fails(monkeypatch, tmp_path, capsys):
    original = Config(
        client_id="id",
        client_secret="secret",
        token="old-token",
        refresh_token="old-refresh",
        broadcaster_id="1",
        channel="canal",
        data_dir=tmp_path,
        overlay_port=8901,
        env_path=tmp_path / ".env",
    )

    monkeypatch.setattr(main_module, "load_config", lambda env_path=None: original)
    monkeypatch.setattr(main_module, "refresh_token", lambda config: None)

    update_calls = []
    monkeypatch.setattr(
        main_module,
        "update_env_file",
        lambda env_path, token, refresh_token: update_calls.append((env_path, token, refresh_token)),
    )

    result = _load_and_refresh_config()

    assert result == original
    assert update_calls == []
    assert "não foi possível renovar" in capsys.readouterr().out.lower()
