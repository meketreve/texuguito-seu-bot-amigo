from __future__ import annotations

import dataclasses
from pathlib import Path

import requests

from chat_parade.config import Config

TOKEN_URL = "https://id.twitch.tv/oauth2/token"


def refresh_token(config: Config) -> Config | None:
    """Trades the stored refresh token for a fresh access token.

    Mirrors texuguito-seu-bot-amigo's TokenManager.refresh_token: same app,
    same grant. Returns None on any failure so the caller can fall back to
    the token it already has instead of crashing the whole bot over a
    renewal that didn't work.
    """
    payload = {
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "grant_type": "refresh_token",
        "refresh_token": config.refresh_token,
    }

    try:
        response = requests.post(TOKEN_URL, data=payload, timeout=10)
    except Exception:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    return dataclasses.replace(
        config,
        token=data["access_token"],
        refresh_token=data.get("refresh_token", config.refresh_token),
    )


def update_env_file(env_path: Path, token: str, refresh_token: str) -> None:
    """Rewrites TOKEN=/REFRESH_TOKEN= in-place, leaving every other line untouched."""
    if not env_path.exists():
        return

    lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)

    updated = []
    for line in lines:
        if line.startswith("TOKEN="):
            updated.append(f"TOKEN={token}\n")
        elif line.startswith("REFRESH_TOKEN="):
            updated.append(f"REFRESH_TOKEN={refresh_token}\n")
        else:
            updated.append(line)

    env_path.write_text("".join(updated), encoding="utf-8")
