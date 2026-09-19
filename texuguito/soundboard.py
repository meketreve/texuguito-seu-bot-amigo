from __future__ import annotations

import asyncio
import io
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.parse import quote

AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg")
AUDIO_URL_PREFIX = "/audios"
TTS_URL_PREFIX = "/tts"
TTS_CACHE_SIZE = 20


@dataclass(frozen=True)
class AudioClip:
    name: str
    cost: int
    url: str


def scan_audio_dir(audio_dir: Path) -> dict[str, AudioClip]:
    """Finds clips laid out as ``<audio_dir>/<cost>/<name>.<ext>``.

    The folder name is the price in points; files in folders that aren't a
    number are ignored. Clip names are the lowercased file stem, which is what
    viewers type after ``!p``.
    """
    clips: dict[str, AudioClip] = {}
    if not audio_dir.is_dir():
        return clips
    for folder in sorted(audio_dir.iterdir()):
        if not (folder.is_dir() and folder.name.isdigit()):
            continue
        cost = int(folder.name)
        for file in sorted(folder.iterdir()):
            if file.is_file() and file.suffix.lower() in AUDIO_EXTENSIONS:
                relative = file.relative_to(audio_dir).as_posix()
                clips[file.stem.lower()] = AudioClip(
                    name=file.stem.lower(),
                    cost=cost,
                    url=f"{AUDIO_URL_PREFIX}/{quote(relative)}",
                )
    return clips


class TtsCache:
    """Holds the last few generated TTS clips in memory for the overlay to fetch.

    The overlay fetches a clip right after being told to play it, so only the
    most recent handful ever need to stick around.
    """

    def __init__(self, max_size: int = TTS_CACHE_SIZE):
        self._max_size = max_size
        self._clips: OrderedDict[str, bytes] = OrderedDict()

    def add(self, mp3: bytes) -> str:
        clip_id = uuid.uuid4().hex
        self._clips[clip_id] = mp3
        while len(self._clips) > self._max_size:
            self._clips.popitem(last=False)
        return clip_id

    def get(self, clip_id: str) -> bytes | None:
        return self._clips.get(clip_id)


def synthesize_tts(text: str) -> bytes:
    """Google TTS (pt-BR) as mp3 bytes. Blocking and needs internet."""
    from gtts import gTTS

    buffer = io.BytesIO()
    gTTS(text=text, lang="pt", tld="com.br").write_to_fp(buffer)
    return buffer.getvalue()


class OverlaySink(Protocol):
    @property
    def has_connections(self) -> bool: ...

    async def broadcast(self, message: dict[str, Any]) -> None: ...


class Soundboard:
    """Plays sounds through the overlay page, so OBS captures them with the
    Browser Source instead of the bot needing an audio device of its own."""

    def __init__(
        self,
        audio_dir: Path,
        tts_cache: TtsCache,
        overlay: OverlaySink,
        volume: float = 1.0,
        synthesize: Callable[[str], bytes] = synthesize_tts,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._audio_dir = audio_dir
        self._tts_cache = tts_cache
        self._overlay = overlay
        self._volume = volume
        self._synthesize = synthesize
        self._clock = clock
        self._last_clip_at: float | None = None
        self.clips = scan_audio_dir(audio_dir)

    def reload(self) -> int:
        self.clips = scan_audio_dir(self._audio_dir)
        return len(self.clips)

    @property
    def has_listeners(self) -> bool:
        return self._overlay.has_connections

    def cooldown_remaining(self, cooldown_seconds: float) -> float:
        if self._last_clip_at is None:
            return 0.0
        return max(0.0, cooldown_seconds - (self._clock() - self._last_clip_at))

    def mark_clip_played(self) -> None:
        self._last_clip_at = self._clock()

    async def play(self, url: str) -> None:
        await self._overlay.broadcast({"type": "audio", "url": url, "volume": self._volume})

    async def stop(self) -> None:
        await self._overlay.broadcast({"type": "audio_stop"})

    async def make_tts(self, text: str) -> str:
        """Synthesizes `text` off the event loop and returns the URL to play it from."""
        loop = asyncio.get_running_loop()
        mp3 = await loop.run_in_executor(None, self._synthesize, text)
        return f"{TTS_URL_PREFIX}/{self._tts_cache.add(mp3)}"
