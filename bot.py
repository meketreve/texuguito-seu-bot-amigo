from dotenv import load_dotenv
import os
import asyncio
import websockets
import json
import requests
import pygame
import logging
<<<<<<< HEAD
from datetime import datetime
from twitchio.ext import commands
from twitchio import eventsub
=======
import time
from pathlib import Path
from typing import Dict, Optional

# Rich imports para interface visual
from rich.console import Console
from rich.panel import Panel
from rich.progress import track, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.logging import RichHandler
from rich.text import Text
from rich.live import Live
from rich import box

# Emoji import
import emoji
>>>>>>> 15c8251eb3496dfa0aece22efad0b288d44b94ab

# Carrega configurações do arquivo .env
load_dotenv()

# Console global para rich
console = Console()

# Utilitários para emojis
def em(emoji_code: str) -> str:
    """Converte código emoji para caractere"""
    return emoji.emojize(emoji_code)

class VisualInterface:
    """Interface visual usando Rich"""
    
    def __init__(self):
        self.console = console
    
    def show_banner(self):
        """Mostra banner inicial do bot"""
        banner_text = Text()
        banner_text.append(em(":badger:"), style="bold blue")
        banner_text.append(" Texuguito Bot ", style="bold blue")
        banner_text.append(em(":musical_note:"), style="bold yellow")
        banner_text.append(" Seu Bot Amigo", style="bold blue")
        
        banner = Panel(
            banner_text,
            title="[bold green]Sistema Iniciando[/]",
            border_style="blue",
            box=box.DOUBLE
        )
        self.console.print(banner)
        self.console.print()
    
    def show_startup_progress(self, tasks: list):
        """Mostra progresso de inicialização"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            for task_name in tasks:
                task_id = progress.add_task(f"[cyan]{task_name}...", total=None)
                time.sleep(0.8)  # Simula carregamento
                progress.update(task_id, completed=100)
    
    def show_config_table(self, bot_config: dict):
        """Mostra tabela de configurações"""
        table = Table(title=f"{em(':gear:')} Configurações Carregadas", box=box.ROUNDED)
        table.add_column("Item", style="cyan", no_wrap=True)
        table.add_column("Valor", style="magenta")
        
        table.add_row(f"{em(':television:')} Canal", bot_config.get('channel', 'N/A'))
        table.add_row(f"{em(':speaker:')} Volume", f"{bot_config.get('audio_volume', 1.0):.1f}")
        table.add_row(f"{em(':repeat:')} Max Reconexões", str(bot_config.get('max_reconnect_attempts', 5)))
        
        self.console.print(table)
        self.console.print()
    
    def show_audio_validation(self, validation_results: dict):
        """Mostra resultado da validação de áudios"""
        if not validation_results:
            self.console.print(f"{em(':warning:')} [yellow]Nenhuma recompensa configurada[/]")
            return
        
        table = Table(title=f"{em(':musical_note:')} Validação de Áudios", box=box.SIMPLE)
        table.add_column("Recompensa", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Arquivo", style="dim")
        
        for reward_name, exists in validation_results.items():
            status = f"{em(':check_mark_button:')} [green]OK[/]" if exists else f"{em(':cross_mark:')} [red]Erro[/]"
            audio_file = config.get('recompensas_audio', {}).get(reward_name, "N/A")
            table.add_row(reward_name, status, audio_file)
        
        self.console.print(table)
        self.console.print()
    
    def show_connection_status(self, connected: bool, session_id: str = None):
        """Mostra status da conexão"""
        if connected:
            status_text = Text()
            status_text.append(em(":satellite:"), style="green")
            status_text.append(" Conectado ao EventSub da Twitch ", style="bold green")
            status_text.append(em(":check_mark_button:"), style="green")
            
            if session_id:
                status_text.append(f"\nSession ID: {session_id[:8]}...", style="dim")
            
            panel = Panel(status_text, border_style="green", box=box.ROUNDED)
        else:
            status_text = Text()
            status_text.append(em(":cross_mark:"), style="red")
            status_text.append(" Desconectado ", style="bold red")
            status_text.append(em(":warning:"), style="red")
            
            panel = Panel(status_text, border_style="red", box=box.ROUNDED)
        
        self.console.print(panel)
    
    def log_reward_redemption(self, reward_title: str, user_name: str, audio_played: bool):
        """Log visual para resgate de recompensa"""
        reward_text = Text()
        reward_text.append(em(":gift:"), style="yellow")
        reward_text.append(f" {reward_title} ", style="bold yellow")
        reward_text.append(f"resgatada por ", style="white")
        reward_text.append(f"{user_name}", style="bold cyan")
        
        if audio_played:
            reward_text.append(f" {em(':speaker:')}", style="green")
        else:
            reward_text.append(f" {em(':muted_speaker:')}", style="red")
        
        panel = Panel(
            reward_text, 
            title="[bold]Recompensa Resgatada[/]",
            border_style="yellow",
            box=box.SIMPLE
        )
        self.console.print(panel)

# Configuração de logging híbrido
class BotLogger:
    def __init__(self, config: dict):
        self.logger = logging.getLogger('TexuguitoBot')
        
        # Criar pasta de logs se não existir
        log_file = Path(config.get('file', 'logs/bot.log'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar nível de logging
        level = getattr(logging, config.get('level', 'INFO').upper())
        self.logger.setLevel(level)
        
        # Handler para arquivo (formato tradicional)
        formatter = logging.Formatter(config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler Rich para console (visual)
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True
        )
        rich_handler.setLevel(level)
        self.logger.addHandler(rich_handler)
        
    def get_logger(self):
        return self.logger

# Configuração global
class Config:
    def __init__(self, config_file: str = "config.json"):
        self.config_path = Path(config_file)
        self.data = self._load_config()
        
    def _load_config(self) -> dict:
        """Carrega configuração do arquivo JSON"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Configuração padrão caso o arquivo não seja encontrado"""
        return {
            "bot_settings": {
                "channel": "meketreve",
                "command_prefix": "!",
                "audio_volume": 1.0,
                "max_reconnect_attempts": 5,
                "reconnect_delay_base": 2
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/bot.log"
            },
            "recompensas_audio": {},
            "audio_paths": {
                "base_directory": "files",
                "fallback_sound": "files/audio/default.mp3"
            }
        }
    
    def get(self, key: str, default=None):
        """Obtém valor da configuração"""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

# Inicialização
config = Config()
logger_instance = BotLogger(config.get('logging', {}))
logger = logger_instance.get_logger()

# Variáveis de ambiente
CLIENT_ID = os.getenv("CLIENT_ID")
TOKEN = os.getenv("TOKEN")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")
CHANNEL = os.getenv("CHANNEL", "meketreve")  # Canal configurável via .env
TWITCH_WS_URL = "wss://eventsub.wss.twitch.tv/ws"

# Configuração do sistema de logs
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configura logger para arquivo
log_filename = os.path.join(LOG_DIR, f"chat_{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()  # Também mostra no console
    ]
)
logger = logging.getLogger('texuguito')

# Diretório de áudios
FILES_DIR = os.path.join(os.path.dirname(__file__), "files")

def escanear_audios():
    """
    Escaneia a pasta files/ e cria mapeamento de áudios.
    Estrutura: files/<custo>/<nome>.mp3
    Retorna: {nome: {"path": caminho, "custo": custo}}
    """
    audios = {}
    
    if not os.path.exists(FILES_DIR):
        print(f"⚠️ Pasta {FILES_DIR} não encontrada.")
        return audios
    
    for pasta in os.listdir(FILES_DIR):
        pasta_path = os.path.join(FILES_DIR, pasta)
        
        # Verifica se é uma pasta com nome numérico (custo)
        if os.path.isdir(pasta_path) and pasta.isdigit():
            custo = int(pasta)
            
            # Escaneia arquivos de áudio na pasta
            for arquivo in os.listdir(pasta_path):
                if arquivo.lower().endswith(('.mp3', '.wav', '.ogg')):
                    nome = os.path.splitext(arquivo)[0].lower()
                    caminho = os.path.join(pasta_path, arquivo)
                    
                    audios[nome] = {
                        "path": caminho,
                        "custo": custo
                    }
    
    print(f"🎵 Escaneados {len(audios)} áudios em {FILES_DIR}")
    for nome, info in audios.items():
        print(f"   • {nome} ({info['custo']} pontos)")
    
    return audios

# Inicializa pygame para tocar áudio
try:
    pygame.mixer.init()
    logger.info("PyGame mixer inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar PyGame mixer: {e}")

<<<<<<< HEAD
# Carrega áudios da pasta files
audios_disponiveis = escanear_audios()

class Bot(commands.Bot):
=======
# Validador de arquivos de áudio
class AudioValidator:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.recompensas_audio = config.get('recompensas_audio', {})
        
    def validate_audio_files(self) -> Dict[str, bool]:
        """Valida se todos os arquivos de áudio existem"""
        validation_results = {}
        missing_files = []
        
        for reward_name, audio_file in self.recompensas_audio.items():
            file_path = Path(audio_file)
            exists = file_path.exists()
            validation_results[reward_name] = exists
            
            if exists:
                self.logger.info(f"✅ Arquivo encontrado: {audio_file}")
            else:
                self.logger.warning(f"❌ Arquivo não encontrado: {audio_file}")
                missing_files.append(audio_file)
        
        if missing_files:
            self.logger.warning(f"Total de {len(missing_files)} arquivo(s) não encontrado(s)")
            self.logger.info("Dica: Certifique-se de que os caminhos no config.json estão corretos")
        else:
            self.logger.info("Todos os arquivos de áudio foram validados com sucesso!")
            
        return validation_results
    
    def get_audio_path(self, reward_name: str) -> Optional[str]:
        """Retorna o caminho do arquivo de áudio para uma recompensa"""
        return self.recompensas_audio.get(reward_name)
>>>>>>> 15c8251eb3496dfa0aece22efad0b288d44b94ab

class TexuguitoBot:
    def __init__(self):
<<<<<<< HEAD
        super().__init__(
            token=TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BROADCASTER_ID,
            prefix="!",
            initial_channels=[CHANNEL]
        )
        self.reconectar = True  # Flag para controle de reconexão

    async def setup_hook(self):
        """Registra comandos após o bot inicializar"""
        # Cria e registra comandos
        @commands.command(name="ping")
        async def ping_cmd(ctx):
            await ctx.send(f"🏓 Pong, {ctx.author.name}!")
        
        @commands.command(name="p", aliases=["play", "tocar"])
        async def play_cmd(ctx, *, nome: str = None):
            global audios_disponiveis
            if not nome:
                await ctx.send("❌ Use: !p <nome>. Digite !audios para ver a lista.")
                return
            nome_lower = nome.lower()
            
            # Busca exata
            if nome_lower in audios_disponiveis:
                audio = audios_disponiveis[nome_lower]
                self.play_audio(audio["path"])
                await ctx.send(f"🔊 Tocando: {nome_lower} ({audio['custo']} pts)")
                logger.info(f"[AUDIO] {ctx.author.name} tocou {nome_lower} ({audio['custo']} pts)")
                return
            
            # Busca parcial
            encontrados = [k for k in audios_disponiveis.keys() if nome_lower in k]
            if encontrados:
                key = encontrados[0]
                audio = audios_disponiveis[key]
                self.play_audio(audio["path"])
                await ctx.send(f"🔊 Tocando: {key} ({audio['custo']} pts)")
                logger.info(f"[AUDIO] {ctx.author.name} tocou {key} ({audio['custo']} pts)")
            else:
                await ctx.send(f"❌ Áudio '{nome}' não encontrado.")
        
        @commands.command(name="audios", aliases=["sons", "lista"])
        async def audios_cmd(ctx):
            global audios_disponiveis
            if not audios_disponiveis:
                await ctx.send("❌ Nenhum áudio disponível.")
                return
            
            # Agrupa por custo
            por_custo = {}
            for nome, info in audios_disponiveis.items():
                custo = info["custo"]
                if custo not in por_custo:
                    por_custo[custo] = []
                por_custo[custo].append(nome)
            
            # Formata a lista
            partes = []
            for custo in sorted(por_custo.keys()):
                nomes = por_custo[custo][:5]  # Limita a 5 por custo
                extra = f"(+{len(por_custo[custo])-5})" if len(por_custo[custo]) > 5 else ""
                partes.append(f"[{custo}pts] {', '.join(nomes)} {extra}")
            
            await ctx.send(f"🎵 Áudios: {' | '.join(partes[:3])}")
        
        @commands.command(name="stop", aliases=["parar"])
        async def stop_cmd(ctx):
            try:
                pygame.mixer.music.stop()
                await ctx.send("⏹️ Áudio parado!")
            except:
                await ctx.send("❌ Nenhum áudio tocando.")
        
        @commands.command(name="reload", aliases=["recarregar"])
        async def reload_cmd(ctx):
            global audios_disponiveis
            audios_disponiveis = escanear_audios()
            await ctx.send(f"🔄 Recarregados {len(audios_disponiveis)} áudios!")
            logger.info(f"[SISTEMA] {ctx.author.name} recarregou os áudios")
        
        @commands.command(name="comandos", aliases=["help", "ajuda", "cmds"])
        async def help_cmd(ctx):
            await ctx.send("📋 Comandos: !ping, !p <nome>, !audios, !stop, !reload, !comandos")
        
        self.add_command(ping_cmd)
        self.add_command(play_cmd)
        self.add_command(audios_cmd)
        self.add_command(stop_cmd)
        self.add_command(reload_cmd)
        self.add_command(help_cmd)
        print(f"✅ {len(self.commands)} comandos registrados")

    async def event_ready(self):
        print(f'🦡 Bot conectado!')
        print(f'📺 Canal: {CHANNEL}')
        print(f'🆔 Broadcaster ID: {BROADCASTER_ID}')
        print(f'📝 Logs salvos em: {log_filename}')
        logger.info(f"=== BOT INICIADO - Canal: {CHANNEL} ===")
        
        # Inscreve no evento de mensagens do chat via EventSub
        try:
            print("[DEBUG] Inscrevendo no chat via EventSub...")
            
            # Adiciona o user token ao bot
            await self.add_token(TOKEN, BROADCASTER_ID)
            
            subscription = eventsub.ChatMessageSubscription(
                broadcaster_user_id=BROADCASTER_ID,
                user_id=BROADCASTER_ID
            )
            await self.subscribe_websocket(subscription, token_for=BROADCASTER_ID)
            print("[DEBUG] ✅ Inscrito no channel.chat.message")
        except Exception as e:
            print(f"[DEBUG] ❌ Erro ao inscrever no chat: {e}")
        
        asyncio.create_task(self.conectar_eventsub())

    async def event_message(self, message):
        """Captura todas as mensagens do chat"""
        try:
            # Ignora mensagens do próprio bot (echo)
            if hasattr(message, 'echo') and message.echo:
                return
            
            # Obtém autor e conteúdo
            if hasattr(message, 'chatter') and message.chatter:
                author = message.chatter.name
            elif hasattr(message, 'author') and message.author:
                author = message.author.name
            else:
                author = "Desconhecido"
            
            content = message.text if hasattr(message, 'text') else str(message.content)
            
            # Detecta se é um comando (começa com !)
            if content.startswith("!"):
                logger.info(f"[COMANDO] {author}: {content}")
            else:
                logger.info(f"[CHAT] {author}: {content}")
            
            # Processa comandos
            print(f"[DEBUG] Processando comandos para: {content}")
            result = await self.process_commands(message)
            print(f"[DEBUG] Resultado: {result}")
        except Exception as e:
            logger.error(f"[ERRO] Falha ao processar mensagem: {e}")

    async def event_command_error(self, payload):
        """Silencia erros de comandos não encontrados"""
        from twitchio.ext.commands.exceptions import CommandNotFound
        error = payload.exception if hasattr(payload, 'exception') else payload
        if isinstance(error, CommandNotFound):
            pass  # Ignora comandos não registrados
        else:
            logger.error(f"[ERRO COMANDO] {error}")

    async def conectar_eventsub(self):
        """Conecta ao EventSub com reconexão automática"""
        tentativas = 0
        max_tentativas = 5
        
        while self.reconectar:
            try:
                await self._conectar_websocket()
            except websockets.exceptions.ConnectionClosed as e:
                tentativas += 1
                if tentativas >= max_tentativas:
                    print(f"❌ Máximo de tentativas ({max_tentativas}) atingido. Parando reconexão.")
                    break
                tempo_espera = min(30, 2 ** tentativas)  # Backoff exponencial, max 30s
                print(f"⚠️ Conexão fechada: {e}. Reconectando em {tempo_espera}s... (tentativa {tentativas}/{max_tentativas})")
                await asyncio.sleep(tempo_espera)
            except Exception as e:
                print(f"❌ Erro inesperado no WebSocket: {e}")
                tentativas += 1
                if tentativas >= max_tentativas:
                    break
                await asyncio.sleep(5)

    async def _conectar_websocket(self):
        """Lógica principal de conexão WebSocket"""
        async with websockets.connect(TWITCH_WS_URL) as ws:
            print("🔌 Conectado ao WebSocket da Twitch")

            # Aguarda mensagem inicial com session_id
            message = await ws.recv()
            data = json.loads(message)
            session_id = data.get("payload", {}).get("session", {}).get("id")
            print(f"🔑 Session ID recebido: {session_id}")

            if not session_id:
                print("❌ Erro ao obter session_id.")
                return

            # Registra subscription no EventSub
            if not await self._registrar_eventsub(session_id):
                return

            # Loop principal de escuta
            while True:
                message = await ws.recv()
                data = json.loads(message)
                
                # Responde a keepalive silenciosamente
                if data.get("metadata", {}).get("message_type") == "session_keepalive":
                    continue
                
                if "payload" in data and "event" in data["payload"]:
                    await self._processar_evento(data["payload"]["event"])

    async def _registrar_eventsub(self, session_id):
        """Registra a subscription no EventSub"""
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

        try:
            response = requests.post(
                "https://api.twitch.tv/helix/eventsub/subscriptions",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 202]:
                print("✅ EventSub registrado com sucesso!")
                return True
            else:
                print(f"❌ Erro no EventSub: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao registrar EventSub: {e}")
            return False

    async def _processar_evento(self, evento):
        """Processa um evento de resgate de recompensa"""
        recompensa_nome = evento.get("reward", {}).get("title", "")
        usuario = evento.get("user_name", "Desconhecido")
        
        # Log do resgate
        logger.info(f"[RECOMPENSA] {usuario} resgatou: {recompensa_nome}")
        print(f"🎁 Recompensa resgatada por {usuario}: {recompensa_nome}")

        if recompensa_nome in recompensas_audio:
            self.play_audio(recompensas_audio[recompensa_nome])
        else:
            print(f"⚠️ Recompensa não encontrada no config.json: {recompensa_nome}")

    def play_audio(self, file):
        """Toca um arquivo de áudio"""
        if os.path.exists(file):
            try:
                pygame.mixer.init()
                pygame.mixer.music.load(file)
                pygame.mixer.music.set_volume(1)
                pygame.mixer.music.play()
                logger.info(f"[AUDIO] Tocando: {file}")
            except pygame.error as e:
                print(f"❌ Erro ao tocar áudio: {e}")
        else:
            print(f"❌ Arquivo de áudio não encontrado -> {file}")

    def recarregar_config(self):
        """Recarrega as recompensas do config.json"""
        global recompensas_audio
        recompensas_audio = carregar_recompensas()
        logger.info("[SISTEMA] Configurações recarregadas")

if __name__ == "__main__":
    print(f"📁 Logs serão salvos em: {log_filename}")
    bot = Bot()
    bot.run()
=======
        # Interface visual
        self.ui = VisualInterface()
        
        # Configurações do bot
        bot_settings = config.get('bot_settings', {})
        self.channel = bot_settings.get('channel', 'meketreve')
        
        # Inicializa componentes
        self.audio_validator = AudioValidator(config, logger)
        self.max_reconnect_attempts = bot_settings.get('max_reconnect_attempts', 5)
        self.reconnect_delay_base = bot_settings.get('reconnect_delay_base', 2)
        self.audio_volume = bot_settings.get('audio_volume', 1.0)
        self.is_connected = False
        
        logger.info(f"[bold blue]Bot inicializado para canal:[/] [cyan]{self.channel}[/]")
    
    async def start(self):
        """Inicia o bot"""
        logger.info('🤖 Texuguito Bot iniciado!')
        
        # Valida arquivos de áudio na inicialização
        logger.info("🔍 Validando arquivos de áudio...")
        validation_results = self.audio_validator.validate_audio_files()
        
        # Inicia conexão com EventSub
        await self.conectar_eventsub_com_retry()
    
    async def conectar_eventsub_com_retry(self):
        """Conecta ao EventSub com sistema de retry automático"""
        for tentativa in range(self.max_reconnect_attempts):
            try:
                logger.info(f"🔄 Tentativa de conexão {tentativa + 1}/{self.max_reconnect_attempts}")
                await self.conectar_eventsub()
                break
            except Exception as e:
                logger.error(f"❌ Falha na tentativa {tentativa + 1}: {e}")
                if tentativa < self.max_reconnect_attempts - 1:
                    delay = self.reconnect_delay_base ** tentativa
                    logger.info(f"⏳ Aguardando {delay}s antes da próxima tentativa...")
                    await asyncio.sleep(delay)
                else:
                    logger.error("💀 Máximo de tentativas de reconexão atingido. Bot será encerrado.")
                    return
    
    async def conectar_eventsub(self):
        """Conecta ao WebSocket da Twitch EventSub"""
        try:
            async with websockets.connect(TWITCH_WS_URL) as ws:
                logger.info("✅ Conectado ao WebSocket da Twitch")
                self.is_connected = True
                
                # Aguarda mensagem inicial com session_id
                message = await ws.recv()
                data = json.loads(message)
                session_id = data.get("payload", {}).get("session", {}).get("id")
                
                if not session_id:
                    raise Exception("Não foi possível obter session_id do WebSocket")
                
                logger.info(f"🆔 Session ID recebido: {session_id}")
                
                # Mostra status de conexão bem-sucedida
                self.ui.show_connection_status(True, session_id)
                
                # Registra subscription para recompensas
                await self._registrar_subscription(session_id)
                
                # Mensagem final de status
                console.print(f"\n{em(':rocket:')} [bold green]Bot está rodando e aguardando resgates![/]")
                console.print(f"{em(':information:')} [dim]Pressione Ctrl+C para parar o bot[/]")
                
                # Loop principal de escuta
                await self._escutar_eventos(ws)
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"⚠️ Conexão WebSocket fechada: {e}")
            self.is_connected = False
            raise
        except Exception as e:
            logger.error(f"❌ Erro na conexão EventSub: {e}")
            self.is_connected = False
            raise
    
    async def _registrar_subscription(self, session_id: str):
        """Registra subscription para eventos de recompensas"""
        try:
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
            
            response = requests.post(
                "https://api.twitch.tv/helix/eventsub/subscriptions", 
                json=payload, 
                headers=headers
            )
            
            if response.status_code == 202:
                logger.info("✅ Subscription registrada com sucesso")
            else:
                logger.error(f"❌ Erro ao registrar subscription: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao registrar subscription: {e}")
            raise
    
    async def _escutar_eventos(self, ws):
        """Loop principal para escutar eventos do WebSocket"""
        try:
            while True:
                message = await ws.recv()
                await self._processar_evento(json.loads(message))
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ Conexão WebSocket foi fechada")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao escutar eventos: {e}")
            raise
    
    async def _processar_evento(self, data: dict):
        """Processa eventos recebidos do WebSocket"""
        try:
            # Log detalhado apenas em modo DEBUG
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Evento recebido: {json.dumps(data, indent=2)}")
            
            # Verifica se é um evento de recompensa
            if "payload" in data and "event" in data["payload"]:
                event_data = data["payload"]["event"]
                
                if "reward" in event_data and "title" in event_data["reward"]:
                    reward_title = event_data["reward"]["title"]
                    user_name = event_data.get("user_name", "Usuário desconhecido")
                    
                    logger.info(f"🎁 Recompensa '{reward_title}' resgatada por {user_name}")
                    
                    # Reproduz áudio correspondente e mostra log visual
                    audio_played = await self._tocar_audio_recompensa(reward_title)
                    
                    # Log visual da recompensa
                    self.ui.log_reward_redemption(reward_title, user_name, audio_played)
                    
        except Exception as e:
            logger.error(f"❌ Erro ao processar evento: {e}")
    
    async def _tocar_audio_recompensa(self, reward_title: str) -> bool:
        """Reproduz áudio baseado na recompensa resgatada"""
        try:
            audio_path = self.audio_validator.get_audio_path(reward_title)
            
            if audio_path:
                await self._play_audio(audio_path)
                logger.info(f"🔊 Áudio reproduzido para recompensa: {reward_title}")
                return True
            else:
                logger.warning(f"⚠️ Nenhum áudio configurado para a recompensa: {reward_title}")
                
                # Tenta tocar áudio de fallback se configurado
                fallback_path = config.get('audio_paths.fallback_sound')
                if fallback_path and Path(fallback_path).exists():
                    await self._play_audio(fallback_path)
                    logger.info(f"🔊 Áudio de fallback reproduzido")
                    return True
                
                return False
                    
        except Exception as e:
            logger.error(f"❌ Erro ao reproduzir áudio para recompensa '{reward_title}': {e}")
            return False
    
    async def _play_audio(self, file_path: str):
        """Reproduz arquivo de áudio de forma assíncrona"""
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Executa reprodução em thread separada para não bloquear o loop de eventos
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._play_audio_sync, file_path)
            
        except Exception as e:
            logger.error(f"❌ Erro ao reproduzir áudio '{file_path}': {e}")
    
    def _play_audio_sync(self, file_path: str):
        """Reproduz áudio de forma síncrona (executada em thread separada)"""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(self.audio_volume)
            pygame.mixer.music.play()
            
            # Aguarda até o áudio terminar
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
        except Exception as e:
            logger.error(f"❌ Erro na reprodução síncrona do áudio: {e}")
    
    def get_status(self) -> str:
        """Retorna status do bot como string"""
        status_msg = f"🤖 Texuguito Bot\n"
        status_msg += f"📡 Conectado: {'✅' if self.is_connected else '❌'}\n"
        status_msg += f"🎵 Recompensas: {len(config.get('recompensas_audio', {}))}\n"
        status_msg += f"🏠 Canal: {self.channel}"
        return status_msg

async def main():
    """Função principal para inicializar o bot"""
    # Interface visual
    ui = VisualInterface()
    
    try:
        # Mostra banner inicial
        ui.show_banner()
        
        # Verifica variáveis de ambiente necessárias
        required_env_vars = ['CLIENT_ID', 'TOKEN', 'BROADCASTER_ID']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            console.print(f"{em(':cross_mark:')} [bold red]Variáveis de ambiente faltando:[/] {', '.join(missing_vars)}")
            console.print(f"{em(':light_bulb:')} [yellow]Execute[/] [bold cyan]setup.py[/] [yellow]primeiro para configurar as credenciais[/]")
            return
        
        # Progresso de inicialização
        startup_tasks = [
            "Carregando configurações",
            "Inicializando pygame",
            "Validando arquivos de áudio",
            "Preparando conexão"
        ]
        ui.show_startup_progress(startup_tasks)
        
        # Cria o bot
        bot = TexuguitoBot()
        
        # Mostra tabela de configurações
        bot_config = config.get('bot_settings', {})
        ui.show_config_table(bot_config)
        
        # Mostra validação de áudios
        console.print(f"\n{em(':magnifying_glass_tilted_right:')} [bold cyan]Validando Áudios...[/]")
        validation_results = bot.audio_validator.validate_audio_files()
        ui.show_audio_validation(validation_results)
        
        # Status antes da conexão
        console.print(f"\n{em(':satellite:')} [bold blue]Conectando ao EventSub da Twitch...[/]")
        ui.show_connection_status(False)
        
        # Inicia o bot
        await bot.start()
        
    except KeyboardInterrupt:
        console.print(f"\n{em(':stop_button:')} [bold yellow]Bot interrompido pelo usuário[/]")
        ui.show_connection_status(False)
    except Exception as e:
        console.print(f"\n{em(':skull:')} [bold red]Erro fatal:[/] {e}")
        ui.show_connection_status(False)
        raise

if __name__ == "__main__":
    asyncio.run(main())
>>>>>>> 15c8251eb3496dfa0aece22efad0b288d44b94ab
