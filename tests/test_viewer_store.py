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
