from dotenv import load_dotenv
import os
import asyncio
import websockets
import json
import requests
import pygame
import logging
import coloredlogs
from pathlib import Path
from typing import Dict, Optional
from twitchio.ext import commands

# Carrega configurações do arquivo .env
load_dotenv()

# Configuração de logging
class BotLogger:
    def __init__(self, config: dict):
        self.logger = logging.getLogger('TexuguitoBot')
        
        # Criar pasta de logs se não existir
        log_file = Path(config.get('file', 'logs/bot.log'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar nível de logging
        level = getattr(logging, config.get('level', 'INFO').upper())
        self.logger.setLevel(level)
        
        # Formato
        formatter = logging.Formatter(config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # Handler para arquivo
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler colorido para console
        coloredlogs.install(level=level, logger=self.logger, fmt=config.get('format'))
        
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
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN = os.getenv("TOKEN")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")
TWITCH_WS_URL = "wss://eventsub.wss.twitch.tv/ws"

# Inicializa pygame para tocar áudio
try:
    pygame.mixer.init()
    logger.info("PyGame mixer inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar PyGame mixer: {e}")

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

class Bot(commands.Bot):
    def __init__(self):
        # Configurações do bot
        bot_settings = config.get('bot_settings', {})
        channel = bot_settings.get('channel', 'meketreve')
        prefix = bot_settings.get('command_prefix', '!')
        
        super().__init__(token=TOKEN, prefix=prefix, initial_channels=[channel])
        
        # Inicializa componentes
        self.audio_validator = AudioValidator(config, logger)
        self.max_reconnect_attempts = bot_settings.get('max_reconnect_attempts', 5)
        self.reconnect_delay_base = bot_settings.get('reconnect_delay_base', 2)
        self.audio_volume = bot_settings.get('audio_volume', 1.0)
        self.is_connected = False
        
        logger.info(f"Bot inicializado - Canal: {channel}, Prefix: {prefix}")
    
    async def event_ready(self):
        """Evento chamado quando o bot está pronto"""
        logger.info(f'🤖 Bot logado como: {self.nick}')
        logger.info(f'📊 ID do usuário: {self.user_id}')
        
        # Valida arquivos de áudio na inicialização
        logger.info("🔍 Validando arquivos de áudio...")
        validation_results = self.audio_validator.validate_audio_files()
        
        # Inicia conexão com EventSub
        asyncio.create_task(self.conectar_eventsub_com_retry())
    
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
                
                # Registra subscription para recompensas
                await self._registrar_subscription(session_id)
                
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
                    
                    # Reproduz áudio correspondente
                    await self._tocar_audio_recompensa(reward_title)
                    
        except Exception as e:
            logger.error(f"❌ Erro ao processar evento: {e}")
    
    async def _tocar_audio_recompensa(self, reward_title: str):
        """Reproduz áudio baseado na recompensa resgatada"""
        try:
            audio_path = self.audio_validator.get_audio_path(reward_title)
            
            if audio_path:
                await self._play_audio(audio_path)
                logger.info(f"🔊 Áudio reproduzido para recompensa: {reward_title}")
            else:
                logger.warning(f"⚠️ Nenhum áudio configurado para a recompensa: {reward_title}")
                
                # Tenta tocar áudio de fallback se configurado
                fallback_path = config.get('audio_paths.fallback_sound')
                if fallback_path and Path(fallback_path).exists():
                    await self._play_audio(fallback_path)
                    logger.info(f"🔊 Áudio de fallback reproduzido")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao reproduzir áudio para recompensa '{reward_title}': {e}")
    
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
    
    @commands.command(name='status')
    async def status_command(self, ctx):
        """Comando para verificar status do bot"""
        try:
            status_msg = "🤖 **Status do Texuguito Bot**\n"
            status_msg += f"📡 Conectado: {'✅' if self.is_connected else '❌'}\n"
            status_msg += f"🎵 Recompensas configuradas: {len(config.get('recompensas_audio', {}))}\n"
            
            await ctx.send(status_msg)
            logger.info(f"Comando !status executado por {ctx.author.name}")
            
        except Exception as e:
            logger.error(f"❌ Erro no comando status: {e}")

def main():
    """Função principal para inicializar o bot"""
    try:
        # Verifica variáveis de ambiente necessárias
        required_env_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'TOKEN', 'BROADCASTER_ID']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
            logger.info("💡 Execute setup.py primeiro para configurar as credenciais")
            return
        
        logger.info("🚀 Iniciando Texuguito Bot...")
        
        # Cria e executa o bot
        bot = Bot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"💀 Erro fatal na inicialização: {e}")
        raise

if __name__ == "__main__":
    main()
