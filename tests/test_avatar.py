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
