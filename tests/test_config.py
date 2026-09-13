import pytest

from chat_parade.config import MissingConfigError, env_is_complete, load_config


def test_load_config_reads_required_fields(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIENT_ID", "abc123")
    monkeypatch.setenv("CLIENT_SECRET", "sekret789")
    monkeypatch.setenv("TOKEN", "tok456")
    monkeypatch.setenv("REFRESH_TOKEN", "refresh456")
    monkeypatch.setenv("BROADCASTER_ID", "789")
    monkeypatch.setenv("CHANNEL", "meucanal")
    monkeypatch.delenv("AUDIO_DIR", raising=False)
    monkeypatch.delenv("AUDIO_VOLUME", raising=False)

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
    assert str(config.audio_dir) == "audios"
    assert config.audio_volume == 1.0


def test_load_config_reads_optional_audio_settings(monkeypatch, tmp_path):
    for key in ("CLIENT_ID", "CLIENT_SECRET", "TOKEN", "REFRESH_TOKEN", "BROADCASTER_ID", "CHANNEL"):
        monkeypatch.setenv(key, "x")
    monkeypatch.setenv("AUDIO_DIR", "meus-sons")
    monkeypatch.setenv("AUDIO_VOLUME", "0.5")

    config = load_config(env_path=tmp_path / "does-not-exist.env")

    assert str(config.audio_dir) == "meus-sons"
    assert config.audio_volume == 0.5


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


def test_env_is_complete_false_when_file_missing(tmp_path):
    assert env_is_complete(tmp_path / "does-not-exist.env") is False


def test_env_is_complete_false_when_file_predates_new_required_vars(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "CLIENT_ID=abc123\nTOKEN=tok456\nBROADCASTER_ID=789\nCHANNEL=meucanal\n",
        encoding="utf-8",
    )

    assert env_is_complete(env_path) is False


def test_env_is_complete_true_when_all_required_vars_present(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "CLIENT_ID=abc123\n"
        "CLIENT_SECRET=sekret\n"
        "TOKEN=tok456\n"
        "REFRESH_TOKEN=refresh456\n"
        "BROADCASTER_ID=789\n"
        "CHANNEL=meucanal\n",
        encoding="utf-8",
    )

    assert env_is_complete(env_path) is True
