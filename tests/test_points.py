import json

from chat_parade.points import POINTS_PER_TICK, PointsStore, award_tick


def test_new_user_starts_at_zero(tmp_path):
    points = PointsStore(tmp_path / "p.json")
    assert points.get("fulano") == 0


def test_add_and_spend_are_case_insensitive_and_persisted(tmp_path):
    path = tmp_path / "p.json"
    points = PointsStore(path)
    points.add("Fulano", 50)

    assert points.spend("FULANO", 20) is True
    assert PointsStore(path).get("fulano") == 30


def test_spend_refuses_when_balance_is_too_low(tmp_path):
    points = PointsStore(tmp_path / "p.json")
    points.add("fulano", 10)

    assert points.spend("fulano", 11) is False
    assert points.get("fulano") == 10


def test_reads_texuguito_points_file_as_is(tmp_path):
    """The balance file from texuguito-seu-bot-amigo can be copied over unchanged."""
    path = tmp_path / "points.json"
    path.write_text(json.dumps({"meketrevee": 100, "EasyBR9": 40}), encoding="utf-8")

    points = PointsStore(path)

    assert points.get("meketrevee") == 100
    assert points.get("easybr9") == 40


def test_corrupt_file_is_moved_aside_instead_of_crashing(tmp_path):
    path = tmp_path / "p.json"
    path.write_text("{nao é json", encoding="utf-8")

    points = PointsStore(path)

    assert points.get("fulano") == 0
    assert not path.exists()
    assert (tmp_path / "p.json.corrupt").exists()


def test_add_many_writes_once(tmp_path, monkeypatch):
    points = PointsStore(tmp_path / "p.json")
    saves = []
    monkeypatch.setattr(points, "save", lambda: saves.append(1))

    points.add_many({"a", "b", "c"}, 1)

    assert len(saves) == 1


def test_award_tick_only_credits_viewers_present_on_both_ticks(tmp_path):
    points = PointsStore(tmp_path / "p.json")

    credited = award_tick({"ana", "bruno"}, {"bruno", "carla"}, points)

    assert credited == {"bruno"}
    assert points.get("bruno") == POINTS_PER_TICK
    assert points.get("ana") == 0
    assert points.get("carla") == 0
