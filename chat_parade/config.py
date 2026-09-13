from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

REQUIRED_KEYS = (
    "CLIENT_ID",
    "CLIENT_SECRET",
    "TOKEN",
    "REFRESH_TOKEN",
    "BROADCASTER_ID",
    "CHANNEL",
)


@dataclass(frozen=True)
class Config:
    client_id: str
    client_secret: str
    token: str
    refresh_token: str
    broadcaster_id: str
    channel: str
    data_dir: Path
    overlay_port: int
    env_path: Path


class MissingConfigError(RuntimeError):
    pass


def env_is_complete(env_path: Path) -> bool:
    """True when env_path exists and defines every var load_config requires.

    Used by run.bat to decide whether to launch oauth_setup: unlike
    ``if exist .env``, this also catches an .env left over from before a
    var like CLIENT_SECRET/REFRESH_TOKEN became required.
    """
    if not env_path.exists():
        return False
    values = dotenv_values(env_path)
    return all(values.get(key) for key in REQUIRED_KEYS)


def load_config(env_path: Path | None = None) -> Config:
    load_dotenv(dotenv_path=env_path)

    required = {key: os.getenv(key) for key in REQUIRED_KEYS}
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise MissingConfigError(
            "Faltam variáveis no .env: " + ", ".join(missing)
        )

    return Config(
        client_id=required["CLIENT_ID"],
        client_secret=required["CLIENT_SECRET"],
        token=required["TOKEN"],
        refresh_token=required["REFRESH_TOKEN"],
        broadcaster_id=required["BROADCASTER_ID"],
        channel=required["CHANNEL"],
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        overlay_port=int(os.getenv("OVERLAY_PORT", "8901")),
        env_path=env_path if env_path is not None else Path(".env"),
    )
