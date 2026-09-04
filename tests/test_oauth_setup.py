from urllib.parse import parse_qs, urlparse

import pytest

from chat_parade.oauth_setup import (
    REDIRECT_URI,
    SCOPES,
    build_auth_url,
    exchange_code_for_token,
    fetch_broadcaster_id,
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

    monkeypatch.setattr("chat_parade.oauth_setup.requests.post", fake_post)

    token, refresh_token = exchange_code_for_token("abc123", "shh", "the-code")

    assert token == "tok"
    assert refresh_token == "reftok"


def test_exchange_code_for_token_raises_when_no_access_token(monkeypatch):
    def fake_post(url, data, timeout):
        class FakeResponse:
            def json(self):
                return {"message": "invalid code"}

        return FakeResponse()

    monkeypatch.setattr("chat_parade.oauth_setup.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="invalid code"):
        exchange_code_for_token("abc123", "shh", "bad-code")


def test_fetch_broadcaster_id_returns_id_from_helix_users(monkeypatch):
    def fake_get(url, headers, timeout):
        assert url == "https://api.twitch.tv/helix/users"
        assert headers == {"Client-ID": "abc123", "Authorization": "Bearer tok"}

        class FakeResponse:
            def json(self):
                return {"data": [{"id": "999"}]}

        return FakeResponse()

    monkeypatch.setattr("chat_parade.oauth_setup.requests.get", fake_get)

    broadcaster_id = fetch_broadcaster_id("abc123", "tok")

    assert broadcaster_id == "999"


def test_preserved_settings_defaults_when_env_missing(tmp_path):
    data_dir, overlay_port = preserved_settings(tmp_path / "does-not-exist.env")

    assert data_dir == "data"
    assert overlay_port == 8901


def test_preserved_settings_reads_existing_env_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("DATA_DIR=meus_dados\nOVERLAY_PORT=9999\n", encoding="utf-8")

    data_dir, overlay_port = preserved_settings(env_path)

    assert data_dir == "meus_dados"
    assert overlay_port == 9999


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
