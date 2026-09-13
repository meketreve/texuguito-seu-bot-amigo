"""Points, soundboard and raffle commands (ported from texuguito-seu-bot-amigo).

Each handler takes its dependencies explicitly and returns the chat reply (or
None for no reply), so they can be tested without a Twitch connection.
"""
from __future__ import annotations

from chat_parade.points import PointsStore
from chat_parade.raffle import Raffle
from chat_parade.soundboard import Soundboard

CLIP_COOLDOWN_SECONDS = 60
TTS_COST = 200
# Twitch rejects chat messages over 500 characters.
MAX_REPLY_LENGTH = 450


def _truncate(text: str) -> str:
    if len(text) <= MAX_REPLY_LENGTH:
        return text
    return text[: MAX_REPLY_LENGTH - 3] + "..."


def handle_ping(username: str) -> str:
    return f"🏓 Pong, {username}!"


def handle_pontos(points: PointsStore, username: str) -> str:
    return f"🪙 {username}, você tem {points.get(username)} pontos."


def handle_addpoints(
    points: PointsStore, username: str, args: list[str], is_privileged: bool
) -> str | None:
    if not is_privileged:
        return None
    if len(args) < 2:
        return "❌ Use: !addpoints <@usuario> <quantidade>"
    target = args[0].lstrip("@").lower()
    try:
        amount = int(args[1])
    except ValueError:
        return "❌ Use: !addpoints <@usuario> <quantidade>"
    points.add(target, amount)
    return f"✅ {amount} pontos adicionados para {target}! Saldo: {points.get(target)} pts."


def _no_overlay_reply() -> str:
    return "🔇 O overlay não está aberto, então não tem onde tocar o áudio. Nenhum ponto foi cobrado."


async def handle_play(
    points: PointsStore, soundboard: Soundboard, username: str, args: list[str]
) -> str:
    if not args:
        return "❌ Use: !p <nome>"
    remaining = soundboard.cooldown_remaining(CLIP_COOLDOWN_SECONDS)
    if remaining > 0:
        return f"⏳ Cooldown ativo! Aguarde mais {int(remaining) + 1} segundos."
    name = " ".join(args).lower()
    clip = soundboard.clips.get(name)
    if clip is None:
        return f"❌ Áudio '{name}' não encontrado."
    if not soundboard.has_listeners:
        return _no_overlay_reply()
    if not points.spend(username, clip.cost):
        return f"❌ Pontos insuficientes! '{clip.name}' custa {clip.cost} pts."
    soundboard.mark_clip_played()
    await soundboard.play(clip.url)
    return f"🔊 Tocando: {clip.name}. Saldo: {points.get(username)} pts."


async def handle_tts(
    points: PointsStore, soundboard: Soundboard, username: str, args: list[str]
) -> str:
    if not args:
        return "❌ Use: !tts <mensagem>"
    if not soundboard.has_listeners:
        return _no_overlay_reply()
    if not points.spend(username, TTS_COST):
        return f"❌ Pontos insuficientes ({TTS_COST} pts necessários)."
    try:
        url = await soundboard.make_tts(f"{username} enviou a mensagem: {' '.join(args)}")
    except Exception as exc:
        print(f"[texuguito] erro no TTS: {exc}")
        points.add(username, TTS_COST)  # refund: nothing was played
        return "❌ Erro ao gerar o TTS. Seus pontos foram devolvidos."
    await soundboard.play(url)
    return f"🎙️ [TTS] {username} enviou uma mensagem! (-{TTS_COST} pts)"


def handle_audios(soundboard: Soundboard) -> str:
    if not soundboard.clips:
        return "🔈 Nenhum áudio encontrado nas pastas."
    by_cost: dict[int, list[str]] = {}
    for clip in soundboard.clips.values():
        by_cost.setdefault(clip.cost, []).append(clip.name)
    parts = [f"[{cost} pts: {', '.join(sorted(names))}]" for cost, names in sorted(by_cost.items())]
    return _truncate("🎵 Sons Disponíveis: " + " | ".join(parts))


async def handle_stop(soundboard: Soundboard) -> str:
    await soundboard.stop()
    return "⏹️ Áudio parado!"


def handle_reload(soundboard: Soundboard, is_privileged: bool) -> str | None:
    if not is_privileged:
        return None
    return f"🔄 Recarregado! {soundboard.reload()} áudios."


def handle_status(soundboard: Soundboard) -> str:
    return (
        f"📊 [STATUS] Texuguito está online! 🎵 {len(soundboard.clips)} áudios carregados. "
        "🪙 Sistema de pontos ativo."
    )


def handle_sorteio(
    raffle: Raffle, args: list[str], is_broadcaster: bool
) -> tuple[str | None, int | None]:
    """Returns (reply, minutes). `minutes` is set only when a raffle actually
    started, so the caller knows to schedule its end."""
    if not is_broadcaster:
        return None, None
    if raffle.active:
        return "❌ Já existe um sorteio em andamento!", None
    try:
        prize, minutes = int(args[0]), int(args[1])
    except (IndexError, ValueError):
        prize = minutes = 0
    if prize <= 0 or minutes <= 0:
        return "❌ Use: !sorteio <pontos> <minutos>", None
    raffle.start(prize)
    return (
        f"🎉 [SORTEIO] Um sorteio de {prize} pontos começou! Digite !join para participar. "
        f"Tempo: {minutes} min.",
        minutes,
    )


def handle_join(raffle: Raffle, username: str) -> None:
    # Silent on purpose: a reply per participant would flood the chat.
    raffle.join(username)


def raffle_result_reply(winner: str | None, prize: int) -> str:
    if winner is None:
        return "⚠️ O sorteio terminou, mas não houve participantes."
    return f"🎊 PARABÉNS @{winner}! Você ganhou o sorteio de {prize} pontos! 🥳"
