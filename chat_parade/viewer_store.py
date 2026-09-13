from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DANCE_DURATION_SECONDS = 4.0
CHEER_DURATION_SECONDS = 4.0

DEFAULT_COLOR_PALETTE = [
    "#e74c3c", "#3498db", "#2ecc71", "#f1c40f",
    "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_int(username: str) -> int:
    digest = hashlib.sha256(username.lower().encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def default_color_for(username: str) -> str:
    rng = random.Random(_seed_int(username) + 2)
    return rng.choice(DEFAULT_COLOR_PALETTE)


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
        """Read viewers.json, degrading to an empty store if it is unreadable.

        Hand-editing this file is the only admin interface the design gives the
        streamer, and ViewerStore is built at the very top of main(), so a typo'd
        edit must not brick startup mid-stream. The bad file is moved aside
        rather than discarded so it can still be inspected or repaired.
        """
        if not self._path.exists():
            self._viewers = {}
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._viewers = {name: Viewer(**data) for name, data in raw.items()}
        # ValueError: not valid JSON. TypeError: an entry with wrong/missing
        # fields. AttributeError: valid JSON whose top level is not an object
        # (a list or string has no .items()).
        except (ValueError, TypeError, AttributeError) as exc:
            print(f"[chat-parade] {self._path} corrompido ou inválido ({exc}); iniciando vazio")
            corrupt_path = self._path.with_suffix(self._path.suffix + ".corrupt")
            self._path.replace(corrupt_path)
            self._viewers = {}

    def save(self) -> None:
        """Write viewers.json atomically.

        A plain write_text truncates first, so a crash mid-write would leave a
        half-written file that load() then has to quarantine. Writing to a temp
        file and renaming means readers only ever see a complete file.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        raw = {name: asdict(viewer) for name, viewer in self._viewers.items()}
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self._path)

    def _create(self, username: str) -> bool:
        """Add a viewer if it is missing. Returns whether anything was created.

        Expects an already-lowercased username, and deliberately does not save:
        callers decide when to hit the disk, so a batch of creations can share a
        single write.
        """
        if username in self._viewers:
            return False
        self._viewers[username] = Viewer(cor=default_color_for(username))
        self._status[username] = ViewerStatus()
        return True

    def get_or_create(self, username: str) -> Viewer:
        username = username.lower()
        if self._create(username):
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

        # One write for the whole poll cycle instead of one per new chatter:
        # get_or_create saves on every creation, so N joiners meant N truncate-
        # and-rewrite passes over the same file.
        created_any = False
        for username in joined:
            created_any |= self._create(username)
            self.status_for(username).present = True

        for username in left:
            self.status_for(username).present = False

        if created_any:
            self.save()

        return joined, left
