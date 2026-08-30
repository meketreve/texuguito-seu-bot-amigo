from __future__ import annotations

import re
from dataclasses import dataclass

import webcolors

from chat_parade.viewer_store import ViewerEvent, ViewerStore

HATS = ("boné", "coroa", "chifres", "nenhum")
ACCESSORIES = ("óculos", "capa", "asas", "nenhum")
NICK_MAX_LENGTH = 16
_NICK_PATTERN = re.compile(r"[^\w\sÀ-ÿ]", re.UNICODE)
_HEX_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass
class ParsedCommand:
    name: str
    args: list[str]


def parse_command(message: str) -> ParsedCommand | None:
    message = message.strip()
    if not message.startswith("!"):
        return None
    parts = message[1:].split()
    if not parts:
        return None
    return ParsedCommand(name=parts[0].lower(), args=parts[1:])


def validate_color(raw: str) -> str | None:
    raw = raw.strip()
    if _HEX_PATTERN.match(raw):
        return raw.lower()
    try:
        return webcolors.name_to_hex(raw.lower())
    except ValueError:
        return None


def validate_hat(raw: str) -> tuple[bool, str | None]:
    raw = raw.strip().lower()
    if raw not in HATS:
        return False, None
    return True, None if raw == "nenhum" else raw


def validate_accessory(raw: str) -> tuple[bool, str | None]:
    raw = raw.strip().lower()
    if raw not in ACCESSORIES:
        return False, None
    return True, None if raw == "nenhum" else raw


def validate_nick(raw: str) -> str | None:
    cleaned = _NICK_PATTERN.sub("", raw).strip()
    cleaned = cleaned[:NICK_MAX_LENGTH]
    return cleaned or None


def handle_cor(
    store: ViewerStore, username: str, args: list[str]
) -> tuple[str | None, ViewerEvent | None]:
    if not args:
        return f"@{username} uso: !cor <nome ou hex>", None
    cor = validate_color(" ".join(args))
    if cor is None:
        return (
            f"@{username} cor inválida. Use um nome CSS (ex: blue) ou hex (#rrggbb).",
            None,
        )
    store.set_color(username, cor)
    return None, ViewerEvent(type="updated", username=username.lower())


def handle_resetcor(
    store: ViewerStore, username: str, args: list[str]
) -> tuple[str | None, ViewerEvent | None]:
    store.reset_color(username)
    return None, ViewerEvent(type="updated", username=username.lower())


def handle_chapeu(
    store: ViewerStore, username: str, args: list[str]
) -> tuple[str | None, ViewerEvent | None]:
    if not args:
        return f"@{username} uso: !chapeu <boné|coroa|chifres|nenhum>", None
    ok, value = validate_hat(" ".join(args))
    if not ok:
        return f"@{username} chapéu inválido. Opções: {', '.join(HATS)}.", None
    store.set_chapeu(username, value)
    return None, ViewerEvent(type="updated", username=username.lower())


def handle_acessorio(
    store: ViewerStore, username: str, args: list[str]
) -> tuple[str | None, ViewerEvent | None]:
    if not args:
        return f"@{username} uso: !acessorio <óculos|capa|asas|nenhum>", None
    ok, value = validate_accessory(" ".join(args))
    if not ok:
        return f"@{username} acessório inválido. Opções: {', '.join(ACCESSORIES)}.", None
    store.set_acessorio(username, value)
    return None, ViewerEvent(type="updated", username=username.lower())


def handle_nick(
    store: ViewerStore, username: str, args: list[str]
) -> tuple[str | None, ViewerEvent | None]:
    if not args:
        return f"@{username} uso: !nick <apelido>", None
    nick = validate_nick(" ".join(args))
    if nick is None:
        return f"@{username} apelido inválido.", None
    store.set_nick(username, nick)
    return None, ViewerEvent(type="updated", username=username.lower())


def handle_danca(
    store: ViewerStore, username: str, args: list[str]
) -> tuple[str | None, ViewerEvent | None]:
    store.trigger_dance(username)
    return None, ViewerEvent(type="updated", username=username.lower())


def handle_avatarmod(
    store: ViewerStore, username: str, args: list[str], is_privileged: bool
) -> tuple[str | None, ViewerEvent | None]:
    if not is_privileged:
        return None, None
    if len(args) < 2:
        return f"@{username} uso: !avatarmod <usuario> <cor>", None
    target, *color_parts = args
    cor = validate_color(" ".join(color_parts))
    if cor is None:
        return f"@{username} cor inválida.", None
    store.set_color(target, cor)
    return None, ViewerEvent(type="updated", username=target.lower())
