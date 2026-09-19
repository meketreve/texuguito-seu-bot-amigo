import asyncio

from twitchio import Chatter, Message

from texuguito.config import Config
from texuguito.points import PointsStore
from texuguito.soundboard import Soundboard, TtsCache
from texuguito.twitch_chat import ChatParadeBot, _args
from texuguito.viewer_store import ViewerStore


def _config(tmp_path) -> Config:
    return Config(
        client_id="id",
        client_secret="secret",
        token="tok",
        refresh_token="reftok",
        broadcaster_id="1",
        channel="meucanal",
        data_dir=tmp_path,
        overlay_port=8901,
        env_path=tmp_path / ".env",
    )


class _FakeOverlay:
    def __init__(self, connected: bool = True):
        self.has_connections = connected
        self.sent: list[dict] = []

    async def broadcast(self, message: dict) -> None:
        self.sent.append(message)


def _bot(tmp_path, store, events, overlay=None) -> ChatParadeBot:
    soundboard = Soundboard(tmp_path / "audios", TtsCache(), overlay or _FakeOverlay())
    return ChatParadeBot(_config(tmp_path), store, events, PointsStore(tmp_path / "p.json"), soundboard)


def _capture_replies(bot: ChatParadeBot) -> list[str]:
    replies: list[str] = []

    async def fake_reply(ctx, text):
        if text:
            replies.append(text)

    bot._reply = fake_reply
    return replies


def _make_message(content: str, *, reply: bool, name: str = "fulano", badges: str = "") -> Message:
    """Build a real twitchio Message the way the IRC parser would.

    Twitch prepends "@username " to the content of a message sent with the
    "Reply" feature and sets the reply-parent-msg-id tag.
    """
    tags = {
        "id": "msg-id",
        "tmi-sent-ts": "0",
        "user-id": "42",
        "badges": badges,
        "turbo": "0",
        "subscriber": "0",
        "mod": "0",
        "display-name": name,
        "color": "#ff0000",
    }
    if reply:
        tags["reply-parent-msg-id"] = "parent-msg-id"
    chatter = Chatter(None, name=name, channel=None, tags=tags)
    return Message(content=content, author=chatter, channel=None, tags=tags, raw_data="")


async def _invoke(bot: ChatParadeBot, ctx) -> None:
    """Dispatch a command exactly the way production does.

    ``Bot.handle_commands`` calls ``get_context`` then ``invoke``, and ``invoke``
    fans out through ``Client.run_event`` and ``Command.__call__`` before the
    command body runs -- so this covers the real path, including the event
    registry that the viewer-event Queue used to shadow.
    """
    await bot.invoke(ctx)


async def test_bot_constructs_without_touching_the_network(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    bot = _bot(tmp_path, store, events)

    assert bot is not None
    assert bot._store is store
    assert bot._viewer_events is events


async def test_viewer_queue_does_not_shadow_twitchio_event_registry(tmp_path):
    """Regression test: the viewer-event Queue used to be stored as
    self._events, the same name twitchio's Client uses for its event-listener
    dict. Client.run_event does `if name in self._events`, so every dispatch
    raised TypeError - and Bot.invoke fires run_event("command_invoke") before
    running any command body, so no chat command could ever execute."""
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    bot = _bot(tmp_path, store, events)

    # twitchio's own registry is untouched and still a usable mapping.
    assert isinstance(bot._events, dict)
    assert ("event_message" in bot._events) is False  # must not raise TypeError
    # ...and our queue lives somewhere else.
    assert bot._viewer_events is events
    assert bot._viewer_events is not bot._events


async def test_args_are_not_shifted_for_reply_messages(tmp_path):
    """Regression test: a viewer using Twitch's Reply feature sends
    '@alguem !nick Rei do Chat'. Re-splitting message.content by hand yields
    ['!nick', 'Rei', 'do', 'Chat'] (args shifted by one); twitchio's own parse
    already stripped both the @mention and the command name."""
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    bot = _bot(tmp_path, store, events)

    message = _make_message("@alguem !nick Rei do Chat", reply=True)
    ctx = await bot.get_context(message)

    assert ctx.is_valid
    assert _args(ctx) == ["Rei", "do", "Chat"]
    # The old implementation would have produced this instead:
    assert message.content.split()[1:] == ["!nick", "Rei", "do", "Chat"]


async def test_args_still_correct_for_plain_messages(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    bot = _bot(tmp_path, store, events)

    ctx = await bot.get_context(_make_message("!nick Rei do Chat", reply=False))

    assert ctx.is_valid
    assert _args(ctx) == ["Rei", "do", "Chat"]


async def test_nick_command_on_reply_message_sets_the_right_nick(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    bot = _bot(tmp_path, store, events)

    ctx = await bot.get_context(_make_message("@alguem !nick Rei do Chat", reply=True))
    await _invoke(bot, ctx)

    assert store.get_or_create("fulano").nick == "Rei do Chat"
    assert events.get_nowait().username == "fulano"


async def test_avatarmod_on_reply_message_targets_the_right_user(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    bot = _bot(tmp_path, store, events)

    message = _make_message("@alguem !avatarmod beltrano #00ff00", reply=True)
    message.author._mod = 1  # simulate a moderator
    ctx = await bot.get_context(message)
    await _invoke(bot, ctx)

    assert store.get_or_create("beltrano").cor == "#00ff00"
    assert events.get_nowait().username == "beltrano"


async def test_play_command_goes_through_the_bot_to_the_overlay(tmp_path):
    clip = tmp_path / "audios" / "20" / "oof.mp3"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"x")
    overlay = _FakeOverlay()
    bot = _bot(tmp_path, ViewerStore(tmp_path / "v.json"), asyncio.Queue(), overlay)
    bot._points.add("fulano", 20)
    replies = _capture_replies(bot)

    await _invoke(bot, await bot.get_context(_make_message("!p oof", reply=False)))

    assert overlay.sent == [{"type": "audio", "url": "/audios/20/oof.mp3", "volume": 1.0}]
    assert bot._points.get("fulano") == 0
    assert replies == ["🔊 Tocando: oof. Saldo: 0 pts."]


async def test_pontos_alias_replies_with_balance(tmp_path):
    bot = _bot(tmp_path, ViewerStore(tmp_path / "v.json"), asyncio.Queue())
    bot._points.add("fulano", 7)
    replies = _capture_replies(bot)

    await _invoke(bot, await bot.get_context(_make_message("!pts", reply=False)))

    assert replies == ["🪙 fulano, você tem 7 pontos."]


async def test_sorteio_from_broadcaster_schedules_the_draw(tmp_path):
    bot = _bot(tmp_path, ViewerStore(tmp_path / "v.json"), asyncio.Queue())
    replies = _capture_replies(bot)
    message = _make_message("!sorteio 100 1", reply=False, name="dono", badges="broadcaster/1")

    await _invoke(bot, await bot.get_context(message))
    await _invoke(bot, await bot.get_context(_make_message("!join", reply=False, name="fulano")))

    assert bot._raffle.participants == {"fulano"}
    assert bot._raffle_task is not None and not bot._raffle_task.done()
    bot._raffle_task.cancel()
    assert "!join" in replies[0]
