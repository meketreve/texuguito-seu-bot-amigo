from dotenv import load_dotenv
import os
import asyncio
import websockets
import json
import requests
import pygame
from twitchio.ext import commands

# Carrega configurações do arquivo .env
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN = os.getenv("TOKEN")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")
TWITCH_WS_URL = "wss://eventsub.wss.twitch.tv/ws"

# Inicializa pygame para tocar áudio
pygame.init()

# Lista de recompensas e arquivos de áudio correspondentes
recompensas_audio = {
    "320c6743-3658-45f0-875e-998dee1bb59c": "oof.mp3",
    "oof": "oof.mp3",
    "vixe": "files/audio10/vixi.mp3",
    "audio_50": "files/audio50/audio2.mp3",
    "audio_100": "files/audio100/audio3.mp3",
    "audio_200": "files/audio200/audio4.mp3"
}

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=TOKEN, prefix="!", initial_channels=['meketreve'])

    async def event_ready(self):
        print(f'Logado como {self.nick}')
        print(f'ID do usuário: {self.user_id}')
        asyncio.create_task(self.conectar_eventsub())

    async def conectar_eventsub(self):
        async with websockets.connect(TWITCH_WS_URL) as ws:
            print("Conectado ao WebSocket da Twitch")

            # Aguarda mensagem inicial com session_id
            message = await ws.recv()
            data = json.loads(message)
            session_id = data.get("payload", {}).get("session", {}).get("id")
            print(f"Session ID recebido: {session_id}")

            if not session_id:
                print("Erro ao obter session_id.")
                return

            headers = {
                "Client-ID": CLIENT_ID,
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "type": "channel.channel_points_custom_reward_redemption.add",
                "version": "1",
                "condition": {"broadcaster_user_id": BROADCASTER_ID},
                "transport": {"method": "websocket", "session_id": session_id}
            }

            response = requests.post("https://api.twitch.tv/helix/eventsub/subscriptions", json=payload, headers=headers)
            print("Resposta do EventSub:", response.status_code, response.text)

            while True:
                message = await ws.recv()
                data = json.loads(message)
                print(json.dumps(data, indent=4))  # Log dos eventos recebidos

                if "payload" in data and "event" in data["payload"]:
                    recompensa_nome = data["payload"]["event"]["reward"]["title"]
                    print(f"Recompensa resgatada: {recompensa_nome}")

                    if recompensa_nome in recompensas_audio:
                        self.play_audio(recompensas_audio[recompensa_nome])
                    else:
                        print(f"Recompensa não encontrada no dicionário: {recompensa_nome}")

    def play_audio(self, file):
        if os.path.exists(file):
            pygame.mixer.init()
            pygame.mixer.music.load(file)
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.play()
            print(f"Tocando áudio: {file}")
        else:
            print(f"Erro: Arquivo de áudio não encontrado -> {file}")

bot = Bot()
bot.run()