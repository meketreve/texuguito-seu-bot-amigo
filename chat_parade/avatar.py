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
