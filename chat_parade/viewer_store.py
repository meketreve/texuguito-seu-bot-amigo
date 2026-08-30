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
