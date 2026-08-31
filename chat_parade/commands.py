from __future__ import annotations

import re
from dataclasses import dataclass

import webcolors

from chat_parade.viewer_store import ViewerEvent, ViewerStore

HATS = ("boné", "coroa", "chifres", "nenhum")
ACCESSORIES = ("óculos", "capa", "asas", "nenhum")
NICK_MAX_LENGTH = 16
_NICK_PATTERN = re.compile(r"[^\w À-ÿ]", re.UNICODE)
_HEX_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")

# Hex values match the equivalent CSS3 name exactly (e.g. "verde" == "green",
# not "lime"), so !cor gives the same result in Portuguese or English.
PT_COLOR_NAMES: dict[str, str] = {
    "vermelho": "#ff0000",
    "verde": "#008000",
    "verde-limão": "#00ff00",
    "verde limão": "#00ff00",
    "verde-claro": "#90ee90",
    "verde claro": "#90ee90",
    "verde-escuro": "#006400",
    "verde escuro": "#006400",
    "azul": "#0000ff",
    "azul-claro": "#add8e6",
    "azul claro": "#add8e6",
    "azul-escuro": "#00008b",
    "azul escuro": "#00008b",
    "azul-marinho": "#000080",
    "azul marinho": "#000080",
    "amarelo": "#ffff00",
    "laranja": "#ffa500",
    "roxo": "#800080",
    "violeta": "#ee82ee",
    "rosa": "#ffc0cb",
    "rosa-choque": "#ff00ff",
    "rosa choque": "#ff00ff",
    "preto": "#000000",
    "branco": "#ffffff",
    "cinza": "#808080",
    "cinza-claro": "#d3d3d3",
    "cinza claro": "#d3d3d3",
    "cinza-escuro": "#a9a9a9",
    "cinza escuro": "#a9a9a9",
    "marrom": "#a52a2a",
    "castanho": "#a52a2a",
    "dourado": "#ffd700",
    "prateado": "#c0c0c0",
    "prata": "#c0c0c0",
    "turquesa": "#40e0d0",
    "bege": "#f5f5dc",
    "ciano": "#00ffff",
    "magenta": "#ff00ff",
    "vinho": "#800000",
    "bordô": "#800000",
    "salmão": "#fa8072",
    "índigo": "#4b0082",
    "coral": "#ff7f50",
}


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
    lowered = raw.lower()
    if lowered in PT_COLOR_NAMES:
        return PT_COLOR_NAMES[lowered]
    try:
        return webcolors.name_to_hex(lowered)
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
            f"@{username} cor inválida. Use um nome em português (ex: azul) ou "
            "inglês (ex: blue) ou hex (#rrggbb).",
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
