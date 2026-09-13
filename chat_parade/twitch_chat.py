from __future__ import annotations

import asyncio

from twitchio.ext import commands

from chat_parade import commands as cmds
from chat_parade import economy_commands as eco
from chat_parade.config import Config
from chat_parade.points import PointsStore
from chat_parade.raffle import Raffle
from chat_parade.soundboard import Soundboard
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


def _is_privileged(ctx: commands.Context) -> bool:
    return ctx.author.is_mod or ctx.author.is_broadcaster


class ChatParadeBot(commands.Bot):
    def __init__(
        self,
        config: Config,
        store: ViewerStore,
        events: "asyncio.Queue[ViewerEvent]",
        points: PointsStore,
        soundboard: Soundboard,
    ):
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
        self._points = points
        self._soundboard = soundboard
        self._raffle = Raffle()
        # Keeps a reference so the pending raffle-end task isn't garbage collected.
        self._raffle_task: asyncio.Task | None = None

    async def event_ready(self) -> None:
        print(f"[texuguito] conectado ao chat de {self.nick}")

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

    async def _reply(self, ctx, text: str | None) -> None:
        if text:
            await ctx.send(text)

    async def _respond(self, ctx, username: str, args: list[str], handler, **kwargs) -> None:
        reply, event = handler(self._store, username, args, **kwargs)
        await self._reply(ctx, reply)
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
        await self._respond(
            ctx,
            ctx.author.name,
            _args(ctx),
            cmds.handle_avatarmod,
            is_privileged=_is_privileged(ctx),
        )

    @commands.command(name="comandos", aliases=["ajuda", "help"])
    async def comandos_cmd(self, ctx: commands.Context) -> None:
        await self._respond(
            ctx,
            ctx.author.name,
            [],
            cmds.handle_comandos,
            is_privileged=_is_privileged(ctx),
            is_broadcaster=ctx.author.is_broadcaster,
        )

    # --- Points, soundboard and raffle ---

    @commands.command(name="ping")
    async def ping_cmd(self, ctx: commands.Context) -> None:
        await self._reply(ctx, eco.handle_ping(ctx.author.name))

    @commands.command(name="pontos", aliases=["pts"])
    async def pontos_cmd(self, ctx: commands.Context) -> None:
        await self._reply(ctx, eco.handle_pontos(self._points, ctx.author.name))

    @commands.command(name="addpoints", aliases=["dar", "give"])
    async def addpoints_cmd(self, ctx: commands.Context) -> None:
        reply = eco.handle_addpoints(self._points, ctx.author.name, _args(ctx), _is_privileged(ctx))
        await self._reply(ctx, reply)

    @commands.command(name="p", aliases=["play"])
    async def play_cmd(self, ctx: commands.Context) -> None:
        reply = await eco.handle_play(self._points, self._soundboard, ctx.author.name, _args(ctx))
        await self._reply(ctx, reply)

    @commands.command(name="tts")
    async def tts_cmd(self, ctx: commands.Context) -> None:
        reply = await eco.handle_tts(self._points, self._soundboard, ctx.author.name, _args(ctx))
        await self._reply(ctx, reply)

    @commands.command(name="audios", aliases=["sons", "sounds"])
    async def audios_cmd(self, ctx: commands.Context) -> None:
        await self._reply(ctx, eco.handle_audios(self._soundboard))

    @commands.command(name="stop")
    async def stop_cmd(self, ctx: commands.Context) -> None:
        await self._reply(ctx, await eco.handle_stop(self._soundboard))

    @commands.command(name="reload")
    async def reload_cmd(self, ctx: commands.Context) -> None:
        await self._reply(ctx, eco.handle_reload(self._soundboard, _is_privileged(ctx)))

    @commands.command(name="status")
    async def status_cmd(self, ctx: commands.Context) -> None:
        await self._reply(ctx, eco.handle_status(self._soundboard))

    @commands.command(name="sorteio")
    async def sorteio_cmd(self, ctx: commands.Context) -> None:
        reply, minutes = eco.handle_sorteio(self._raffle, _args(ctx), ctx.author.is_broadcaster)
        await self._reply(ctx, reply)
        if minutes is not None:
            self._raffle_task = asyncio.create_task(self._finish_raffle_later(ctx, minutes * 60))

    @commands.command(name="join")
    async def join_cmd(self, ctx: commands.Context) -> None:
        eco.handle_join(self._raffle, ctx.author.name)

    async def _finish_raffle_later(self, ctx: commands.Context, delay_seconds: float) -> None:
        await asyncio.sleep(delay_seconds)
        winner, prize = self._raffle.finish(self._points)
        await self._reply(ctx, eco.raffle_result_reply(winner, prize))
