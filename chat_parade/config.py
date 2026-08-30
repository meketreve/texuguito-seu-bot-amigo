from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    client_id: str
    token: str
    broadcaster_id: str
    channel: str
    data_dir: Path
    overlay_port: int


class MissingConfigError(RuntimeError):
    pass


def load_config(env_path: Path | None = None) -> Config:
    load_dotenv(dotenv_path=env_path)

    required = {
        "CLIENT_ID": os.getenv("CLIENT_ID"),
        "TOKEN": os.getenv("TOKEN"),
        "BROADCASTER_ID": os.getenv("BROADCASTER_ID"),
        "CHANNEL": os.getenv("CHANNEL"),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise MissingConfigError(
            "Faltam variáveis no .env: " + ", ".join(missing)
        )

    return Config(
        client_id=required["CLIENT_ID"],
        token=required["TOKEN"],
        broadcaster_id=required["BROADCASTER_ID"],
        channel=required["CHANNEL"],
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        overlay_port=int(os.getenv("OVERLAY_PORT", "8901")),
    )
