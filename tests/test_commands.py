from chat_parade.commands import (
    handle_acessorio,
    handle_avatarmod,
    handle_chapeu,
    handle_cor,
    handle_danca,
    handle_nick,
    handle_resetcor,
    parse_command,
    validate_accessory,
    validate_color,
    validate_hat,
    validate_nick,
)
from chat_parade.viewer_store import ViewerStore


def test_parse_command_extracts_name_and_args():
    parsed = parse_command("!cor azul escuro")
    assert parsed.name == "cor"
    assert parsed.args == ["azul", "escuro"]


def test_parse_command_returns_none_for_non_commands():
    assert parse_command("oi gente") is None


def test_parse_command_returns_none_for_bare_prefix():
    assert parse_command("!") is None


def test_validate_color_accepts_hex():
    assert validate_color("#FF8800") == "#ff8800"


def test_validate_color_accepts_css_name():
    assert validate_color("red") == "#ff0000"


def test_validate_color_rejects_garbage():
    assert validate_color("banana123") is None


def test_validate_color_accepts_portuguese_name():
    assert validate_color("azul") == "#0000ff"


def test_validate_color_portuguese_matches_equivalent_css_name():
    # "verde" must equal CSS "green" (#008000), not "lime" (#00ff00) -
    # otherwise the same color word means different things in each language.
    assert validate_color("verde") == validate_color("green")


def test_validate_color_accepts_portuguese_name_with_hyphen_or_space():
    assert validate_color("azul-claro") == validate_color("azul claro")


def test_validate_color_portuguese_name_is_case_insensitive():
    assert validate_color("AZUL") == "#0000ff"


def test_validate_hat_accepts_known_values():
    assert validate_hat("boné") == (True, "boné")
    assert validate_hat("nenhum") == (True, None)


def test_validate_hat_rejects_unknown():
    assert validate_hat("sombrinha") == (False, None)


def test_validate_hat_accepts_new_curated_hats():
    for name in (
        "tricornio",
        "bicorne",
        "cartola",
        "tiara",
        "coco",
        "natalino",
        "mago",
        "viking",
        "elmo",
        "legionario",
        "bandana",
        "capuz",
        "faixa",
    ):
        assert validate_hat(name) == (True, name)


def test_validate_accessory_accepts_known_values():
    assert validate_accessory("capa") == (True, "capa")


def test_validate_accessory_accepts_new_curated_accessories():
    for name in (
        "colar",
        "cachecol",
        "laco",
        "tapaolho",
        "oculosescuros",
        "monoculo",
        "asasmorcego",
        "asasborboleta",
        "asaslibelula",
    ):
        assert validate_accessory(name) == (True, name)


def test_validate_nick_strips_forbidden_chars_and_truncates():
    assert validate_nick("Rei!!! do Chat 999999999999") == "Rei do Chat 9999"


def test_validate_nick_keeps_accented_letters():
    assert validate_nick("João") == "João"


def test_validate_nick_returns_none_for_empty_result():
    assert validate_nick("!!!@@@") is None


def test_validate_nick_strips_embedded_control_whitespace():
    assert validate_nick("Rei\ndo\tChat") == "ReidoChat"


def test_handle_cor_updates_store_on_valid_color(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_cor(store, "fulano", ["#123456"])
    assert reply is None
    assert event.type == "updated"
    assert event.username == "fulano"
    assert store.get_or_create("fulano").cor == "#123456"


def test_handle_cor_replies_error_on_invalid_color(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_cor(store, "fulano", ["naoexiste123"])
    assert reply is not None
    assert event is None


def test_handle_cor_replies_usage_when_no_args(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_cor(store, "fulano", [])
    assert reply is not None
    assert event is None


def test_handle_resetcor_reverts_to_default(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    default = store.get_or_create("fulano").cor
    store.set_color("fulano", "#000000")

    reply, event = handle_resetcor(store, "fulano", [])

    assert reply is None
    assert event.type == "updated"
    assert store.get_or_create("fulano").cor == default


def test_handle_chapeu_sets_value(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_chapeu(store, "fulano", ["coroa"])
    assert reply is None
    assert store.get_or_create("fulano").chapeu == "coroa"


def test_handle_acessorio_rejects_unknown(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_acessorio(store, "fulano", ["jetpack"])
    assert reply is not None
    assert event is None


def test_handle_nick_sets_value(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_nick(store, "fulano", ["Rei", "do", "Chat"])
    assert reply is None
    assert store.get_or_create("fulano").nick == "Rei do Chat"


def test_handle_danca_triggers_dance(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_danca(store, "fulano", [])
    assert reply is None
    assert event.type == "updated"
    assert store.status_for("fulano").dancing_until > 0


def test_handle_avatarmod_ignored_when_not_privileged(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_avatarmod(
        store, "fulano", ["outrapessoa", "red"], is_privileged=False
    )
    assert reply is None
    assert event is None


def test_handle_avatarmod_changes_target_when_privileged(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    reply, event = handle_avatarmod(
        store, "mod1", ["outrapessoa", "red"], is_privileged=True
    )
    assert event.username == "outrapessoa"
    assert store.get_or_create("outrapessoa").cor == "#ff0000"
