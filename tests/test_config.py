import pytest

from chat_parade.config import MissingConfigError, load_config


def test_load_config_reads_required_fields(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIENT_ID", "abc123")
    monkeypatch.setenv("CLIENT_SECRET", "sekret789")
    monkeypatch.setenv("TOKEN", "tok456")
    monkeypatch.setenv("REFRESH_TOKEN", "refresh456")
    monkeypatch.setenv("BROADCASTER_ID", "789")
    monkeypatch.setenv("CHANNEL", "meucanal")

    env_path = tmp_path / "does-not-exist.env"
    config = load_config(env_path=env_path)

    assert config.client_id == "abc123"
    assert config.client_secret == "sekret789"
    assert config.token == "tok456"
    assert config.refresh_token == "refresh456"
    assert config.broadcaster_id == "789"
    assert config.channel == "meucanal"
    assert config.overlay_port == 8901
    assert config.env_path == env_path


def test_load_config_raises_when_missing_fields(monkeypatch, tmp_path):
    monkeypatch.delenv("CLIENT_ID", raising=False)
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    monkeypatch.delenv("TOKEN", raising=False)
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("BROADCASTER_ID", raising=False)
    monkeypatch.delenv("CHANNEL", raising=False)

    with pytest.raises(MissingConfigError):
        load_config(env_path=tmp_path / "does-not-exist.env")


def test_load_config_raises_when_only_client_secret_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIENT_ID", "abc123")
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    monkeypatch.setenv("TOKEN", "tok456")
    monkeypatch.setenv("REFRESH_TOKEN", "refresh456")
    monkeypatch.setenv("BROADCASTER_ID", "789")
    monkeypatch.setenv("CHANNEL", "meucanal")

    with pytest.raises(MissingConfigError):
        load_config(env_path=tmp_path / "does-not-exist.env")
