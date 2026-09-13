from __future__ import annotations

import asyncio
import json
from pathlib import Path

from chat_parade.viewer_store import ViewerStore

POINTS_PER_TICK = 1
POINTS_TICK_SECONDS = 60


class PointsStore:
    """Channel points, persisted as ``{"username": points}`` in points.json.

    Same file format as texuguito-seu-bot-amigo's points.json, so an existing
    balance file can be copied over as-is.
    """

    def __init__(self, path: Path):
        self._path = path
        self._points: dict[str, int] = {}
        self.load()

    def load(self) -> None:
        """Read points.json, degrading to an empty store if it is unreadable.

        Like viewers.json, a bad file is moved aside instead of discarded so a
        hand-edit typo can't brick startup or silently wipe everyone's balance.
        """
        if not self._path.exists():
            self._points = {}
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._points = {name.lower(): int(value) for name, value in raw.items()}
        except (ValueError, TypeError, AttributeError) as exc:
            print(f"[chat-parade] {self._path} corrompido ou inválido ({exc}); iniciando vazio")
            self._path.replace(self._path.with_suffix(self._path.suffix + ".corrupt"))
            self._points = {}

    def save(self) -> None:
        """Write points.json atomically (temp file + rename), like ViewerStore.save."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(self._points, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self._path)

    def get(self, username: str) -> int:
        return self._points.get(username.lower(), 0)

    def add(self, username: str, amount: int) -> None:
        self.add_many({username}, amount)

    def add_many(self, usernames: set[str], amount: int) -> None:
        """Credit every user in one write instead of one write per user."""
        if not usernames:
            return
        for username in usernames:
            username = username.lower()
            self._points[username] = self._points.get(username, 0) + amount
        self.save()

    def spend(self, username: str, amount: int) -> bool:
        """Debit `amount` if the user can afford it. Returns whether it was debited."""
        username = username.lower()
        current = self.get(username)
        if current < amount:
            return False
        self._points[username] = current - amount
        self.save()
        return True


def award_tick(previous: set[str], current: set[str], points: PointsStore) -> set[str]:
    """Credits viewers present on both this tick and the previous one.

    Requiring two consecutive ticks means a viewer earns a point only for a
    full minute actually spent in chat, not for being caught by one check.
    Returns who was credited.
    """
    active = previous & current
    points.add_many(active, POINTS_PER_TICK)
    return active


async def run_points_loop(store: ViewerStore, points: PointsStore) -> None:
    previous = store.present_usernames()
    while True:
        await asyncio.sleep(POINTS_TICK_SECONDS)
        current = store.present_usernames()
        award_tick(previous, current, points)
        previous = current
