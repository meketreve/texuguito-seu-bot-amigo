import json

import pytest

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


@pytest.mark.parametrize(
    "bad_content",
    [
        '{"fulano": {"cor": "#ff0000",',  # truncated / unparseable JSON
        '{"fulano": {"cor": "#ff0000", "naoexiste": 1}}',  # unknown field
        '["fulano"]',  # valid JSON, wrong top-level shape
    ],
)
def test_corrupt_file_does_not_brick_startup(tmp_path, bad_content):
    """Regression test: hand-editing viewers.json is the only admin interface in
    the design, and ViewerStore is constructed at the top of main(), so a typo'd
    edit used to crash the whole app with a raw traceback - possibly mid-stream."""
    path = tmp_path / "viewers.json"
    path.write_text(bad_content, encoding="utf-8")

    store = ViewerStore(path)  # must not raise

    assert store.usernames() == []
    corrupt = tmp_path / "viewers.json.corrupt"
    assert corrupt.read_text(encoding="utf-8") == bad_content
    assert not path.exists()  # moved aside, not copied


def test_store_recovers_and_keeps_working_after_a_corrupt_file(tmp_path):
    path = tmp_path / "viewers.json"
    path.write_text("nao é json", encoding="utf-8")

    store = ViewerStore(path)
    store.set_color("fulano", "#ff8800")

    assert json.loads(path.read_text(encoding="utf-8"))["fulano"]["cor"] == "#ff8800"
    assert ViewerStore(path).get_or_create("fulano").cor == "#ff8800"


def test_save_leaves_no_temp_file_behind(tmp_path):
    """save() writes to a temp file and renames it so a crash mid-write cannot
    leave a half-written viewers.json. The rename must always consume the temp."""
    path = tmp_path / "viewers.json"
    store = ViewerStore(path)
    store.set_color("fulano", "#ff8800")
    store.set_nick("fulano", "Fulano")

    assert path.exists()
    assert list(tmp_path.glob("*.tmp")) == []


def test_sync_present_chatters_persists_all_joiners_in_one_write(tmp_path):
    path = tmp_path / "viewers.json"
    store = ViewerStore(path)

    writes = []
    original_save = store.save
    store.save = lambda: (writes.append(1), original_save())[1]

    joined, _ = store.sync_present_chatters({"ana", "bruno", "carla"})

    assert joined == {"ana", "bruno", "carla"}
    assert len(writes) == 1, "three new joiners must cost one disk write, not three"

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert set(raw) == {"ana", "bruno", "carla"}
    assert all(store.status_for(name).present for name in ("ana", "bruno", "carla"))
    assert list(tmp_path.glob("*.tmp")) == []


def test_sync_present_chatters_does_not_write_when_nothing_is_new(tmp_path):
    store = ViewerStore(tmp_path / "viewers.json")
    store.sync_present_chatters({"ana"})

    writes = []
    original_save = store.save
    store.save = lambda: (writes.append(1), original_save())[1]

    store.sync_present_chatters({"ana"})

    assert writes == []


def test_get_or_create_still_saves_immediately_on_its_own(tmp_path):
    """The batched path must not change get_or_create's behaviour: a chat
    command creating a viewer still has to persist it right away."""
    path = tmp_path / "viewers.json"
    store = ViewerStore(path)

    store.get_or_create("fulano")

    assert "fulano" in json.loads(path.read_text(encoding="utf-8"))
