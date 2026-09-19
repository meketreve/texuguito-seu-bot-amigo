import socket
from unittest.mock import Mock

import pytest
import requests

from texuguito import check_setup
from texuguito.check_setup import (
    EXIT_NEEDS_SETUP,
    EXIT_OFFLINE,
    EXIT_OK,
    EXIT_PORT_BUSY,
    check,
    port_is_free,
)
from texuguito.oauth_setup import SCOPES

ENV = """CLIENT_ID=id
CLIENT_SECRET=secret
TOKEN=old-token
REFRESH_TOKEN=old-refresh
BROADCASTER_ID=1
CHANNEL=meucanal
DATA_DIR=data
OVERLAY_PORT={port}
"""


@pytest.fixture
def env_path(tmp_path, monkeypatch):
    # load_config() goes through load_dotenv, which copies the file into
    # os.environ and never overwrites what's already there. setenv-then-delenv
    # makes monkeypatch restore the original (absent) state afterwards, so one
    # test's .env can't leak into the next.
    for key in ("CLIENT_ID", "CLIENT_SECRET", "TOKEN", "REFRESH_TOKEN", "BROADCASTER_ID", "CHANNEL", "OVERLAY_PORT"):
        monkeypatch.setenv(key, "placeholder")
        monkeypatch.delenv(key)
    path = tmp_path / ".env"
    path.write_text(ENV.format(port=_free_port()), encoding="utf-8")
    return path


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _refresh_response(status: int) -> Mock:
    response = Mock(status_code=status)
    response.json.return_value = {"access_token": "new-token", "refresh_token": "new-refresh"}
    return response


def _stub_twitch(monkeypatch, *, refresh_status=200, scopes=SCOPES.split(), offline=False):
    def fake_refresh(config):
        if offline:
            raise requests.exceptions.ConnectionError("sem internet")
        return _refresh_response(refresh_status)

    monkeypatch.setattr(check_setup, "request_refresh", fake_refresh)
    monkeypatch.setattr(check_setup, "token_scopes", lambda token: None if scopes is None else set(scopes))


def test_missing_env_needs_setup(tmp_path):
    code, _ = check(tmp_path / "nao-existe.env")
    assert code == EXIT_NEEDS_SETUP


def test_valid_credentials_are_refreshed_and_saved(env_path, monkeypatch):
    _stub_twitch(monkeypatch)

    code, message = check(env_path)

    assert code == EXIT_OK
    assert "meucanal" in message
    content = env_path.read_text(encoding="utf-8")
    assert "TOKEN=new-token" in content
    assert "REFRESH_TOKEN=new-refresh" in content


def test_refused_credentials_need_setup(env_path, monkeypatch):
    """E.g. the Twitch app was deleted in the dev console: the .env is complete
    but useless, and used to make run.bat start a bot that can't connect."""
    _stub_twitch(monkeypatch, refresh_status=400)

    code, message = check(env_path)

    assert code == EXIT_NEEDS_SETUP
    assert "recusou" in message
    assert "TOKEN=old-token" in env_path.read_text(encoding="utf-8")


def test_invalid_token_after_refresh_needs_setup(env_path, monkeypatch):
    _stub_twitch(monkeypatch, scopes=None)
    assert check(env_path)[0] == EXIT_NEEDS_SETUP


def test_missing_scopes_need_setup(env_path, monkeypatch):
    _stub_twitch(monkeypatch, scopes=["chat:read", "chat:edit"])

    code, message = check(env_path)

    assert code == EXIT_NEEDS_SETUP
    assert "moderator:read:chatters" in message


def test_extra_scopes_are_fine(env_path, monkeypatch):
    """A .env carried over from texuguito has a broader set of scopes."""
    _stub_twitch(monkeypatch, scopes=SCOPES.split() + ["channel:read:redemptions"])
    assert check(env_path)[0] == EXIT_OK


def test_offline_starts_anyway(env_path, monkeypatch):
    _stub_twitch(monkeypatch, offline=True)
    assert check(env_path)[0] == EXIT_OFFLINE


def test_twitch_server_error_starts_anyway(env_path, monkeypatch):
    _stub_twitch(monkeypatch, refresh_status=503)
    assert check(env_path)[0] == EXIT_OFFLINE


def test_busy_overlay_port_means_already_running(env_path, monkeypatch):
    _stub_twitch(monkeypatch)
    with socket.socket() as blocker:
        blocker.bind(("0.0.0.0", 0))
        blocker.listen()
        port = blocker.getsockname()[1]
        env_path.write_text(ENV.format(port=port), encoding="utf-8")

        code, message = check(env_path)

    assert code == EXIT_PORT_BUSY
    assert str(port) in message


def test_port_is_free():
    port = _free_port()
    assert port_is_free(port) is True
    with socket.socket() as blocker:
        blocker.bind(("0.0.0.0", port))
        blocker.listen()
        assert port_is_free(port) is False
