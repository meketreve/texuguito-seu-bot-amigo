from urllib.parse import parse_qs, urlparse

import pytest

from texuguito.oauth_setup import (
    REDIRECT_URI,
    SCOPES,
    build_auth_url,
    exchange_code_for_token,
    fetch_account,
    open_callback_server,
    preserved_settings,
    write_env_file,
)


def test_build_auth_url_includes_client_id_redirect_scopes_and_state():
    url = build_auth_url(client_id="abc123", state="xyz")
    query = parse_qs(urlparse(url).query)

    assert url.startswith("https://id.twitch.tv/oauth2/authorize?")
    assert query["client_id"] == ["abc123"]
    assert query["redirect_uri"] == [REDIRECT_URI]
    assert query["response_type"] == ["code"]
    assert query["state"] == ["xyz"]
    assert query["scope"] == [SCOPES]


def test_exchange_code_for_token_returns_access_and_refresh_token(monkeypatch):
    def fake_post(url, data, timeout):
        assert url == "https://id.twitch.tv/oauth2/token"
        assert data == {
            "client_id": "abc123",
            "client_secret": "shh",
            "code": "the-code",
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }

        class FakeResponse:
            def json(self):
                return {"access_token": "tok", "refresh_token": "reftok"}

        return FakeResponse()

    monkeypatch.setattr("texuguito.oauth_setup.requests.post", fake_post)

    token, refresh_token = exchange_code_for_token("abc123", "shh", "the-code")

    assert token == "tok"
    assert refresh_token == "reftok"


def test_exchange_code_for_token_raises_when_no_access_token(monkeypatch):
    def fake_post(url, data, timeout):
        class FakeResponse:
            def json(self):
                return {"message": "invalid code"}

        return FakeResponse()

    monkeypatch.setattr("texuguito.oauth_setup.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="invalid code"):
        exchange_code_for_token("abc123", "shh", "bad-code")


def test_fetch_account_returns_id_and_login_from_helix_users(monkeypatch):
    def fake_get(url, headers, timeout):
        assert url == "https://api.twitch.tv/helix/users"
        assert headers == {"Client-ID": "abc123", "Authorization": "Bearer tok"}

        class FakeResponse:
            def json(self):
                return {"data": [{"id": "999", "login": "MeuCanal"}]}

        return FakeResponse()

    monkeypatch.setattr("texuguito.oauth_setup.requests.get", fake_get)

    assert fetch_account("abc123", "tok") == ("999", "meucanal")


def test_open_callback_server_returns_none_when_port_is_taken(monkeypatch):
    """Regression test: another program on the redirect port (e.g. a dev
    server on the old redirect port, 3000) used to crash setup with a raw OSError traceback, after
    the browser had already been sent to Twitch."""
    import socket

    blocker = socket.socket()
    blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    blocker.bind(("localhost", 0))
    blocker.listen()
    monkeypatch.setattr("texuguito.oauth_setup.REDIRECT_PORT", blocker.getsockname()[1])
    try:
        assert open_callback_server() is None
    finally:
        blocker.close()


def test_preserved_settings_defaults_when_env_missing(tmp_path):
    settings = preserved_settings(tmp_path / "does-not-exist.env")

    assert settings == {"DATA_DIR": "data", "OVERLAY_PORT": "8901"}


def test_preserved_settings_reads_existing_env_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("DATA_DIR=meus_dados\nOVERLAY_PORT=9999\n", encoding="utf-8")

    settings = preserved_settings(env_path)

    assert settings == {"DATA_DIR": "meus_dados", "OVERLAY_PORT": "9999"}


def test_rerunning_setup_keeps_audio_settings_and_drops_old_credentials(tmp_path):
    """Regression test: re-running setup (e.g. after swapping the Twitch app)
    used to rewrite .env with only DATA_DIR/OVERLAY_PORT, dropping AUDIO_DIR
    and AUDIO_VOLUME."""
    env_path = tmp_path / ".env"
    env_path.write_text(
        "CLIENT_ID=app-velho\nTOKEN=token-velho\nAUDIO_DIR=meus-sons\nAUDIO_VOLUME=0.4\n",
        encoding="utf-8",
    )

    write_env_file(
        env_path,
        client_id="app-novo",
        client_secret="shh",
        token="token-novo",
        refresh_token="reftok",
        broadcaster_id="999",
        channel="meucanal",
        settings=preserved_settings(env_path),
    )

    content = env_path.read_text(encoding="utf-8")
    assert "AUDIO_DIR=meus-sons" in content
    assert "AUDIO_VOLUME=0.4" in content
    assert "DATA_DIR=data" in content
    assert "app-velho" not in content
    assert "token-velho" not in content


def test_write_env_file_writes_all_fields(tmp_path):
    env_path = tmp_path / ".env"

    write_env_file(
        env_path,
        client_id="abc123",
        client_secret="shh",
        token="tok",
        refresh_token="reftok",
        broadcaster_id="999",
        channel="meucanal",
    )

    content = env_path.read_text(encoding="utf-8")
    assert "CLIENT_ID=abc123" in content
    assert "CLIENT_SECRET=shh" in content
    assert "TOKEN=tok" in content
    assert "REFRESH_TOKEN=reftok" in content
    assert "BROADCASTER_ID=999" in content
    assert "CHANNEL=meucanal" in content
    assert "DATA_DIR=data" in content
    assert "OVERLAY_PORT=8901" in content
