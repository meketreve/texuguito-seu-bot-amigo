from __future__ import annotations

import secrets
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import dotenv_values

# Must match an "OAuth Redirect URL" registered on the Twitch app, so it can't
# move without every existing app needing a new URL registered. Deliberately
# not 3000: that's the default of countless dev servers (SpacetimeDB, React,
# Rails...), and setup can't receive Twitch's redirect while one of them runs.
REDIRECT_PORT = 17563
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"
AUTHORIZE_URL = "https://id.twitch.tv/oauth2/authorize"
DEV_CONSOLE_URL = "https://dev.twitch.tv/console/apps"

# Only what the bot uses: read+reply chat, read the chatters list, see cheers.
SCOPES = "chat:read chat:edit moderator:read:chatters bits:read"

DEFAULT_SETTINGS = {"DATA_DIR": "data", "OVERLAY_PORT": "8901"}
# Non-credential settings a streamer may have customized in .env.
OPTIONAL_SETTINGS = ("DATA_DIR", "OVERLAY_PORT", "AUDIO_DIR", "AUDIO_VOLUME")


def build_auth_url(client_id: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(client_id: str, client_secret: str, code: str) -> tuple[str, str]:
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    response = requests.post(TOKEN_URL, data=payload, timeout=10)
    data = response.json()

    if "access_token" not in data:
        raise RuntimeError(f"Erro ao obter token: {data.get('message', data)}")

    return data["access_token"], data.get("refresh_token", "")


def fetch_account(client_id: str, token: str) -> tuple[str, str]:
    """(user id, login) of whoever authorized. The bot reads the chatters list
    as that user, so it has to be the channel owner: their login is the
    channel and their id is BROADCASTER_ID."""
    headers = {"Client-ID": client_id, "Authorization": f"Bearer {token}"}
    response = requests.get("https://api.twitch.tv/helix/users", headers=headers, timeout=10)
    user = response.json()["data"][0]
    return user["id"], user["login"].lower()


def preserved_settings(env_path: Path) -> dict[str, str]:
    """The optional settings from an existing .env, over the defaults.

    Lets re-running setup (e.g. after swapping the Twitch app, or because
    CLIENT_SECRET/REFRESH_TOKEN were missing from an older .env) keep a
    custom data dir, port or audio setup instead of silently dropping them.
    """
    settings = dict(DEFAULT_SETTINGS)
    if env_path.exists():
        values = dotenv_values(env_path)
        settings.update({key: values[key] for key in OPTIONAL_SETTINGS if values.get(key)})
    return settings


def write_env_file(
    env_path: Path,
    *,
    client_id: str,
    client_secret: str,
    token: str,
    refresh_token: str,
    broadcaster_id: str,
    channel: str,
    settings: dict[str, str] | None = None,
) -> None:
    settings = DEFAULT_SETTINGS if settings is None else settings
    env_path.write_text(
        "\n".join(
            [
                f"CLIENT_ID={client_id}",
                f"CLIENT_SECRET={client_secret}",
                f"TOKEN={token}",
                f"REFRESH_TOKEN={refresh_token}",
                f"BROADCASTER_ID={broadcaster_id}",
                f"CHANNEL={channel}",
                *(f"{key}={value}" for key, value in settings.items()),
                "",
            ]
        ),
        encoding="utf-8",
    )


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Captures the ?code=/&state= Twitch redirects the browser to after login."""

    auth_code: str | None = None
    auth_state: str | None = None
    done = False

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler's own naming)
        params = parse_qs(urlparse(self.path).query)

        if "code" in params:
            _OAuthCallbackHandler.auth_code = params["code"][0]
            _OAuthCallbackHandler.auth_state = params.get("state", [None])[0]
            self._respond(200, "✅ Autorização concluída! Pode fechar esta janela e voltar pro chat-parade.")
        elif "error" in params:
            error = params["error"][0]
            self._respond(400, f"❌ Erro na autorização: {error}")
        else:
            # Browsers also ask for /favicon.ico and the like; those aren't
            # the Twitch redirect, so keep waiting for the real one.
            self._respond(404, "")
            return

        _OAuthCallbackHandler.done = True

    def _respond(self, status: int, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"<html><body>{message}</body></html>".encode("utf-8"))

    def log_message(self, format: str, *args) -> None:  # noqa: A002 (matches base signature)
        pass


class _CallbackServer(HTTPServer):
    # On Windows, SO_REUSEADDR (which HTTPServer turns on) lets a socket bind
    # a port another program is already listening on, so a busy port would go
    # unnoticed and Twitch's redirect could land in the other program. On
    # Linux/macOS it only skips the TIME_WAIT delay, which is what we want.
    allow_reuse_address = sys.platform != "win32"


def open_callback_server() -> HTTPServer | None:
    """Binds the redirect port, or returns None if another program holds it.

    Done before opening the browser: otherwise the user authorizes on Twitch
    and gets redirected to whatever else is listening on that port.
    """
    try:
        server = _CallbackServer(("localhost", REDIRECT_PORT), _OAuthCallbackHandler)
    except OSError:
        return None
    server.timeout = 1
    return server


def wait_for_callback(server: HTTPServer) -> tuple[str | None, str | None]:
    """Blocks until Twitch's OAuth redirect arrives, then returns (code, state)."""
    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.auth_state = None
    _OAuthCallbackHandler.done = False
    try:
        while not _OAuthCallbackHandler.done:
            server.handle_request()
    finally:
        server.server_close()
    return _OAuthCallbackHandler.auth_code, _OAuthCallbackHandler.auth_state


def _ask(prompt: str, current: str | None) -> str:
    """Asks for a value; Enter keeps `current` when there is one."""
    if current:
        answer = input(f"{prompt} (Enter mantém o atual): ").strip()
        return answer or current
    return input(f"{prompt}: ").strip()


def _print_instructions(has_current: bool) -> None:
    print("=" * 60)
    print("🎉 CHAT PARADE - CONFIGURAÇÃO DA TWITCH")
    print("=" * 60)
    print()
    if has_current:
        print("Já existe um app configurado. Se ele continua valendo, só aperte")
        print("Enter nas duas perguntas e autorize de novo no navegador.")
        print(f"Se a Twitch mostrar o erro \"redirect_mismatch\", adicione {REDIRECT_URI}")
        print("nas URLs de redirecionamento OAuth do app (em Gerenciar) e tente de novo.")
        print()
    if has_current:
        print(f"Se precisar de um app novo, o painel fica em {DEV_CONSOLE_URL}:")
    else:
        print("Primeiro crie um app da Twitch (vou abrir o painel no navegador):")
    print(f"  1. Em {DEV_CONSOLE_URL}, registre um aplicativo novo (Register Your Application).")
    print("  2. Nome: qualquer um (ex: chat-parade-SEUCANAL).")
    print(f"  3. URL de redirecionamento OAuth (OAuth Redirect URLs): {REDIRECT_URI}")
    print("  4. Categoria: Chat Bot. Tipo de cliente (Client Type): Confidencial. Crie o app.")
    print("  5. Em Gerenciar (Manage): copie o ID do cliente e gere um Novo segredo (New Secret).")
    print()
    print("⚠️  No navegador, faça login com a conta DONA DO CANAL.")
    print()


def main() -> int:
    env_path = Path(".env")
    current = dotenv_values(env_path) if env_path.exists() else {}
    has_current = bool(current.get("CLIENT_ID") and current.get("CLIENT_SECRET"))

    _print_instructions(has_current)
    if not has_current:
        webbrowser.open(DEV_CONSOLE_URL)

    client_id = _ask("📝 ID do cliente (Client ID)", current.get("CLIENT_ID"))
    client_secret = _ask("📝 Segredo do cliente (Client Secret)", current.get("CLIENT_SECRET"))
    if not client_id or not client_secret:
        print("❌ O ID e o segredo do cliente são obrigatórios.")
        return 1

    server = open_callback_server()
    if server is None:
        print()
        print(f"❌ A porta {REDIRECT_PORT} está ocupada por outro programa.")
        print(f"   A Twitch devolve a autorização em {REDIRECT_URI}, então ela precisa")
        print("   estar livre. Feche o programa que está usando essa porta e rode a")
        print("   configuração de novo.")
        return 1

    state = secrets.token_urlsafe(16)
    auth_url = build_auth_url(client_id, state)
    print()
    print("🔗 Abrindo o navegador pra você autorizar o chat-parade na Twitch...")
    webbrowser.open(auth_url)
    print("⏳ Aguardando a autorização... (feche esta janela pra cancelar)")
    print(f"   Se o navegador não abrir, copie este link: {auth_url}")

    code, returned_state = wait_for_callback(server)
    if not code:
        print("❌ A autorização não foi concluída no navegador.")
        return 1
    if returned_state != state:
        print("⚠️ Resposta de autorização inesperada (state não confere), abortando por segurança.")
        return 1

    print()
    print("✅ Autorizado! Obtendo tokens...")
    try:
        token, refresh_token = exchange_code_for_token(client_id, client_secret, code)
        broadcaster_id, channel = fetch_account(client_id, token)
    except (requests.exceptions.RequestException, RuntimeError, KeyError, IndexError) as exc:
        print(f"❌ {exc}")
        print("   Confira se o ID e o segredo do cliente estão certos.")
        return 1

    write_env_file(
        env_path,
        client_id=client_id,
        client_secret=client_secret,
        token=token,
        refresh_token=refresh_token,
        broadcaster_id=broadcaster_id,
        channel=channel,
        settings=preserved_settings(env_path),
    )

    print(f"✅ Tudo certo! Canal configurado: {channel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
