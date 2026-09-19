from pathlib import Path

import pytest

from texuguito.config import Config
from texuguito.token_manager import refresh_token, update_env_file


def make_config(tmp_path, **overrides) -> Config:
    defaults = dict(
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
    defaults.update(overrides)
    return Config(**defaults)


def test_refresh_token_returns_new_config_on_success(monkeypatch, tmp_path):
    config = make_config(tmp_path)

    def fake_post(url, data, timeout):
        assert url == "https://id.twitch.tv/oauth2/token"
        assert data == {
            "client_id": "id",
            "client_secret": "secret",
            "grant_type": "refresh_token",
            "refresh_token": "old-refresh",
        }

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"access_token": "new-token", "refresh_token": "new-refresh"}

        return FakeResponse()

    monkeypatch.setattr("texuguito.token_manager.requests.post", fake_post)

    refreshed = refresh_token(config)

    assert refreshed.token == "new-token"
    assert refreshed.refresh_token == "new-refresh"
    assert refreshed.client_id == "id"


def test_refresh_token_returns_none_on_non_200(monkeypatch, tmp_path):
    config = make_config(tmp_path)

    def fake_post(url, data, timeout):
        class FakeResponse:
            status_code = 400

            def json(self):
                return {"message": "Invalid refresh token"}

        return FakeResponse()

    monkeypatch.setattr("texuguito.token_manager.requests.post", fake_post)

    assert refresh_token(config) is None


def test_refresh_token_returns_none_on_request_exception(monkeypatch, tmp_path):
    config = make_config(tmp_path)

    def fake_post(url, data, timeout):
        raise ConnectionError("network down")

    monkeypatch.setattr("texuguito.token_manager.requests.post", fake_post)

    assert refresh_token(config) is None


def test_update_env_file_rewrites_only_token_lines(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "CLIENT_ID=id\n"
        "TOKEN=old-token\n"
        "REFRESH_TOKEN=old-refresh\n"
        "CHANNEL=canal\n",
        encoding="utf-8",
    )

    update_env_file(env_path, token="new-token", refresh_token="new-refresh")

    lines = env_path.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "CLIENT_ID=id",
        "TOKEN=new-token",
        "REFRESH_TOKEN=new-refresh",
        "CHANNEL=canal",
    ]


def test_update_env_file_noop_when_file_missing(tmp_path):
    env_path = tmp_path / "does-not-exist.env"

    update_env_file(env_path, token="new-token", refresh_token="new-refresh")

    assert not env_path.exists()
