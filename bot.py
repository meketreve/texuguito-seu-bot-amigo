from dotenv import load_dotenv
import os
import asyncio
import json
import requests
import pygame
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from gtts import gTTS
import tempfile
import random


# TwitchIO stable 2.10.0
from twitchio.ext import commands

# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler
from rich.text import Text
from rich import box
import emoji

# Load .env
load_dotenv()
console = Console()

def em(emoji_code: str) -> str:
    return emoji.emojize(emoji_code)

class VisualInterface:
    def __init__(self):
        self.console = console
    
    def show_banner(self):
        banner_text = Text()
        banner_text.append(em(":badger:"), style="bold blue")
        banner_text.append(" Texuguito Bot ", style="bold blue")
        banner_text.append(em(":musical_note:"), style="bold yellow")
        banner_text.append(" v2.10 Estável", style="bold green")
        
        banner = Panel(
            banner_text,
            title="[bold green]Sistema Iniciando[/]",
            border_style="blue",
            box=box.DOUBLE
        )
        self.console.print(banner)
    
    def show_config_table(self, bot_config: dict):
        table = Table(title=f"{em(':gear:')} Configurações", box=box.ROUNDED)
        table.add_column("Item", style="cyan")
        table.add_column("Valor", style="magenta")
        for k, v in bot_config.items():
            table.add_row(str(k), str(v))
        self.console.print(table)

    def log_point_reward(self, count: int):
        text = Text()
        text.append(em(":coin:"), style="yellow")
        text.append(f" {count} usuários receberam pontos!", style="bold yellow")
        self.console.print(Panel(text, border_style="yellow", box=box.SIMPLE))

# PointsManager
class PointsManager:
    def __init__(self, file_path: str = "points.json"):
        self.file_path = Path(file_path)
        self.points = self._load()

    def _load(self) -> dict:
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.points, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar pontos: {e}")

    def get_points(self, user: str) -> int:
        return self.points.get(user.lower(), 0)

    def add_points(self, user: str, amount: int):
        user = user.lower()
        self.points[user] = self.points.get(user, 0) + amount
        self.save()

    def remove_points(self, user: str, amount: int) -> bool:
        user = user.lower()
        current = self.get_points(user)
        if current >= amount:
            self.points[user] = current - amount
            self.save()
            return True
        return False

# Env Variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN = os.getenv("TOKEN", "")
if TOKEN.startswith("oauth:"): TOKEN = TOKEN.replace("oauth:", "")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN", "")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")
CHANNEL = os.getenv("CHANNEL", "meketreve").lower()
POINTS_REWARD = 1
CHECK_INTERVAL = 60
FILES_DIR = os.path.join(os.path.dirname(__file__), "files")

class TokenManager:
    """Gerencia a renovação automática de tokens do Twitch"""
    @staticmethod
    def refresh_token():
        global TOKEN, REFRESH_TOKEN
        
        if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
            logger.error("❌ CLIENT_ID, CLIENT_SECRET ou REFRESH_TOKEN faltando para renovação!")
            return False

        url = "https://id.twitch.tv/oauth2/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        }
        
        try:
            logger.info("🔄 Tentando renovar o token de acesso...")
            response = requests.post(url, data=payload, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                TOKEN = data["access_token"]
                REFRESH_TOKEN = data.get("refresh_token", REFRESH_TOKEN)
                
                # Atualiza o arquivo .env
                TokenManager.update_env(TOKEN, REFRESH_TOKEN)
                logger.info("✅ Token renovado e arquivo .env atualizado com sucesso!")
                return True
            else:
                logger.error(f"❌ Falha ao renovar token: {data.get('message', 'Erro desconhecido')}")
                return False
        except Exception as e:
            logger.error(f"❌ Erro na requisição de refresh: {e}")
            return False

    @staticmethod
    def update_env(new_token, new_refresh):
        """Atualiza fisicamente o arquivo .env com os novos valores"""
        env_path = Path(".env")
        if not env_path.exists(): return
        
        lines = []
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        with open(env_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith("TOKEN="):
                    f.write(f"TOKEN={new_token}\n")
                elif line.startswith("REFRESH_TOKEN="):
                    f.write(f"REFRESH_TOKEN={new_refresh}\n")
                else:
                    f.write(line)

def escanear_audios():
    audios = {}
    if not os.path.exists(FILES_DIR): return audios
    for pasta in os.listdir(FILES_DIR):
        pasta_path = os.path.join(FILES_DIR, pasta)
        if os.path.isdir(pasta_path) and pasta.isdigit():
            custo = int(pasta)
            for arquivo in os.listdir(pasta_path):
                if arquivo.lower().endswith(('.mp3', '.wav', '.ogg')):
                    nome = os.path.splitext(arquivo)[0].lower()
                    audios[nome] = {"path": os.path.join(pasta_path, arquivo), "custo": custo}
    return audios

class TexuguitoBot(commands.Bot):
    def __init__(self):
        # Em 2.10.0, o token precisa do prefixo oauth:
        # nick é opcional, ele pega do token se possível
        super().__init__(
            token=f"oauth:{TOKEN}",
            prefix='!',
            initial_channels=[CHANNEL]
        )
        self.ui = VisualInterface()
        self.points_manager = PointsManager()
        self.audios_chat = escanear_audios()
        self.last_chatters = set()
        self.audio_volume = 1.0
        
        # Estado do Sorteio
        self.raffle_active = False
        self.raffle_points = 0
        self.raffle_participants = set()
        self.raffle_task = None
        self.last_audio_time = 0



    async def event_ready(self):
        logger.info(f"✅ BOT ONLINE NO CANAL: {CHANNEL}")
        asyncio.create_task(self.points_loop())

    async def event_message(self, message):
        if message.echo or not message.author: return
        author = message.author.name
        content = message.content
        
        if content.startswith('!'):
            logger.info(f"📥 [COMANDO] {author}: {content}")
        else:
            logger.info(f"💬 [CHAT] {author}: {content}")
            
        await self.handle_commands(message)

    @commands.command(name="ping")
    async def ping_cmd(self, ctx):
        await ctx.send(f"🏓 Pong, {ctx.author.name}!")

    @commands.command(name="pontos", aliases=["pts"])
    async def pontos_cmd(self, ctx):
        saldo = self.points_manager.get_points(ctx.author.name)
        await ctx.send(f"🪙 {ctx.author.name}, você tem {saldo} pontos.")

    @commands.command(name="p", aliases=["play"])
    async def play_cmd(self, ctx, *, nome: str = None):
        if not nome:
            await ctx.send("❌ Use: !p <nome>")
            return
        
        # Cooldown de 1 minuto
        cd = 60
        now = time.time()
        elapsed = now - self.last_audio_time
        if elapsed < cd:
            restante = int(cd - elapsed)
            await ctx.send(f"⏳ Cooldown ativo! Aguarde mais {restante} segundos.")
            return

        nome = nome.lower()
        if nome in self.audios_chat:
            audio = self.audios_chat[nome]
            if self.points_manager.remove_points(ctx.author.name, audio['custo']):
                # Atualiza o timestamp apenas se os pontos forem removidos e o áudio for tocar
                self.last_audio_time = now
                await self._play_audio(audio["path"])
                await ctx.send(f"🔊 Tocando: {nome}. Saldo: {self.points_manager.get_points(ctx.author.name)} pts.")
            else:
                await ctx.send(f"❌ Pontos insuficientes!")
        else:
            await ctx.send(f"❌ Áudio '{nome}' não encontrado.")


    @commands.command(name="addpoints", aliases=["dar", "give"])
    async def addpoints_cmd(self, ctx, user: str = None, amount: int = None):
        # Broadcaster (Dono) ou Moderadores podem usar
        if not ctx.author.is_mod and str(ctx.author.id) != BROADCASTER_ID:
            logger.warning(f"🚫 {ctx.author.name} tentou usar addpoints sem permissão.")
            return

        if not user or amount is None:
            await ctx.send("❌ Use: !addpoints <@usuario> <quantidade>")
            return

        target = user.replace("@", "").lower()
        self.points_manager.add_points(target, amount)
        await ctx.send(f"✅ {amount} pontos adicionados para {target}! Saldo: {self.points_manager.get_points(target)} pts.")
        logger.info(f"💰 [SISTEMA] {ctx.author.name} deu {amount} pontos para {target}.")

    @commands.command(name="comandos", aliases=["help", "ajuda"])
    async def comandos_cmd(self, ctx):
        comandos = [
            "!pontos", "!p <nome>", "!tts <msg>", "!audios", 
            "!stop", "!status", "!ping", "!join"
        ]
        if ctx.author.is_mod or str(ctx.author.id) == BROADCASTER_ID:
            comandos.append("!addpoints <@user> <qtd>")
            comandos.append("!reload")
            comandos.append("!sorteio <pts> <min>")
            
        await ctx.send(f"🤖 Comandos disponíveis: {', '.join(comandos)}")

    @commands.command(name="status")
    async def status_cmd(self, ctx):
        # Informações básicas de status
        uptime = "Online" # Simplificado
        total_audios = len(self.audios_chat)
        await ctx.send(f"📊 [STATUS] Texuguito Bot está {uptime}! 🎵 {total_audios} áudios carregados. 🪙 Sistema de pontos ativo.")

    @commands.command(name="audios", aliases=["sons", "sounds"])
    async def audios_cmd(self, ctx):
        if not self.audios_chat:
            await ctx.send("🔈 Nenhum áudio encontrado nas pastas.")
            return

        # Agrupa áudios por custo
        categorias = {}
        for nome, info in self.audios_chat.items():
            custo = info['custo']
            if custo not in categorias:
                categorias[custo] = []
            categorias[custo].append(nome)

        # Monta a mensagem de resposta
        msg = "🎵 Sons Disponíveis: "
        partes = []
        for custo in sorted(categorias.keys()):
            sons = ", ".join(sorted(categorias[custo]))
            partes.append(f"[{custo} pts: {sons}]")
        
        final_msg = msg + " | ".join(partes)
        
        # Twitch tem limite de 500 caracteres, vamos cortar se for muito longo
        if len(final_msg) > 450:
            final_msg = final_msg[:447] + "..."
            
        await ctx.send(final_msg)

    @commands.command(name="reload")
    async def reload_cmd(self, ctx):
        self.audios_chat = escanear_audios()
        await ctx.send("🔄 Recarregado!")

    @commands.command(name="tts")
    async def tts_cmd(self, ctx, *, texto: str = None):
        CUSTO_TTS = 200
        if not texto:
            await ctx.send("❌ Use: !tts <mensagem>")
            return

        if self.points_manager.remove_points(ctx.author.name, CUSTO_TTS):
            try:
                # Cria arquivo temporário para o áudio
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    temp_path = fp.name
                
                # Gera o áudio via gTTS (incluindo o nome de quem enviou)
                texto_completo = f"{ctx.author.name} enviou a mensagem: {texto}"
                tts = gTTS(text=texto_completo, lang='pt', tld='com.br')
                tts.save(temp_path)
                
                # Toca o áudio
                await self._play_audio(temp_path)
                
                # Garante que o pygame solte o arquivo antes de deletar (WinError 32 fix)
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                except: pass
                
                # Pequena pausa para o SO processar a liberação
                await asyncio.sleep(0.5)

                # Remove o arquivo após tocar
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                await ctx.send(f"🎙️ [TTS] {ctx.author.name} enviou uma mensagem! (-{CUSTO_TTS} pts)")
            except Exception as e:
                logger.error(f"Erro no TTS: {e}")
                await ctx.send("❌ Erro ao gerar o TTS.")
        else:
            await ctx.send(f"❌ Pontos insuficientes ({CUSTO_TTS} pts necessários).")

    @commands.command(name="stop")
    async def stop_cmd(self, ctx):
        pygame.mixer.music.stop()
        await ctx.send("⏹️ Áudio parado!")

    @commands.command(name="sorteio")
    async def sorteio_cmd(self, ctx, pontos: int = None, minutos: int = None):
        # Apenas Broadcaster
        if str(ctx.author.id) != BROADCASTER_ID:
            return

        if self.raffle_active:
            await ctx.send("❌ Já existe um sorteio em andamento!")
            return

        if pontos is None or minutos is None or pontos <= 0 or minutos <= 0:
            await ctx.send("❌ Use: !sorteio <pontos> <minutos>")
            return

        self.raffle_active = True
        self.raffle_points = pontos
        self.raffle_participants = set()
        
        await ctx.send(f"🎉 [SORTEIO] Um sorteio de {pontos} pontos começou! Digite !join para participar. Tempo: {minutos} min.")
        logger.info(f"🎁 [SORTEIO] Iniciado por {ctx.author.name}: {pontos} pts, {minutos} min.")
        
        # Inicia a tarefa do sorteio
        self.raffle_task = asyncio.create_task(self.run_raffle(minutos, pontos, ctx))

    @commands.command(name="join")
    async def join_cmd(self, ctx):
        if not self.raffle_active:
            return
        
        user = ctx.author.name.lower()
        if user in self.raffle_participants:
            return # Já está participando
            
        self.raffle_participants.add(user)
        # Feedback silencioso ou discreto para não poluir o chat se quiser
        # await ctx.send(f"✅ {ctx.author.name} entrou no sorteio!")

    async def run_raffle(self, minutos, pontos, ctx):
        await asyncio.sleep(minutos * 60)
        
        self.raffle_active = False
        if not self.raffle_participants:
            await ctx.send("⚠️ O sorteio terminou, mas não houve participantes.")
            logger.info("🎁 [SORTEIO] Terminado sem participantes.")
            return

        ganhador = random.choice(list(self.raffle_participants))
        self.points_manager.add_points(ganhador, pontos)
        
        await ctx.send(f"🎊 PARABÉNS @{ganhador}! Você ganhou o sorteio de {pontos} pontos! 🥳")
        logger.info(f"🎊 [SORTEIO] O ganhador foi {ganhador} ({pontos} pts).")
        
        # Reset do estado
        self.raffle_points = 0
        self.raffle_participants = set()
        self.raffle_task = None

    async def points_loop(self):
        while True:
            await asyncio.sleep(CHECK_INTERVAL)
            try:
                chatters = await self._get_chatters()
                current_set = set(chatters)
                active = self.last_chatters.intersection(current_set)
                if active:
                    for u in active: self.points_manager.add_points(u, POINTS_REWARD)
                    self.ui.log_point_reward(len(active))
                self.last_chatters = current_set
            except Exception as e: logger.error(f"Erro no loop de pontos: {e}")

    async def _get_chatters(self) -> list:
        url = f"https://api.twitch.tv/helix/chat/chatters?broadcaster_id={BROADCASTER_ID}&moderator_id={BROADCASTER_ID}"
        headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {TOKEN}"}
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers))
        if resp.status_code == 200:
            return [u["user_name"].lower() for u in resp.json().get("data", [])]
        return []

    async def _play_audio(self, path):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._play_sync, path)

    def _play_sync(self, path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.audio_volume)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): pygame.time.wait(100)
        except Exception as e: logger.error(f"Erro Áudio: {e}")

async def main():
    ui = VisualInterface()
    ui.show_banner()
    
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, BROADCASTER_ID]):
        print("❌ Faltam credenciais no .env! Rode o setup.bat primeiro.")
        return
    
    # Tenta renovar o token antes de iniciar para garantir conexão
    if not TokenManager.refresh_token():
        logger.warning("⚠️ Não foi possível renovar o token, tentando conectar com o token atual...")

    try: pygame.mixer.init()
    except: pass
    
    bot = TexuguitoBot()
    ui.show_config_table({"Canal": CHANNEL, "Points": f"{POINTS_REWARD}/min", "Status": "Autenticando..."})
    await bot.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('TexuguitoBot')
    rich_handler = RichHandler(console=console, show_time=True, show_path=False, markup=True)
    logger.addHandler(rich_handler)
    asyncio.run(main())
