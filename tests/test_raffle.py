from chat_parade.points import PointsStore
from chat_parade.raffle import Raffle


def test_only_one_raffle_at_a_time():
    raffle = Raffle()
    assert raffle.start(100) is True
    assert raffle.start(50) is False
    assert raffle.prize == 100


def test_join_is_ignored_without_an_active_raffle():
    raffle = Raffle()
    assert raffle.join("fulano") is False
    assert raffle.participants == set()


def test_join_counts_each_user_once():
    raffle = Raffle()
    raffle.start(100)
    assert raffle.join("Fulano") is True
    assert raffle.join("fulano") is False
    assert raffle.participants == {"fulano"}


def test_finish_credits_the_winner_and_resets(tmp_path):
    points = PointsStore(tmp_path / "p.json")
    raffle = Raffle(choose=lambda participants: participants[-1])
    raffle.start(100)
    raffle.join("ana")
    raffle.join("bruno")

    winner, prize = raffle.finish(points)

    assert (winner, prize) == ("bruno", 100)
    assert points.get("bruno") == 100
    assert raffle.active is False
    assert raffle.participants == set()


def test_finish_without_participants_has_no_winner(tmp_path):
    raffle = Raffle()
    raffle.start(100)

    assert raffle.finish(PointsStore(tmp_path / "p.json")) == (None, 100)
    assert raffle.active is False
