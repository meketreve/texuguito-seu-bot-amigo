"""Pre-flight check run.bat does before starting the app.

Exit code tells run.bat what to do next:
  0 - all good, start the app
  1 - credentials missing or refused by Twitch: run the setup
  2 - couldn't reach Twitch: start anyway (the app retries on its own)
  3 - the overlay port is taken: the app is probably already open
"""
from __future__ import annotations

import socket
import sys
from pathlib import Path

import requests

from chat_parade.config import env_is_complete, load_config
from chat_parade.oauth_setup import SCOPES
from chat_parade.token_manager import refreshed_config, request_refresh, update_env_file

EXIT_OK = 0
EXIT_NEEDS_SETUP = 1
EXIT_OFFLINE = 2
EXIT_PORT_BUSY = 3

VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # See oauth_setup._CallbackServer: on Windows SO_REUSEADDR would let
        # this bind succeed even with another program listening.
        if sys.platform != "win32":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", port))
        except OSError:
            return False
    return True


def token_scopes(token: str) -> set[str] | None:
    """Scopes granted to `token`, or None if Twitch says it's invalid."""
    response = requests.get(VALIDATE_URL, headers={"Authorization": f"OAuth {token}"}, timeout=10)
    if response.status_code != 200:
        return None
    return set(response.json().get("scopes", []))


def check(env_path: Path) -> tuple[int, str]:
    if not env_is_complete(env_path):
        return EXIT_NEEDS_SETUP, "O chat-parade ainda não está conectado à Twitch."

    config = load_config(env_path)

    if not port_is_free(config.overlay_port):
        return (
            EXIT_PORT_BUSY,
            f"A porta {config.overlay_port} já está em uso: o chat-parade provavelmente já está "
            "aberto em outra janela. Feche a outra janela e tente de novo.",
        )

    try:
        response = request_refresh(config)
        if response.status_code in (400, 401, 403):
            return (
                EXIT_NEEDS_SETUP,
                "A Twitch recusou as credenciais salvas (app apagado, segredo trocado ou "
                "acesso revogado). Vamos conectar de novo.",
            )
        if response.status_code != 200:
            return EXIT_OFFLINE, f"A Twitch respondeu com erro {response.status_code}; tentando iniciar mesmo assim."

        config = refreshed_config(config, response)
        update_env_file(env_path, config.token, config.refresh_token)

        scopes = token_scopes(config.token)
    except requests.exceptions.RequestException:
        return EXIT_OFFLINE, "Não deu pra falar com a Twitch (sem internet?); tentando iniciar mesmo assim."

    if scopes is None:
        return EXIT_NEEDS_SETUP, "O token da Twitch não é mais válido. Vamos conectar de novo."
    missing = set(SCOPES.split()) - scopes
    if missing:
        return (
            EXIT_NEEDS_SETUP,
            "O chat-parade precisa de permissões novas na Twitch "
            f"({', '.join(sorted(missing))}). Vamos autorizar de novo.",
        )

    return EXIT_OK, f"Conectado à Twitch como {config.channel}."


def main() -> int:
    code, message = check(Path(".env"))
    print(("✅ " if code == EXIT_OK else "⚠️  ") + message)
    return code


if __name__ == "__main__":
    sys.exit(main())
