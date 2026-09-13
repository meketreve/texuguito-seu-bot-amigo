# Chat Parade Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a headless Python app that reads Twitch chat/chatters and drives a browser-source overlay showing every viewer as a pixel-art avatar walking across the stream footer, customizable via chat commands.

**Architecture:** One `asyncio` process runs three long-lived coroutines side by side: a `twitchio` chat bot (commands + badge tracking), a Helix "Get Chatters" poller (so lurkers show up too), and a headless FastAPI/uvicorn server that serves the overlay page and pushes viewer state over WebSocket. All three talk to a single in-memory `ViewerStore` backed by `data/viewers.json`. The browser-source page (plain HTML/canvas/JS) only draws what it's told — no state logic lives client-side.

**Tech Stack:** Python 3.10+, twitchio 2.10.0, FastAPI + uvicorn (headless), requests, webcolors, pytest + pytest-asyncio, vanilla JS/Canvas for the overlay page.

**Spec:** [docs/superpowers/specs/2026-08-30-chat-parade-design.md](../specs/2026-08-30-chat-parade-design.md)

## Global Constraints

- Python 3.10+ (uses `X | None` union syntax throughout).
- `twitchio==2.10.0` — pinned to match the working sibling project (`texuguito-seu-bot-amigo`); do not upgrade without re-verifying the `Chatter`/`Context`/`Bot` APIs used here.
- Reuse Twitch credentials from `../texuguito-seu-bot-amigo/.env` (`CLIENT_ID`, `TOKEN`, `BROADCASTER_ID`, `CHANNEL`) — that app already has the `moderator:read:chatters` scope needed for the chatters poller.
- The HTTP/WebSocket server always runs headless — it must never open a browser window itself, only print the local URL to the console for pasting into OBS's Browser Source.
- No cooldown/rate-limit on personalization commands (explicit user decision).
- Color input is free-form (any CSS3 color name or `#rrggbb` hex), validated but not restricted to a fixed palette.
- Viewer customization state (`cor`, `chapeu`, `acessorio`, `nick`) persists in `data/viewers.json` across restarts; live-only status (`is_mod`, `is_sub`, `is_broadcaster`, `present`, dance/cheer timers) is never persisted.
- `data/viewers.json` and `.env` are gitignored — never commit real credentials or runtime viewer data.

---

### Task 1: Project scaffolding & config loading

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `pytest.ini`
- Create: `chat_parade/__init__.py`
- Create: `chat_parade/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `chat_parade.config.Config` (frozen dataclass: `client_id: str`, `token: str`, `broadcaster_id: str`, `channel: str`, `data_dir: Path`, `overlay_port: int`), `chat_parade.config.load_config(env_path: Path | None = None) -> Config`, `chat_parade.config.MissingConfigError(RuntimeError)`.

- [ ] **Step 1: Create the requirements file**

```
twitchio==2.10.0
fastapi==0.115.0
uvicorn[standard]==0.32.0
aiofiles==24.1.0
python-dotenv==1.0.1
requests==2.32.3
webcolors==1.13
pytest==8.3.3
pytest-asyncio==0.24.0
```

Save as `requirements.txt`.

- [ ] **Step 2: Create the env example and pytest config**

`.env.example`:

```
CLIENT_ID=seu_client_id
TOKEN=seu_token
BROADCASTER_ID=seu_broadcaster_id
CHANNEL=nome_do_canal
DATA_DIR=data
OVERLAY_PORT=8901
```

`pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 3: Create the package init**

`chat_parade/__init__.py` (empty file).

- [ ] **Step 4: Write the failing test for config loading**

`tests/test_config.py`:

```python
import pytest

from chat_parade.config import MissingConfigError, load_config


def test_load_config_reads_required_fields(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIENT_ID", "abc123")
    monkeypatch.setenv("TOKEN", "tok456")
    monkeypatch.setenv("BROADCASTER_ID", "789")
    monkeypatch.setenv("CHANNEL", "meucanal")

    config = load_config(env_path=tmp_path / "does-not-exist.env")

    assert config.client_id == "abc123"
    assert config.token == "tok456"
    assert config.broadcaster_id == "789"
    assert config.channel == "meucanal"
    assert config.overlay_port == 8901


def test_load_config_raises_when_missing_fields(monkeypatch, tmp_path):
    monkeypatch.delenv("CLIENT_ID", raising=False)
    monkeypatch.delenv("TOKEN", raising=False)
    monkeypatch.delenv("BROADCASTER_ID", raising=False)
    monkeypatch.delenv("CHANNEL", raising=False)

    with pytest.raises(MissingConfigError):
        load_config(env_path=tmp_path / "does-not-exist.env")
```

- [ ] **Step 5: Run the test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chat_parade.config'` (or import error).

- [ ] **Step 6: Implement config.py**

`chat_parade/config.py`:

```python
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
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (2 tests).

- [ ] **Step 8: Install dependencies and commit**

```bash
pip install -r requirements.txt
git add requirements.txt .env.example pytest.ini chat_parade/__init__.py chat_parade/config.py tests/test_config.py
git commit -m "Add project scaffolding and env config loader"
```

---

### Task 2: Pixel-art avatar generator

**Files:**
- Create: `chat_parade/avatar.py`
- Test: `tests/test_avatar.py`

**Interfaces:**
- Consumes: nothing (pure module, stdlib only).
- Produces: `chat_parade.avatar.GRID_W: int`, `chat_parade.avatar.GRID_H: int`, `chat_parade.avatar.default_color_for(username: str) -> str`, `chat_parade.avatar.pick_template_index(username: str) -> int`, `chat_parade.avatar.build_avatar_grid(username: str, color: str, chapeu: str | None = None, acessorio: str | None = None) -> list[list[str | None]]`, `chat_parade.avatar.HATS: dict[str, tuple[str, list[tuple[int,int]]]]`, `chat_parade.avatar.ACCESSORIES: dict[str, tuple[str, list[tuple[int,int]]]]`.

- [ ] **Step 1: Write the failing tests**

`tests/test_avatar.py`:

```python
from chat_parade.avatar import (
    GRID_H,
    GRID_W,
    build_avatar_grid,
    default_color_for,
    pick_template_index,
)


def test_pick_template_index_is_deterministic():
    assert pick_template_index("Fulano") == pick_template_index("Fulano")


def test_default_color_is_deterministic():
    assert default_color_for("Fulano") == default_color_for("Fulano")


def test_default_color_is_case_insensitive():
    assert default_color_for("Fulano") == default_color_for("fulano")


def test_build_avatar_grid_has_correct_dimensions():
    grid = build_avatar_grid("Fulano", "#ff0000")
    assert len(grid) == GRID_H
    assert all(len(row) == GRID_W for row in grid)


def test_build_avatar_grid_paints_body_with_given_color():
    grid = build_avatar_grid("Fulano", "#ff0000")
    painted = {cell for row in grid for cell in row if cell is not None}
    assert "#ff0000" in painted


def test_build_avatar_grid_without_hat_has_empty_hat_row():
    grid = build_avatar_grid("Fulano", "#ff0000")
    assert all(cell is None for cell in grid[0])


def test_build_avatar_grid_with_hat_paints_hat_row():
    grid = build_avatar_grid("Fulano", "#ff0000", chapeu="boné")
    assert any(cell is not None for cell in grid[0])


def test_build_avatar_grid_with_unknown_hat_is_ignored():
    grid = build_avatar_grid("Fulano", "#ff0000", chapeu="sombrinha")
    assert all(cell is None for cell in grid[0])


def test_different_usernames_can_get_different_templates():
    templates_seen = {pick_template_index(f"user{i}") for i in range(30)}
    assert len(templates_seen) > 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_avatar.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chat_parade.avatar'`.

- [ ] **Step 3: Implement avatar.py**

`chat_parade/avatar.py`:

```python
from __future__ import annotations

import hashlib
import random

GRID_W = 10
GRID_H = 13  # linha 0 é reservada para chapéu/coroa/chifres

BASE_TEMPLATES: list[list[list[int]]] = [
    # Template 0: robusto
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
    ],
    # Template 1: magrelo
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
    ],
    # Template 2: quadrado
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
    ],
]

EYE_COLOR = "#1a1a1a"
# Linha 3 = olhar normal, linha 2 = olhar pra cima. As colunas (4, 5) caem
# dentro do corpo em todos os templates acima.
EYE_VARIANTS: list[list[tuple[int, int]]] = [
    [(3, 4), (3, 5)],
    [(2, 4), (2, 5)],
]

DEFAULT_COLOR_PALETTE = [
    "#e74c3c", "#3498db", "#2ecc71", "#f1c40f",
    "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
]

HATS: dict[str, tuple[str, list[tuple[int, int]]]] = {
    "boné": ("#2b6cb0", [(0, 3), (0, 4), (0, 5), (0, 6)]),
    "coroa": ("#f6c90e", [(0, 3), (0, 5), (0, 7)]),
    "chifres": ("#7b3f00", [(0, 2), (0, 7)]),
}

ACCESSORIES: dict[str, tuple[str, list[tuple[int, int]]]] = {
    "óculos": ("#1a1a1a", [(3, 3), (3, 6)]),
    "capa": ("#c0392b", [(5, 1), (6, 1), (7, 1)]),
    "asas": ("#f5f5f5", [(5, 0), (5, 9), (6, 0), (6, 9)]),
}


def _seed_int(username: str) -> int:
    digest = hashlib.sha256(username.lower().encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def pick_template_index(username: str) -> int:
    rng = random.Random(_seed_int(username))
    return rng.randrange(len(BASE_TEMPLATES))


def pick_eye_variant(username: str) -> int:
    rng = random.Random(_seed_int(username) + 1)
    return rng.randrange(len(EYE_VARIANTS))


def default_color_for(username: str) -> str:
    rng = random.Random(_seed_int(username) + 2)
    return rng.choice(DEFAULT_COLOR_PALETTE)


def build_avatar_grid(
    username: str,
    color: str,
    chapeu: str | None = None,
    acessorio: str | None = None,
) -> list[list[str | None]]:
    template = BASE_TEMPLATES[pick_template_index(username)]

    grid: list[list[str | None]] = [
        [color if cell else None for cell in row] for row in template
    ]

    for row, col in EYE_VARIANTS[pick_eye_variant(username)]:
        grid[row][col] = EYE_COLOR

    if chapeu in HATS:
        hat_color, pixels = HATS[chapeu]
        for row, col in pixels:
            grid[row][col] = hat_color

    if acessorio in ACCESSORIES:
        acc_color, pixels = ACCESSORIES[acessorio]
        for row, col in pixels:
            grid[row][col] = acc_color

    return grid
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_avatar.py -v`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add chat_parade/avatar.py tests/test_avatar.py
git commit -m "Add deterministic pixel-art avatar generator"
```

---

### Task 3: Viewer store (state + persistence)

**Files:**
- Create: `chat_parade/viewer_store.py`
- Test: `tests/test_viewer_store.py`

**Interfaces:**
- Consumes: `chat_parade.avatar.default_color_for(username: str) -> str` (Task 2).
- Produces: `chat_parade.viewer_store.Viewer` (dataclass: `cor: str`, `chapeu: str | None`, `acessorio: str | None`, `nick: str | None`, `primeira_vez: str`, `ultima_vez: str`), `chat_parade.viewer_store.ViewerStatus` (dataclass: `is_mod: bool`, `is_sub: bool`, `is_broadcaster: bool`, `present: bool`, `dancing_until: float`, `cheer_until: float`), `chat_parade.viewer_store.ViewerEvent` (dataclass: `type: str`, `username: str`), `chat_parade.viewer_store.ViewerStore(path: Path)` with methods `load()`, `save()`, `get_or_create(username: str) -> Viewer`, `status_for(username: str) -> ViewerStatus`, `usernames() -> list[str]`, `set_color(username: str, cor: str) -> None`, `reset_color(username: str) -> None`, `set_chapeu(username: str, chapeu: str | None) -> None`, `set_acessorio(username: str, acessorio: str | None) -> None`, `set_nick(username: str, nick: str | None) -> None`, `mark_status_from_message(username: str, is_mod: bool, is_sub: bool, is_broadcaster: bool) -> None`, `trigger_dance(username: str) -> None`, `trigger_cheer(username: str) -> None`, `sync_present_chatters(usernames: set[str]) -> tuple[set[str], set[str]]` (returns `(joined, left)`).

- [ ] **Step 1: Write the failing tests**

`tests/test_viewer_store.py`:

```python
from chat_parade.viewer_store import ViewerStore


def test_get_or_create_assigns_deterministic_default_color(tmp_path):
    store = ViewerStore(tmp_path / "viewers.json")
    viewer = store.get_or_create("Fulano")
    assert viewer.cor
    assert store.get_or_create("fulano").cor == viewer.cor


def test_set_color_persists_across_store_instances(tmp_path):
    path = tmp_path / "viewers.json"
    store = ViewerStore(path)
    store.set_color("fulano", "#ff8800")

    reloaded = ViewerStore(path)
    assert reloaded.get_or_create("fulano").cor == "#ff8800"


def test_reset_color_reverts_to_seed_default(tmp_path):
    store = ViewerStore(tmp_path / "viewers.json")
    original = store.get_or_create("fulano").cor
    store.set_color("fulano", "#000000")
    store.reset_color("fulano")
    assert store.get_or_create("fulano").cor == original


def test_set_chapeu_and_acessorio_update_viewer(tmp_path):
    store = ViewerStore(tmp_path / "viewers.json")
    store.set_chapeu("fulano", "boné")
    store.set_acessorio("fulano", "capa")
    viewer = store.get_or_create("fulano")
    assert viewer.chapeu == "boné"
    assert viewer.acessorio == "capa"


def test_sync_present_chatters_reports_joined_and_left(tmp_path):
    store = ViewerStore(tmp_path / "viewers.json")

    joined, left = store.sync_present_chatters({"ana", "bruno"})
    assert joined == {"ana", "bruno"}
    assert left == set()

    joined, left = store.sync_present_chatters({"ana"})
    assert joined == set()
    assert left == {"bruno"}


def test_mark_status_from_message_updates_status(tmp_path):
    store = ViewerStore(tmp_path / "viewers.json")
    store.mark_status_from_message("fulano", is_mod=True, is_sub=False, is_broadcaster=False)
    status = store.status_for("fulano")
    assert status.is_mod is True
    assert status.present is True


def test_trigger_dance_sets_future_timestamp(tmp_path):
    store = ViewerStore(tmp_path / "viewers.json")
    store.trigger_dance("fulano")
    assert store.status_for("fulano").dancing_until > 0


def test_status_is_never_written_to_disk(tmp_path):
    path = tmp_path / "viewers.json"
    store = ViewerStore(path)
    store.mark_status_from_message("fulano", is_mod=True, is_sub=True, is_broadcaster=False)

    raw = path.read_text(encoding="utf-8")
    assert "is_mod" not in raw
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_viewer_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chat_parade.viewer_store'`.

- [ ] **Step 3: Implement viewer_store.py**

`chat_parade/viewer_store.py`:

```python
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from chat_parade.avatar import default_color_for

DANCE_DURATION_SECONDS = 4.0
CHEER_DURATION_SECONDS = 4.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Viewer:
    cor: str
    chapeu: str | None = None
    acessorio: str | None = None
    nick: str | None = None
    primeira_vez: str = field(default_factory=_now_iso)
    ultima_vez: str = field(default_factory=_now_iso)


@dataclass
class ViewerStatus:
    is_mod: bool = False
    is_sub: bool = False
    is_broadcaster: bool = False
    present: bool = False
    dancing_until: float = 0.0
    cheer_until: float = 0.0


@dataclass
class ViewerEvent:
    type: str  # "joined" | "left" | "updated"
    username: str


class ViewerStore:
    def __init__(self, path: Path):
        self._path = path
        self._viewers: dict[str, Viewer] = {}
        self._status: dict[str, ViewerStatus] = {}
        self.load()

    def load(self) -> None:
        if not self._path.exists():
            self._viewers = {}
            return
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        self._viewers = {name: Viewer(**data) for name, data in raw.items()}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        raw = {name: asdict(viewer) for name, viewer in self._viewers.items()}
        self._path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_or_create(self, username: str) -> Viewer:
        username = username.lower()
        if username not in self._viewers:
            self._viewers[username] = Viewer(cor=default_color_for(username))
            self._status[username] = ViewerStatus()
            self.save()
        return self._viewers[username]

    def status_for(self, username: str) -> ViewerStatus:
        username = username.lower()
        return self._status.setdefault(username, ViewerStatus())

    def usernames(self) -> list[str]:
        return list(self._viewers.keys())

    def set_color(self, username: str, cor: str) -> None:
        viewer = self.get_or_create(username)
        viewer.cor = cor
        viewer.ultima_vez = _now_iso()
        self.save()

    def reset_color(self, username: str) -> None:
        username = username.lower()
        self.set_color(username, default_color_for(username))

    def set_chapeu(self, username: str, chapeu: str | None) -> None:
        viewer = self.get_or_create(username)
        viewer.chapeu = chapeu
        viewer.ultima_vez = _now_iso()
        self.save()

    def set_acessorio(self, username: str, acessorio: str | None) -> None:
        viewer = self.get_or_create(username)
        viewer.acessorio = acessorio
        viewer.ultima_vez = _now_iso()
        self.save()

    def set_nick(self, username: str, nick: str | None) -> None:
        viewer = self.get_or_create(username)
        viewer.nick = nick
        viewer.ultima_vez = _now_iso()
        self.save()

    def mark_status_from_message(
        self, username: str, is_mod: bool, is_sub: bool, is_broadcaster: bool
    ) -> None:
        self.get_or_create(username)
        status = self.status_for(username)
        status.is_mod = is_mod
        status.is_sub = is_sub
        status.is_broadcaster = is_broadcaster
        status.present = True

    def trigger_dance(self, username: str) -> None:
        self.get_or_create(username)
        self.status_for(username).dancing_until = time.time() + DANCE_DURATION_SECONDS

    def trigger_cheer(self, username: str) -> None:
        self.get_or_create(username)
        self.status_for(username).cheer_until = time.time() + CHEER_DURATION_SECONDS

    def sync_present_chatters(self, usernames: set[str]) -> tuple[set[str], set[str]]:
        usernames = {u.lower() for u in usernames}
        currently_present = {
            name for name, status in self._status.items() if status.present
        }

        joined = usernames - currently_present
        left = currently_present - usernames

        for username in joined:
            self.get_or_create(username)
            self.status_for(username).present = True

        for username in left:
            self.status_for(username).present = False

        return joined, left
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_viewer_store.py -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add chat_parade/viewer_store.py tests/test_viewer_store.py
git commit -m "Add viewer state store with JSON persistence"
```

---

### Task 4: Chat command parsing, validation and handlers

**Files:**
- Create: `chat_parade/commands.py`
- Test: `tests/test_commands.py`

**Interfaces:**
- Consumes: `chat_parade.viewer_store.ViewerStore`, `chat_parade.viewer_store.ViewerEvent` (Task 3).
- Produces: `chat_parade.commands.ParsedCommand` (dataclass: `name: str`, `args: list[str]`), `chat_parade.commands.parse_command(message: str) -> ParsedCommand | None`, `chat_parade.commands.validate_color(raw: str) -> str | None`, `chat_parade.commands.validate_hat(raw: str) -> tuple[bool, str | None]`, `chat_parade.commands.validate_accessory(raw: str) -> tuple[bool, str | None]`, `chat_parade.commands.validate_nick(raw: str) -> str | None`, `chat_parade.commands.HATS: tuple[str, ...]`, `chat_parade.commands.ACCESSORIES: tuple[str, ...]`, and handlers all shaped `(store, username, args, **kwargs) -> tuple[str | None, ViewerEvent | None]`: `handle_cor`, `handle_resetcor`, `handle_chapeu`, `handle_acessorio`, `handle_nick`, `handle_danca`, `handle_avatarmod(store, username, args, is_privileged: bool)`.

- [ ] **Step 1: Write the failing tests**

`tests/test_commands.py`:

```python
from chat_parade.commands import (
    handle_acessorio,
    handle_avatarmod,
    handle_chapeu,
    handle_cor,
    handle_danca,
    handle_nick,
    handle_resetcor,
    parse_command,
    validate_accessory,
    validate_color,
    validate_hat,
    validate_nick,
)
from chat_parade.viewer_store import ViewerStore


def test_parse_command_extracts_name_and_args():
    parsed = parse_command("!cor azul escuro")
    assert parsed.name == "cor"
    assert parsed.args == ["azul", "escuro"]


def test_parse_command_returns_none_for_non_commands():
    assert parse_command("oi gente") is None


def test_parse_command_returns_none_for_bare_prefix():
    assert parse_command("!") is None


def test_validate_color_accepts_hex():
    assert validate_color("#FF8800") == "#ff8800"


def test_validate_color_accepts_css_name():
    assert validate_color("red") == "#ff0000"


def test_validate_color_rejects_garbage():
    assert validate_color("banana123") is None


def test_validate_hat_accepts_known_values():
    assert validate_hat("boné") == (True, "boné")
    assert validate_hat("nenhum") == (True, None)


def test_validate_hat_rejects_unknown():
    assert validate_hat("sombrinha") == (False, None)


def test_validate_accessory_accepts_known_values():
    assert validate_accessory("capa") == (True, "capa")


def test_validate_nick_strips_forbidden_chars_and_truncates():
    assert validate_nick("Rei!!! do Chat 999999999999") == "Rei do Chat 9999"


def test_validate_nick_keeps_accented_letters():
    assert validate_nick("João") == "João"


def test_validate_nick_returns_none_for_empty_result():
    assert validate_nick("!!!@@@") is None


def test_handle_cor_updates_store_on_valid_color(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_cor(store, "fulano", ["#123456"])
    assert reply is None
    assert event.type == "updated"
    assert event.username == "fulano"
    assert store.get_or_create("fulano").cor == "#123456"


def test_handle_cor_replies_error_on_invalid_color(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_cor(store, "fulano", ["naoexiste123"])
    assert reply is not None
    assert event is None


def test_handle_cor_replies_usage_when_no_args(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_cor(store, "fulano", [])
    assert reply is not None
    assert event is None


def test_handle_resetcor_reverts_to_default(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    default = store.get_or_create("fulano").cor
    store.set_color("fulano", "#000000")

    reply, event = handle_resetcor(store, "fulano", [])

    assert reply is None
    assert event.type == "updated"
    assert store.get_or_create("fulano").cor == default


def test_handle_chapeu_sets_value(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_chapeu(store, "fulano", ["coroa"])
    assert reply is None
    assert store.get_or_create("fulano").chapeu == "coroa"


def test_handle_acessorio_rejects_unknown(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_acessorio(store, "fulano", ["jetpack"])
    assert reply is not None
    assert event is None


def test_handle_nick_sets_value(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_nick(store, "fulano", ["Rei", "do", "Chat"])
    assert reply is None
    assert store.get_or_create("fulano").nick == "Rei do Chat"


def test_handle_danca_triggers_dance(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_danca(store, "fulano", [])
    assert reply is None
    assert event.type == "updated"
    assert store.status_for("fulano").dancing_until > 0


def test_handle_avatarmod_ignored_when_not_privileged(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_avatarmod(
        store, "fulano", ["outrapessoa", "red"], is_privileged=False
    )
    assert reply is None
    assert event is None


def test_handle_avatarmod_changes_target_when_privileged(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_avatarmod(
        store, "mod1", ["outrapessoa", "red"], is_privileged=True
    )
    assert event.username == "outrapessoa"
    assert store.get_or_create("outrapessoa").cor == "#ff0000"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_commands.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chat_parade.commands'`.

- [ ] **Step 3: Implement commands.py**

`chat_parade/commands.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_commands.py -v`
Expected: PASS (22 tests).

- [ ] **Step 5: Commit**

```bash
git add chat_parade/commands.py tests/test_commands.py
git commit -m "Add chat command parsing, validation and handlers"
```

---

### Task 5: Headless web server + overlay frontend

**Files:**
- Create: `chat_parade/web_server.py`
- Create: `web/overlay.html`
- Create: `web/overlay.js`
- Test: `tests/test_web_server.py`

**Interfaces:**
- Consumes: `chat_parade.viewer_store.ViewerStore`, `chat_parade.viewer_store.ViewerEvent` (Task 3), `chat_parade.avatar.build_avatar_grid` (Task 2).
- Produces: `chat_parade.web_server.viewer_payload(store: ViewerStore, username: str) -> dict`, `chat_parade.web_server.snapshot_payload(store: ViewerStore) -> dict`, `chat_parade.web_server.OverlayBroadcaster(store, events: asyncio.Queue[ViewerEvent])` with `async register(websocket) -> None`, `unregister(websocket) -> None`, `async run() -> None` (consumes the queue forever), `chat_parade.web_server.create_app(store: ViewerStore, events: asyncio.Queue[ViewerEvent]) -> tuple[FastAPI, OverlayBroadcaster]`.

- [ ] **Step 1: Write the failing tests**

`tests/test_web_server.py`:

```python
import asyncio

from fastapi.testclient import TestClient

from chat_parade.viewer_store import ViewerStore
from chat_parade.web_server import create_app


def test_websocket_sends_initial_snapshot(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    store.get_or_create("fulano")
    store.status_for("fulano").present = True
    events: asyncio.Queue = asyncio.Queue()
    app, _ = create_app(store, events)

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()

    assert data["type"] == "snapshot"
    assert data["viewers"][0]["username"] == "fulano"


def test_websocket_snapshot_excludes_absent_viewers(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    store.get_or_create("ausente")  # never marked present
    events: asyncio.Queue = asyncio.Queue()
    app, _ = create_app(store, events)

    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()

    assert data["viewers"] == []


def test_overlay_page_is_served(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    app, _ = create_app(store, events)

    client = TestClient(app)
    response = client.get("/overlay")

    assert response.status_code == 200
    assert b"parade" in response.content
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_web_server.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chat_parade.web_server'`.

- [ ] **Step 3: Implement web_server.py**

`chat_parade/web_server.py`:

```python
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from chat_parade.avatar import build_avatar_grid
from chat_parade.viewer_store import ViewerEvent, ViewerStore

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def viewer_payload(store: ViewerStore, username: str) -> dict[str, Any]:
    viewer = store.get_or_create(username)
    status = store.status_for(username)
    return {
        "username": username,
        "nick": viewer.nick or username,
        "grid": build_avatar_grid(username, viewer.cor, viewer.chapeu, viewer.acessorio),
        "is_mod": status.is_mod,
        "is_sub": status.is_sub,
        "is_broadcaster": status.is_broadcaster,
        "dancing": status.dancing_until > time.time(),
        "cheering": status.cheer_until > time.time(),
    }


def snapshot_payload(store: ViewerStore) -> dict[str, Any]:
    present = [
        viewer_payload(store, name)
        for name in store.usernames()
        if store.status_for(name).present
    ]
    return {"type": "snapshot", "viewers": present}


class OverlayBroadcaster:
    def __init__(self, store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"):
        self._store = store
        self._events = events
        self._connections: set[WebSocket] = set()

    async def register(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        await websocket.send_json(snapshot_payload(self._store))

    def unregister(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def run(self) -> None:
        while True:
            event = await self._events.get()
            message = {
                "type": event.type,
                "username": event.username,
                "viewer": None if event.type == "left" else viewer_payload(self._store, event.username),
            }
            await self._broadcast(message)

    async def _broadcast(self, message: dict[str, Any]) -> None:
        stale = set()
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                stale.add(connection)
        self._connections -= stale


def create_app(
    store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"
) -> tuple[FastAPI, OverlayBroadcaster]:
    app = FastAPI()
    broadcaster = OverlayBroadcaster(store, events)

    @app.get("/overlay")
    async def overlay_page() -> FileResponse:
        return FileResponse(WEB_DIR / "overlay.html")

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await broadcaster.register(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            broadcaster.unregister(websocket)

    return app, broadcaster
```

- [ ] **Step 4: Create the overlay page**

`web/overlay.html`:

```html
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <title>chat-parade overlay</title>
  <style>
    html, body { margin: 0; padding: 0; background: transparent; overflow: hidden; }
    canvas { display: block; }
  </style>
</head>
<body>
  <canvas id="parade" width="1920" height="160"></canvas>
  <script src="/static/overlay.js"></script>
</body>
</html>
```

- [ ] **Step 5: Create the overlay animation script**

`web/overlay.js`:

```javascript
const PIXEL_SIZE = 4;
const SPEED_PX_PER_SEC = 60;
const canvas = document.getElementById("parade");
const ctx = canvas.getContext("2d");

const viewers = new Map();

function laneY() {
  return canvas.height - PIXEL_SIZE * 13 - 10;
}

function spawnX() {
  return canvas.width + Math.random() * 200;
}

function upsertViewer(payload) {
  const existing = viewers.get(payload.username);
  const x = existing ? existing.x : spawnX();
  viewers.set(payload.username, { ...payload, x, y: laneY() });
}

function removeViewer(username) {
  viewers.delete(username);
}

function applySnapshot(snapshot) {
  viewers.clear();
  for (const viewer of snapshot.viewers) {
    upsertViewer(viewer);
  }
}

function connect() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${protocol}//${location.host}/ws`);

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "snapshot") {
      applySnapshot(message);
    } else if (message.type === "left") {
      removeViewer(message.username);
    } else {
      upsertViewer(message.viewer);
    }
  };

  ws.onclose = () => {
    setTimeout(connect, 1000);
  };
}

function drawBadges(viewer, yOffset, width) {
  let label = "";
  if (viewer.is_broadcaster) label = "♛";
  else if (viewer.is_mod) label = "MOD";
  if (label) {
    ctx.fillStyle = "#ffffff";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(label, viewer.x + width / 2, yOffset - 14);
  }
  if (viewer.is_sub) {
    ctx.strokeStyle = "#f6c90e";
    ctx.lineWidth = 1;
    ctx.strokeRect(viewer.x - 1, yOffset - 1, width + 2, viewer.grid.length * PIXEL_SIZE + 2);
  }
}

function drawViewer(viewer, timestamp) {
  const grid = viewer.grid;
  const width = grid[0].length * PIXEL_SIZE;
  const bounce = viewer.dancing ? Math.abs(Math.sin(timestamp / 120)) * 6 : 0;
  const yOffset = viewer.y - bounce;

  if (viewer.cheering) {
    ctx.beginPath();
    ctx.strokeStyle = "#ffd700";
    ctx.lineWidth = 2;
    ctx.arc(
      viewer.x + width / 2,
      yOffset + (grid.length * PIXEL_SIZE) / 2,
      grid.length * PIXEL_SIZE * 0.7,
      0,
      Math.PI * 2
    );
    ctx.stroke();
  }

  for (let row = 0; row < grid.length; row++) {
    for (let col = 0; col < grid[row].length; col++) {
      const color = grid[row][col];
      if (!color) continue;
      ctx.fillStyle = color;
      ctx.fillRect(viewer.x + col * PIXEL_SIZE, yOffset + row * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE);
    }
  }

  drawBadges(viewer, yOffset, width);

  ctx.fillStyle = "#ffffff";
  ctx.font = "10px monospace";
  ctx.textAlign = "center";
  ctx.fillText(viewer.nick, viewer.x + width / 2, yOffset - 4);
}

let lastTimestamp = performance.now();

function tick(timestamp) {
  const deltaSeconds = (timestamp - lastTimestamp) / 1000;
  lastTimestamp = timestamp;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (const viewer of viewers.values()) {
    viewer.x -= SPEED_PX_PER_SEC * deltaSeconds;
    const width = viewer.grid[0].length * PIXEL_SIZE;
    if (viewer.x < -width) {
      viewer.x = spawnX();
    }
    drawViewer(viewer, timestamp);
  }

  requestAnimationFrame(tick);
}

connect();
requestAnimationFrame(tick);
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/test_web_server.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7: Commit**

```bash
git add chat_parade/web_server.py web/overlay.html web/overlay.js tests/test_web_server.py
git commit -m "Add headless FastAPI overlay server and canvas frontend"
```

---

### Task 6: Twitch chat bot wiring

**Files:**
- Create: `chat_parade/twitch_chat.py`
- Test: `tests/test_twitch_chat.py`

**Interfaces:**
- Consumes: `chat_parade.config.Config` (Task 1), `chat_parade.viewer_store.ViewerStore`, `chat_parade.viewer_store.ViewerEvent` (Task 3), `chat_parade.commands.handle_*` (Task 4).
- Produces: `chat_parade.twitch_chat.ChatParadeBot(config: Config, store: ViewerStore, events: asyncio.Queue[ViewerEvent])` (subclass of `twitchio.ext.commands.Bot`).

- [ ] **Step 1: Write the failing test**

`tests/test_twitch_chat.py`:

```python
import asyncio

from chat_parade.config import Config
from chat_parade.twitch_chat import ChatParadeBot
from chat_parade.viewer_store import ViewerStore


def _config(tmp_path) -> Config:
    return Config(
        client_id="id",
        token="tok",
        broadcaster_id="1",
        channel="meucanal",
        data_dir=tmp_path,
        overlay_port=8901,
    )


def test_bot_constructs_without_touching_the_network(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    bot = ChatParadeBot(_config(tmp_path), store, events)

    assert bot is not None
    assert bot._store is store
    assert bot._events is events
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_twitch_chat.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chat_parade.twitch_chat'`.

- [ ] **Step 3: Implement twitch_chat.py**

`chat_parade/twitch_chat.py`:

```python
from __future__ import annotations

import asyncio

from twitchio.ext import commands

from chat_parade import commands as cmds
from chat_parade.config import Config
from chat_parade.viewer_store import ViewerEvent, ViewerStore


class ChatParadeBot(commands.Bot):
    def __init__(self, config: Config, store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"):
        super().__init__(
            token=f"oauth:{config.token}",
            prefix="!",
            initial_channels=[config.channel],
        )
        self._store = store
        self._events = events

    async def event_ready(self) -> None:
        print(f"[chat-parade] conectado ao chat de {self.nick}")

    async def event_message(self, message) -> None:
        if message.echo or not message.author:
            return

        self._store.mark_status_from_message(
            message.author.name,
            is_mod=message.author.is_mod,
            is_sub=message.author.is_subscriber,
            is_broadcaster=message.author.is_broadcaster,
        )

        tags = message.tags or {}
        bits = tags.get("bits")
        if bits and int(bits) > 0:
            self._store.trigger_cheer(message.author.name)

        await self._events.put(ViewerEvent(type="updated", username=message.author.name.lower()))

        await self.handle_commands(message)

    async def _respond(self, ctx, username: str, args: list[str], handler, **kwargs) -> None:
        reply, event = handler(self._store, username, args, **kwargs)
        if reply:
            await ctx.send(reply)
        if event:
            await self._events.put(event)

    @commands.command(name="cor")
    async def cor_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, ctx.message.content.split()[1:], cmds.handle_cor)

    @commands.command(name="resetcor")
    async def resetcor_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, [], cmds.handle_resetcor)

    @commands.command(name="chapeu")
    async def chapeu_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, ctx.message.content.split()[1:], cmds.handle_chapeu)

    @commands.command(name="acessorio")
    async def acessorio_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, ctx.message.content.split()[1:], cmds.handle_acessorio)

    @commands.command(name="nick")
    async def nick_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, ctx.message.content.split()[1:], cmds.handle_nick)

    @commands.command(name="dança", aliases=["danca"])
    async def danca_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, [], cmds.handle_danca)

    @commands.command(name="avatarmod")
    async def avatarmod_cmd(self, ctx: commands.Context) -> None:
        is_privileged = ctx.author.is_mod or ctx.author.is_broadcaster
        await self._respond(
            ctx,
            ctx.author.name,
            ctx.message.content.split()[1:],
            cmds.handle_avatarmod,
            is_privileged=is_privileged,
        )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_twitch_chat.py -v`
Expected: PASS (1 test). This only proves the bot wires up without raising; real IRC behavior is covered by the manual test in Task 9 since it needs a live connection.

- [ ] **Step 5: Commit**

```bash
git add chat_parade/twitch_chat.py tests/test_twitch_chat.py
git commit -m "Add twitchio bot wiring chat commands to the viewer store"
```

---

### Task 7: Chatters poller (lurkers included)

**Files:**
- Create: `chat_parade/chatters_poller.py`
- Test: `tests/test_chatters_poller.py`

**Interfaces:**
- Consumes: `chat_parade.config.Config` (Task 1), `chat_parade.viewer_store.ViewerStore`, `chat_parade.viewer_store.ViewerEvent` (Task 3).
- Produces: `chat_parade.chatters_poller.fetch_chatters(config: Config) -> set[str]`, `chat_parade.chatters_poller.poll_once(config, store, events) -> None`, `chat_parade.chatters_poller.run_chatters_poller(config, store, events) -> None` (infinite loop), `chat_parade.chatters_poller.POLL_INTERVAL_SECONDS: int`.

- [ ] **Step 1: Write the failing tests**

`tests/test_chatters_poller.py`:

```python
import asyncio
from unittest.mock import Mock, patch

import pytest

from chat_parade.chatters_poller import fetch_chatters, poll_once
from chat_parade.config import Config
from chat_parade.viewer_store import ViewerStore


def _config(tmp_path) -> Config:
    return Config(
        client_id="id",
        token="tok",
        broadcaster_id="1",
        channel="canal",
        data_dir=tmp_path,
        overlay_port=8901,
    )


def test_fetch_chatters_parses_usernames(tmp_path):
    fake_response = Mock(status_code=200)
    fake_response.json.return_value = {
        "data": [{"user_name": "Ana"}, {"user_name": "BRUNO"}]
    }
    with patch("chat_parade.chatters_poller.requests.get", return_value=fake_response):
        result = fetch_chatters(_config(tmp_path))

    assert result == {"ana", "bruno"}


def test_fetch_chatters_raises_on_error_status(tmp_path):
    fake_response = Mock(status_code=401, text="unauthorized")
    with patch("chat_parade.chatters_poller.requests.get", return_value=fake_response):
        with pytest.raises(RuntimeError):
            fetch_chatters(_config(tmp_path))


async def test_poll_once_enqueues_joined_events(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    with patch("chat_parade.chatters_poller.fetch_chatters", return_value={"ana"}):
        await poll_once(_config(tmp_path), store, events)

    event = events.get_nowait()
    assert event.type == "joined"
    assert event.username == "ana"


async def test_poll_once_swallows_fetch_errors(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    with patch(
        "chat_parade.chatters_poller.fetch_chatters",
        side_effect=RuntimeError("boom"),
    ):
        await poll_once(_config(tmp_path), store, events)

    assert events.empty()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_chatters_poller.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chat_parade.chatters_poller'`.

- [ ] **Step 3: Implement chatters_poller.py**

`chat_parade/chatters_poller.py`:

```python
from __future__ import annotations

import asyncio

import requests

from chat_parade.config import Config
from chat_parade.viewer_store import ViewerEvent, ViewerStore

CHATTERS_URL = "https://api.twitch.tv/helix/chat/chatters"
POLL_INTERVAL_SECONDS = 45


def fetch_chatters(config: Config) -> set[str]:
    response = requests.get(
        CHATTERS_URL,
        params={
            "broadcaster_id": config.broadcaster_id,
            "moderator_id": config.broadcaster_id,
        },
        headers={
            "Client-Id": config.client_id,
            "Authorization": f"Bearer {config.token}",
        },
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Helix chatters falhou: {response.status_code} {response.text}")
    return {entry["user_name"].lower() for entry in response.json().get("data", [])}


async def poll_once(
    config: Config, store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"
) -> None:
    loop = asyncio.get_event_loop()
    try:
        chatters = await loop.run_in_executor(None, fetch_chatters, config)
    except Exception as exc:
        print(f"[chat-parade] erro ao buscar chatters: {exc}")
        return

    joined, left = store.sync_present_chatters(chatters)
    for username in joined:
        await events.put(ViewerEvent(type="joined", username=username))
    for username in left:
        await events.put(ViewerEvent(type="left", username=username))


async def run_chatters_poller(
    config: Config, store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"
) -> None:
    while True:
        await poll_once(config, store, events)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_chatters_poller.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add chat_parade/chatters_poller.py tests/test_chatters_poller.py
git commit -m "Add Helix chatters poller so lurkers show up in the parade"
```

---

### Task 8: Main orchestration (headless entrypoint)

**Files:**
- Create: `chat_parade/main.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `chat_parade.config.load_config` (Task 1), `chat_parade.viewer_store.ViewerStore`, `chat_parade.viewer_store.ViewerEvent` (Task 3), `chat_parade.web_server.create_app` (Task 5), `chat_parade.twitch_chat.ChatParadeBot` (Task 6), `chat_parade.chatters_poller.run_chatters_poller` (Task 7).
- Produces: `chat_parade.main.build_components(config: Config) -> tuple[ViewerStore, asyncio.Queue, FastAPI, OverlayBroadcaster, ChatParadeBot]`, `chat_parade.main.main() -> None` (coroutine).

- [ ] **Step 1: Write the failing test**

`tests/test_main.py`:

```python
from chat_parade.config import Config
from chat_parade.main import build_components


async def test_build_components_wires_everything_without_network(tmp_path):
    config = Config(
        client_id="id",
        token="tok",
        broadcaster_id="1",
        channel="canal",
        data_dir=tmp_path,
        overlay_port=8901,
    )

    store, events, app, broadcaster, bot = build_components(config)

    assert store is not None
    assert events.empty()
    assert app is not None
    assert broadcaster is not None
    assert bot is not None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chat_parade.main'`.

- [ ] **Step 3: Implement main.py**

`chat_parade/main.py`:

```python
from __future__ import annotations

import asyncio

import uvicorn

from chat_parade.chatters_poller import run_chatters_poller
from chat_parade.config import Config, load_config
from chat_parade.twitch_chat import ChatParadeBot
from chat_parade.viewer_store import ViewerEvent, ViewerStore
from chat_parade.web_server import create_app


def build_components(config: Config):
    store = ViewerStore(config.data_dir / "viewers.json")
    events: "asyncio.Queue[ViewerEvent]" = asyncio.Queue()
    app, broadcaster = create_app(store, events)
    bot = ChatParadeBot(config, store, events)
    return store, events, app, broadcaster, bot


async def _run_web_server(app, port: int) -> None:
    server_config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(server_config)
    await server.serve()


async def main() -> None:
    config = load_config()
    store, events, app, broadcaster, bot = build_components(config)

    print(f"[chat-parade] overlay pronto em: http://localhost:{config.overlay_port}/overlay")
    print("[chat-parade] cole essa URL como Browser Source no OBS.")

    await asyncio.gather(
        bot.start(),
        run_chatters_poller(config, store, events),
        broadcaster.run(),
        _run_web_server(app, config.overlay_port),
    )


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: PASS (1 test).

- [ ] **Step 5: Run the full test suite**

Run: `pytest -v`
Expected: PASS, all tests across every task green.

- [ ] **Step 6: Commit**

```bash
git add chat_parade/main.py tests/test_main.py
git commit -m "Add headless main entrypoint wiring bot, poller and web server"
```

---

### Task 9: README, .env setup and manual verification

**Files:**
- Create: `README.md`
- Modify: `.env` (created locally from the sibling project's credentials, never committed)

**Interfaces:**
- Consumes: nothing new — this task documents and wires up runtime config for everything built in Tasks 1-8.

- [ ] **Step 1: Write the README**

`README.md`:

```markdown
# chat-parade

Overlay pixel art pra live na Twitch: todo mundo assistindo aparece andando
no rodapé da stream, com avatar gerado automaticamente e personalizável via
comandos no chat.

## Setup

1. `pip install -r requirements.txt`
2. Copie `.env.example` pra `.env` e preencha com as credenciais do seu app
   Twitch (pode reaproveitar as mesmas do `texuguito-seu-bot-amigo`, que já
   tem o escopo `moderator:read:chatters`):

   ```
   CLIENT_ID=...
   TOKEN=...
   BROADCASTER_ID=...
   CHANNEL=...
   ```

3. Rode os testes: `pytest`
4. Suba o app: `python -m chat_parade.main`

O processo não abre navegador nenhum — ele imprime no console algo como:

```
[chat-parade] overlay pronto em: http://localhost:8901/overlay
[chat-parade] cole essa URL como Browser Source no OBS.
```

Cole essa URL num Browser Source do OBS (largura/altura à sua escolha, fundo
já é transparente).

## Comandos do chat

| Comando | Quem pode | Efeito |
| --- | --- | --- |
| `!cor <nome ou hex>` | Todos, no próprio avatar | Troca a cor do corpo. |
| `!resetcor` | Todos, no próprio avatar | Volta pra cor gerada pela seed. |
| `!chapeu <boné\|coroa\|chifres\|nenhum>` | Todos, no próprio avatar | Troca o chapéu. |
| `!acessorio <óculos\|capa\|asas\|nenhum>` | Todos, no próprio avatar | Troca o acessório. |
| `!nick <apelido>` | Todos, no próprio avatar | Nome exibido no rodapé. |
| `!dança` (ou `!danca`) | Todos, no próprio avatar | Dispara uma animação por alguns segundos. |
| `!avatarmod <usuario> <cor>` | Mod/Broadcaster | Força a cor do avatar de outro viewer. |

Decorações automáticas (sem comando): sub ativo ganha borda dourada, mod
ganha a etiqueta "MOD", broadcaster ganha uma coroa (♛), e dar cheer solta um
anel dourado ao redor do avatar por alguns segundos.

## Se o token expirar

O token é o mesmo app do `texuguito-seu-bot-amigo` — rode `python setup.py`
naquele projeto de novo pra gerar um token novo e copie os valores pro `.env`
daqui.

## Testes

`pytest` roda toda a suíte (parsing de comando, geração de avatar, estado
persistido, servidor web). O comportamento de IRC ao vivo e a animação no
navegador só dá pra verificar manualmente: suba o app, abra a URL impressa
no navegador (ou no Browser Source do OBS) e digite os comandos no chat de
teste.
```

- [ ] **Step 2: Copy credentials from the sibling project into a local .env**

Run (adjust paths if your sibling checkout lives elsewhere):

```bash
python -c "
from pathlib import Path
import re

src = Path('../texuguito-seu-bot-amigo/.env').read_text(encoding='utf-8')
wanted = {'CLIENT_ID', 'TOKEN', 'BROADCASTER_ID', 'CHANNEL'}
values = dict(re.findall(r'^(\w+)=(.*)$', src, re.MULTILINE))

lines = [f'{k}={values[k]}' for k in wanted if k in values]
lines.append('DATA_DIR=data')
lines.append('OVERLAY_PORT=8901')

Path('.env').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Escrito .env com', list(values.keys()))
"
```

Expected: prints the copied keys; `.env` now exists locally (already gitignored — verify with `git status` that it does NOT show up as untracked-to-be-added).

- [ ] **Step 3: Run the full test suite one more time**

Run: `pytest -v`
Expected: PASS, every test from every task green.

- [ ] **Step 4: Manual verification (requires live Twitch — do this yourself, not automatable)**

1. Run: `python -m chat_parade.main`
2. Confirm the console prints the `http://localhost:8901/overlay` line and nothing crashes.
3. Open that URL in a normal browser tab first — canvas should render (empty until viewers show up).
4. Add it as a Browser Source in OBS with the same URL.
5. From your Twitch channel chat (or a test account), send `!cor blue`, `!chapeu coroa`, `!dança` and confirm the avatar updates live in the overlay within a few seconds.
6. Stop with Ctrl+C — confirm `data/viewers.json` was written with your test viewer's customization.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Add README with setup, command reference and manual test steps"
```
