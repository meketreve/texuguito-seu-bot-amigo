from __future__ import annotations

import asyncio

from twitchio.ext import commands

from chat_parade import commands as cmds
from chat_parade.config import Config
from chat_parade.viewer_store import ViewerEvent, ViewerStore


def _args(ctx: commands.Context) -> list[str]:
    """Command arguments as already parsed by twitchio.

    ``ctx.view.words`` is built by twitchio's own ``StringParser`` *after*
    ``Bot.get_context`` strips the ``@username`` prefix that Twitch prepends to
    "Reply" messages, and after the command name itself is popped out. Splitting
    ``ctx.message.content`` by hand instead would shift every argument by one for
    any reply-style message.
    """
    return list(ctx.view.words.values())


class ChatParadeBot(commands.Bot):
    def __init__(self, config: Config, store: ViewerStore, events: "asyncio.Queue[ViewerEvent]"):
        super().__init__(
            token=f"oauth:{config.token}",
            prefix="!",
            initial_channels=[config.channel],
        )
        self._store = store
        # NOT self._events: twitchio's Client.__init__ already uses that name for
        # its own event-listener registry (twitchio/client.py:99), and
        # Client.run_event does `if name in self._events`. Assigning our Queue
        # there made every run_event call raise TypeError - which killed command
        # dispatch entirely, since Bot.invoke fires run_event("command_invoke")
        # before running any command body.
        self._viewer_events = events

    async def event_ready(self) -> None:
        print(f"[chat-parade] conectado ao chat de {self.nick}")

    async def event_message(self, message) -> None:
        if message.echo or not message.author:
            return

        self._store.mark_status_from_message(
            message.author.name,
            is_mod=message.author.is_mod,
            is_sub=message.author.is_subscriber,
            is_broadcaster=message.author.is_broadcaster,
        )

        tags = message.tags or {}
        bits = tags.get("bits")
        if bits and int(bits) > 0:
            self._store.trigger_cheer(message.author.name)

        await self._viewer_events.put(
            ViewerEvent(type="updated", username=message.author.name.lower())
        )

        await self.handle_commands(message)

    async def _respond(self, ctx, username: str, args: list[str], handler, **kwargs) -> None:
        reply, event = handler(self._store, username, args, **kwargs)
        if reply:
            await ctx.send(reply)
        if event:
            await self._viewer_events.put(event)

    @commands.command(name="cor")
    async def cor_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, _args(ctx), cmds.handle_cor)

    @commands.command(name="resetcor")
    async def resetcor_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, [], cmds.handle_resetcor)

    @commands.command(name="chapeu")
    async def chapeu_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, _args(ctx), cmds.handle_chapeu)

    @commands.command(name="acessorio")
    async def acessorio_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, _args(ctx), cmds.handle_acessorio)

    @commands.command(name="nick")
    async def nick_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, _args(ctx), cmds.handle_nick)

    @commands.command(name="dança", aliases=["danca"])
    async def danca_cmd(self, ctx: commands.Context) -> None:
        await self._respond(ctx, ctx.author.name, [], cmds.handle_danca)

    @commands.command(name="avatarmod")
    async def avatarmod_cmd(self, ctx: commands.Context) -> None:
        is_privileged = ctx.author.is_mod or ctx.author.is_broadcaster
        await self._respond(
            ctx,
            ctx.author.name,
            _args(ctx),
            cmds.handle_avatarmod,
            is_privileged=is_privileged,
        )

    @commands.command(name="comandos", aliases=["ajuda", "help"])
    async def comandos_cmd(self, ctx: commands.Context) -> None:
        is_privileged = ctx.author.is_mod or ctx.author.is_broadcaster
        await self._respond(
            ctx,
            ctx.author.name,
            [],
            cmds.handle_comandos,
            is_privileged=is_privileged,
        )
