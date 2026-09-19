from __future__ import annotations

import random
from typing import Callable

from texuguito.points import PointsStore


class Raffle:
    """One points raffle at a time: the broadcaster opens it, viewers !join,
    and when it closes a random participant wins the prize."""

    def __init__(self, choose: Callable[[list[str]], str] = random.choice):
        self._choose = choose
        self.active = False
        self.prize = 0
        self.participants: set[str] = set()

    def start(self, prize: int) -> bool:
        if self.active:
            return False
        self.active = True
        self.prize = prize
        self.participants = set()
        return True

    def join(self, username: str) -> bool:
        """Returns whether the user was newly added."""
        username = username.lower()
        if not self.active or username in self.participants:
            return False
        self.participants.add(username)
        return True

    def finish(self, points: PointsStore) -> tuple[str | None, int]:
        """Closes the raffle and credits the winner. Returns (winner, prize);
        winner is None when nobody joined."""
        prize = self.prize
        participants = sorted(self.participants)
        self.active = False
        self.prize = 0
        self.participants = set()
        if not participants:
            return None, prize
        winner = self._choose(participants)
        points.add(winner, prize)
        return winner, prize
