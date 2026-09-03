from __future__ import annotations

import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

# Same Twitch app/redirect URL as texuguito-seu-bot-amigo's setup.py — the two
# bots share credentials, and only one setup flow ever runs at a time, so
# reusing the port avoids registering a second Redirect URL on the app.
REDIRECT_PORT = 3000
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"
AUTHORIZE_URL = "https://id.twitch.tv/oauth2/authorize"

# Trimmed to what chat_parade/twitch_chat.py and chatters_poller.py actually
# use (read+reply chat, read the chatters list, see cheers) — texuguito's own
# setup asks for a broader set (redemptions, subscriptions) chat-parade has
# no use for.
SCOPES = "chat:read chat:edit moderator:read:chatters bits:read"


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


def fetch_broadcaster_id(client_id: str, token: str) -> str:
    headers = {"Client-ID": client_id, "Authorization": f"Bearer {token}"}
    response = requests.get("https://api.twitch.tv/helix/users", headers=headers, timeout=10)
    return response.json()["data"][0]["id"]


def write_env_file(
    env_path: Path,
    *,
    client_id: str,
    client_secret: str,
    token: str,
    refresh_token: str,
    broadcaster_id: str,
    channel: str,
    data_dir: str = "data",
    overlay_port: int = 8901,
) -> None:
    env_path.write_text(
        "\n".join(
            [
                f"CLIENT_ID={client_id}",
                f"CLIENT_SECRET={client_secret}",
                f"TOKEN={token}",
                f"REFRESH_TOKEN={refresh_token}",
                f"BROADCASTER_ID={broadcaster_id}",
                f"CHANNEL={channel}",
                f"DATA_DIR={data_dir}",
                f"OVERLAY_PORT={overlay_port}",
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
            self._respond(200, "✅ Autorização concluída! Pode fechar esta janela.")
        else:
            error = params.get("error", ["Erro desconhecido"])[0]
            self._respond(400, f"❌ Erro na autorização: {error}")

        _OAuthCallbackHandler.done = True

    def _respond(self, status: int, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"<html><body>{message}</body></html>".encode("utf-8"))

    def log_message(self, format: str, *args) -> None:  # noqa: A002 (matches base signature)
        pass


def run_local_server() -> tuple[str | None, str | None]:
    """Blocks until Twitch's OAuth redirect hits localhost, then returns (code, state)."""
    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.auth_state = None
    _OAuthCallbackHandler.done = False

    server = HTTPServer(("localhost", REDIRECT_PORT), _OAuthCallbackHandler)
    server.timeout = 1
    try:
        while not _OAuthCallbackHandler.done:
            server.handle_request()
    finally:
        server.server_close()

    return _OAuthCallbackHandler.auth_code, _OAuthCallbackHandler.auth_state


def main() -> None:
    print("=" * 60)
    print("🎉 CHAT PARADE - CONFIGURAÇÃO INICIAL")
    print("=" * 60)
    print()
    print("📋 Instruções:")
    print("1. Acesse: https://dev.twitch.tv/console/apps")
    print("2. Crie um novo app ou use um existente (pode ser o mesmo do texuguito)")
    print(f"3. Adicione '{REDIRECT_URI}' nas URLs de redirecionamento OAuth")
    print()

    client_id = input("📝 Digite seu CLIENT_ID: ").strip()
    client_secret = input("📝 Digite seu CLIENT_SECRET: ").strip()
    channel = input("📺 Digite o nome do seu canal: ").strip().lower()

    if not client_id or not client_secret or not channel:
        print("❌ Todos os campos são obrigatórios!")
        return

    state = secrets.token_urlsafe(16)
    auth_url = build_auth_url(client_id, state)

    print()
    print(f"🌐 Iniciando servidor local na porta {REDIRECT_PORT}...")
    print("🔗 Abrindo navegador para autorização...")
    webbrowser.open(auth_url)
    print("⏳ Aguardando autorização... (feche o terminal para cancelar)")

    code, returned_state = run_local_server()

    if not code:
        print("❌ Não foi possível obter o código de autorização.")
        return
    if returned_state != state:
        print("⚠️ Aviso: state não corresponde (possível CSRF), abortando.")
        return

    print()
    print("✅ Código recebido! Obtendo tokens...")
    try:
        token, refresh_token = exchange_code_for_token(client_id, client_secret, code)
    except (requests.exceptions.RequestException, RuntimeError) as exc:
        print(f"❌ {exc}")
        return
    print("✅ Token obtido com sucesso!")

    print("🔄 Obtendo ID do canal...")
    try:
        broadcaster_id = fetch_broadcaster_id(client_id, token)
    except (requests.exceptions.RequestException, KeyError, IndexError) as exc:
        print(f"❌ Erro ao obter ID do canal: {exc}")
        return
    print(f"✅ ID do canal: {broadcaster_id}")

    write_env_file(
        Path(".env"),
        client_id=client_id,
        client_secret=client_secret,
        token=token,
        refresh_token=refresh_token,
        broadcaster_id=broadcaster_id,
        channel=channel,
    )

    print()
    print("=" * 60)
    print("🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print("Rode o run.bat de novo pra iniciar o chat-parade.")


if __name__ == "__main__":
    main()
