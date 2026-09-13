from chat_parade import economy_commands as eco
from chat_parade.points import PointsStore
from chat_parade.raffle import Raffle
from chat_parade.soundboard import Soundboard, TtsCache


class FakeOverlay:
    def __init__(self, connected: bool = True):
        self.has_connections = connected
        self.sent: list[dict] = []

    async def broadcast(self, message: dict) -> None:
        self.sent.append(message)


def _setup(tmp_path, *, connected=True, synthesize=lambda text: b"mp3", clips=("20/oof.mp3",)):
    for clip in clips:
        path = tmp_path / "audios" / clip
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")
    overlay = FakeOverlay(connected)
    soundboard = Soundboard(tmp_path / "audios", TtsCache(), overlay, synthesize=synthesize)
    points = PointsStore(tmp_path / "p.json")
    return points, soundboard, overlay


# --- !pontos / !addpoints ---

def test_pontos_shows_balance(tmp_path):
    points, _, _ = _setup(tmp_path)
    points.add("fulano", 42)
    assert "42 pontos" in eco.handle_pontos(points, "Fulano")


def test_addpoints_is_silent_for_regular_viewers(tmp_path):
    points, _, _ = _setup(tmp_path)
    assert eco.handle_addpoints(points, "fulano", ["@fulano", "999"], is_privileged=False) is None
    assert points.get("fulano") == 0


def test_addpoints_strips_at_sign_and_credits_target(tmp_path):
    points, _, _ = _setup(tmp_path)
    reply = eco.handle_addpoints(points, "mod", ["@Beltrano", "50"], is_privileged=True)
    assert points.get("beltrano") == 50
    assert "50 pontos" in reply


def test_addpoints_rejects_non_numeric_amount(tmp_path):
    points, _, _ = _setup(tmp_path)
    reply = eco.handle_addpoints(points, "mod", ["beltrano", "muito"], is_privileged=True)
    assert reply.startswith("❌ Use")
    assert points.get("beltrano") == 0


# --- !p ---

async def test_play_charges_points_and_sends_clip_to_overlay(tmp_path):
    points, soundboard, overlay = _setup(tmp_path)
    points.add("fulano", 30)

    reply = await eco.handle_play(points, soundboard, "fulano", ["OOF"])

    assert points.get("fulano") == 10
    assert overlay.sent == [{"type": "audio", "url": "/audios/20/oof.mp3", "volume": 1.0}]
    assert "Tocando: oof" in reply


async def test_play_does_not_charge_when_overlay_is_closed(tmp_path):
    points, soundboard, overlay = _setup(tmp_path, connected=False)
    points.add("fulano", 30)

    reply = await eco.handle_play(points, soundboard, "fulano", ["oof"])

    assert points.get("fulano") == 30
    assert overlay.sent == []
    assert "overlay não está aberto" in reply


async def test_play_refuses_when_points_are_insufficient(tmp_path):
    points, soundboard, overlay = _setup(tmp_path)
    points.add("fulano", 5)

    reply = await eco.handle_play(points, soundboard, "fulano", ["oof"])

    assert points.get("fulano") == 5
    assert overlay.sent == []
    assert "insuficientes" in reply


async def test_play_unknown_clip(tmp_path):
    points, soundboard, _ = _setup(tmp_path)
    reply = await eco.handle_play(points, soundboard, "fulano", ["naoexiste"])
    assert "não encontrado" in reply


async def test_play_cooldown_blocks_the_next_clip_without_charging(tmp_path):
    points, soundboard, overlay = _setup(tmp_path)
    points.add("fulano", 100)

    await eco.handle_play(points, soundboard, "fulano", ["oof"])
    reply = await eco.handle_play(points, soundboard, "fulano", ["oof"])

    assert "Cooldown" in reply
    assert points.get("fulano") == 80
    assert len(overlay.sent) == 1


async def test_play_cooldown_is_not_started_by_a_failed_attempt(tmp_path):
    points, soundboard, _ = _setup(tmp_path)

    await eco.handle_play(points, soundboard, "pobre", ["oof"])  # can't afford it

    assert soundboard.cooldown_remaining(eco.CLIP_COOLDOWN_SECONDS) == 0.0


# --- !tts ---

async def test_tts_charges_and_plays_generated_clip(tmp_path):
    spoken = []
    points, soundboard, overlay = _setup(tmp_path, synthesize=lambda text: spoken.append(text) or b"mp3")
    points.add("fulano", 250)

    reply = await eco.handle_tts(points, soundboard, "fulano", ["oi", "chat"])

    assert points.get("fulano") == 50
    assert spoken == ["fulano enviou a mensagem: oi chat"]
    assert overlay.sent[0]["type"] == "audio"
    assert overlay.sent[0]["url"].startswith("/tts/")
    assert "TTS" in reply


async def test_tts_refunds_when_synthesis_fails(tmp_path):
    def broken(text):
        raise OSError("sem internet")

    points, soundboard, overlay = _setup(tmp_path, synthesize=broken)
    points.add("fulano", 250)

    reply = await eco.handle_tts(points, soundboard, "fulano", ["oi"])

    assert points.get("fulano") == 250
    assert overlay.sent == []
    assert "devolvidos" in reply


async def test_tts_does_not_charge_when_overlay_is_closed(tmp_path):
    points, soundboard, _ = _setup(tmp_path, connected=False)
    points.add("fulano", 250)

    await eco.handle_tts(points, soundboard, "fulano", ["oi"])

    assert points.get("fulano") == 250


# --- !audios / !stop / !reload / !status ---

def test_audios_groups_clips_by_cost(tmp_path):
    _, soundboard, _ = _setup(tmp_path, clips=("20/oof.mp3", "20/bonk.mp3", "100/uau.mp3"))
    reply = eco.handle_audios(soundboard)
    assert "[20 pts: bonk, oof] | [100 pts: uau]" in reply


def test_audios_reply_fits_in_a_chat_message(tmp_path):
    clips = tuple(f"20/som_numero_{i}.mp3" for i in range(100))
    _, soundboard, _ = _setup(tmp_path, clips=clips)
    assert len(eco.handle_audios(soundboard)) <= eco.MAX_REPLY_LENGTH


async def test_stop_tells_the_overlay_to_stop(tmp_path):
    _, soundboard, overlay = _setup(tmp_path)
    await eco.handle_stop(soundboard)
    assert overlay.sent == [{"type": "audio_stop"}]


def test_reload_is_mod_only(tmp_path):
    _, soundboard, _ = _setup(tmp_path)
    assert eco.handle_reload(soundboard, is_privileged=False) is None
    assert "1 áudios" in eco.handle_reload(soundboard, is_privileged=True)


# --- !sorteio / !join ---

def test_sorteio_is_broadcaster_only():
    raffle = Raffle()
    assert eco.handle_sorteio(raffle, ["100", "2"], is_broadcaster=False) == (None, None)
    assert raffle.active is False


def test_sorteio_starts_and_returns_duration():
    raffle = Raffle()
    reply, minutes = eco.handle_sorteio(raffle, ["100", "2"], is_broadcaster=True)
    assert minutes == 2
    assert raffle.active and raffle.prize == 100
    assert "!join" in reply


def test_sorteio_rejects_bad_arguments():
    raffle = Raffle()
    for args in ([], ["100"], ["0", "2"], ["cem", "2"]):
        reply, minutes = eco.handle_sorteio(raffle, args, is_broadcaster=True)
        assert minutes is None
        assert reply.startswith("❌ Use")
    assert raffle.active is False


def test_sorteio_refuses_a_second_raffle():
    raffle = Raffle()
    eco.handle_sorteio(raffle, ["100", "2"], is_broadcaster=True)
    reply, minutes = eco.handle_sorteio(raffle, ["50", "1"], is_broadcaster=True)
    assert minutes is None
    assert "andamento" in reply


def test_raffle_result_reply():
    assert "@fulano" in eco.raffle_result_reply("fulano", 100)
    assert "não houve participantes" in eco.raffle_result_reply(None, 100)
