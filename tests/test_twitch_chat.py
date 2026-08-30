import asyncio

from twitchio import Chatter, Message

from chat_parade.config import Config
from chat_parade.twitch_chat import ChatParadeBot, _args
from chat_parade.viewer_store import ViewerStore


def _config(tmp_path) -> Config:
    return Config(
        client_id="id",
        token="tok",
        broadcaster_id="1",
        channel="meucanal",
        data_dir=tmp_path,
        overlay_port=8901,
    )


def _make_message(content: str, *, reply: bool, name: str = "fulano") -> Message:
    """Build a real twitchio Message the way the IRC parser would.

    Twitch prepends "@username " to the content of a message sent with the
    "Reply" feature and sets the reply-parent-msg-id tag.
    """
    tags = {
        "id": "msg-id",
        "tmi-sent-ts": "0",
        "user-id": "42",
        "badges": "",
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


async def _invoke(bot: ChatParadeBot, command_name: str, ctx) -> None:
    """Call a command's own coroutine directly.

    Deliberately bypasses ``Command.__call__``, which fans out through
    ``Client.run_event`` -- unrelated machinery that is not what these tests are
    exercising. See the fix report for a separate finding about ``run_event``.
    """
    await bot.commands[command_name]._callback(bot, ctx)


async def test_bot_constructs_without_touching_the_network(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()

    bot = ChatParadeBot(_config(tmp_path), store, events)

    assert bot is not None
    assert bot._store is store
    assert bot._events is events


async def test_args_are_not_shifted_for_reply_messages(tmp_path):
    """Regression test: a viewer using Twitch's Reply feature sends
    '@alguem !nick Rei do Chat'. Re-splitting message.content by hand yields
    ['!nick', 'Rei', 'do', 'Chat'] (args shifted by one); twitchio's own parse
    already stripped both the @mention and the command name."""
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    bot = ChatParadeBot(_config(tmp_path), store, events)

    message = _make_message("@alguem !nick Rei do Chat", reply=True)
    ctx = await bot.get_context(message)

    assert ctx.is_valid
    assert _args(ctx) == ["Rei", "do", "Chat"]
    # The old implementation would have produced this instead:
    assert message.content.split()[1:] == ["!nick", "Rei", "do", "Chat"]


async def test_args_still_correct_for_plain_messages(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    bot = ChatParadeBot(_config(tmp_path), store, events)

    ctx = await bot.get_context(_make_message("!nick Rei do Chat", reply=False))

    assert ctx.is_valid
    assert _args(ctx) == ["Rei", "do", "Chat"]


async def test_nick_command_on_reply_message_sets_the_right_nick(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    bot = ChatParadeBot(_config(tmp_path), store, events)

    ctx = await bot.get_context(_make_message("@alguem !nick Rei do Chat", reply=True))
    await _invoke(bot, "nick", ctx)

    assert store.get_or_create("fulano").nick == "Rei do Chat"
    assert events.get_nowait().username == "fulano"


async def test_avatarmod_on_reply_message_targets_the_right_user(tmp_path):
    store = ViewerStore(tmp_path / "v.json")
    events: asyncio.Queue = asyncio.Queue()
    bot = ChatParadeBot(_config(tmp_path), store, events)

    message = _make_message("@alguem !avatarmod beltrano #00ff00", reply=True)
    message.author._mod = 1  # simulate a moderator
    ctx = await bot.get_context(message)
    await _invoke(bot, "avatarmod", ctx)

    assert store.get_or_create("beltrano").cor == "#00ff00"
    assert events.get_nowait().username == "beltrano"
