from chat_parade.soundboard import Soundboard, TtsCache, scan_audio_dir


class FakeOverlay:
    def __init__(self, connected: bool = True):
        self.has_connections = connected
        self.sent: list[dict] = []

    async def broadcast(self, message: dict) -> None:
        self.sent.append(message)


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"fake audio")


def test_scan_reads_cost_from_folder_and_name_from_file(tmp_path):
    _touch(tmp_path / "20" / "Oof.mp3")
    _touch(tmp_path / "500" / "loça.ogg")

    clips = scan_audio_dir(tmp_path)

    assert clips["oof"].cost == 20
    assert clips["oof"].url == "/audios/20/Oof.mp3"
    assert clips["loça"].cost == 500
    # Non-ASCII file names must be URL-encoded for the overlay to fetch them.
    assert clips["loça"].url == "/audios/500/lo%C3%A7a.ogg"


def test_scan_ignores_non_numeric_folders_and_non_audio_files(tmp_path):
    _touch(tmp_path / "extras" / "bonus.mp3")
    _touch(tmp_path / "20" / "leia-me.txt")

    assert scan_audio_dir(tmp_path) == {}


def test_scan_of_missing_folder_is_empty(tmp_path):
    assert scan_audio_dir(tmp_path / "nao-existe") == {}


def test_tts_cache_evicts_oldest_clips():
    cache = TtsCache(max_size=2)
    first = cache.add(b"1")
    second = cache.add(b"2")
    third = cache.add(b"3")

    assert cache.get(first) is None
    assert cache.get(second) == b"2"
    assert cache.get(third) == b"3"


async def test_play_and_stop_are_sent_to_the_overlay(tmp_path):
    overlay = FakeOverlay()
    soundboard = Soundboard(tmp_path, TtsCache(), overlay, volume=0.5)

    await soundboard.play("/audios/20/oof.mp3")
    await soundboard.stop()

    assert overlay.sent == [
        {"type": "audio", "url": "/audios/20/oof.mp3", "volume": 0.5},
        {"type": "audio_stop"},
    ]


async def test_make_tts_stores_the_clip_and_returns_its_url(tmp_path):
    cache = TtsCache()
    soundboard = Soundboard(tmp_path, cache, FakeOverlay(), synthesize=lambda text: text.encode())

    url = await soundboard.make_tts("olá")

    assert url.startswith("/tts/")
    assert cache.get(url.removeprefix("/tts/")) == "olá".encode()


def test_cooldown_counts_down_from_the_last_clip(tmp_path):
    now = [1000.0]
    soundboard = Soundboard(tmp_path, TtsCache(), FakeOverlay(), clock=lambda: now[0])

    assert soundboard.cooldown_remaining(60) == 0.0
    soundboard.mark_clip_played()
    now[0] += 45
    assert soundboard.cooldown_remaining(60) == 15.0
    now[0] += 15
    assert soundboard.cooldown_remaining(60) == 0.0


def test_reload_picks_up_new_clips(tmp_path):
    soundboard = Soundboard(tmp_path, TtsCache(), FakeOverlay())
    assert soundboard.clips == {}

    _touch(tmp_path / "100" / "novo.wav")

    assert soundboard.reload() == 1
    assert "novo" in soundboard.clips
