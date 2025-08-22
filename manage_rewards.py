#!/usr/bin/env python3
"""
Gerenciador de Recompensas do Texuguito Bot
==========================================

Este script permite gerenciar recompensas de Channel Points da Twitch
e sincronizar com o arquivo config.json do bot de forma programática.

Uso:
    python manage_rewards.py create "Nome da Recompensa" --cost 100 --audio "files/audio/som.mp3"
    python manage_rewards.py list
    python manage_rewards.py sync
    python manage_rewards.py remove "Nome da Recompensa"
"""

import argparse
import json
import requests
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import logging
import coloredlogs

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('RewardManager')
coloredlogs.install(level='INFO', logger=logger)

# Carrega variáveis de ambiente
load_dotenv()

class TwitchAPI:
    """Cliente para interação com a API da Twitch"""
    
    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.access_token = os.getenv('TOKEN')
        self.broadcaster_id = os.getenv('BROADCASTER_ID')
        
        if not all([self.client_id, self.access_token, self.broadcaster_id]):
            logger.error("❌ Credenciais da Twitch não configuradas. Execute setup.py primeiro.")
            logger.error("💡 Variáveis necessárias no .env: CLIENT_ID, TOKEN, BROADCASTER_ID")
            sys.exit(1)
        
        self.headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_custom_rewards(self) -> List[Dict]:
        """Obtém todas as recompensas personalizadas do canal"""
        try:
            url = f"https://api.twitch.tv/helix/channel_points/custom_rewards"
            params = {'broadcaster_id': self.broadcaster_id}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                logger.error(f"❌ Erro ao buscar recompensas: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erro na API da Twitch: {e}")
            return []
    
    def create_custom_reward(self, title: str, cost: int, prompt: str = "", 
                           is_enabled: bool = True, background_color: str = None,
                           max_per_stream: int = None, max_per_user_per_stream: int = None,
                           global_cooldown: int = None) -> Optional[Dict]:
        """Cria uma nova recompensa personalizada"""
        try:
            url = f"https://api.twitch.tv/helix/channel_points/custom_rewards"
            params = {'broadcaster_id': self.broadcaster_id}
            
            payload = {
                'title': title,
                'cost': cost,
                'prompt': prompt,
                'is_enabled': is_enabled,
                'should_redemptions_skip_request_queue': True  # Auto-aprovar resgates
            }
            
            # Configurações opcionais
            if background_color:
                payload['background_color'] = background_color
            if max_per_stream is not None:
                payload['is_max_per_stream_enabled'] = True
                payload['max_per_stream'] = max_per_stream
            if max_per_user_per_stream is not None:
                payload['is_max_per_user_per_stream_enabled'] = True
                payload['max_per_user_per_stream'] = max_per_user_per_stream
            if global_cooldown is not None:
                payload['is_global_cooldown_enabled'] = True
                payload['global_cooldown_seconds'] = global_cooldown
            
            response = requests.post(url, headers=self.headers, params=params, json=payload)
            
            if response.status_code == 200:
                reward_data = response.json().get('data', [{}])[0]
                logger.info(f"✅ Recompensa '{title}' criada na Twitch com sucesso!")
                logger.info(f"   ID: {reward_data.get('id')}")
                logger.info(f"   Custo: {cost} pontos")
                return reward_data
            else:
                logger.error(f"❌ Erro ao criar recompensa: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar recompensa: {e}")
            return None
    
    def update_custom_reward(self, reward_id: str, **kwargs) -> bool:
        """Atualiza uma recompensa existente"""
        try:
            url = f"https://api.twitch.tv/helix/channel_points/custom_rewards"
            params = {
                'broadcaster_id': self.broadcaster_id,
                'id': reward_id
            }
            
            # Remove chaves com valor None
            payload = {k: v for k, v in kwargs.items() if v is not None}
            
            response = requests.patch(url, headers=self.headers, params=params, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Recompensa atualizada com sucesso!")
                return True
            else:
                logger.error(f"❌ Erro ao atualizar recompensa: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar recompensa: {e}")
            return False
    
    def delete_custom_reward(self, reward_id: str) -> bool:
        """Remove uma recompensa"""
        try:
            url = f"https://api.twitch.tv/helix/channel_points/custom_rewards"
            params = {
                'broadcaster_id': self.broadcaster_id,
                'id': reward_id
            }
            
            response = requests.delete(url, headers=self.headers, params=params)
            
            if response.status_code == 204:
                logger.info(f"✅ Recompensa removida da Twitch com sucesso!")
                return True
            else:
                logger.error(f"❌ Erro ao remover recompensa: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao remover recompensa: {e}")
            return False

class ConfigManager:
    """Gerenciador do arquivo config.json"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def load_config(self) -> Dict:
        """Carrega configuração do arquivo"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning("⚠️ Arquivo config.json não encontrado, criando um novo...")
                return self._create_default_config()
        except Exception as e:
            logger.error(f"❌ Erro ao carregar config.json: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Cria configuração padrão"""
        default_config = {
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
        
        self.save_config(default_config)
        return default_config
    
    def backup_config(self) -> str:
        """Cria backup do config atual"""
        if not self.config_path.exists():
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.config_path, backup_path)
            logger.info(f"💾 Backup criado: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return ""
    
    def save_config(self, config: Dict) -> bool:
        """Salva configuração no arquivo"""
        try:
            # Cria backup antes de salvar
            self.backup_config()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Config.json atualizado com sucesso!")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar config.json: {e}")
            return False
    
    def add_reward_to_config(self, reward_name: str, audio_path: str, 
                           twitch_id: str = None, cost: int = None) -> bool:
        """Adiciona recompensa ao config"""
        config = self.load_config()
        
        # Adiciona aos mapeamentos de áudio
        config['recompensas_audio'][reward_name] = audio_path
        
        # Adiciona metadados se fornecidos (opcional)
        if 'reward_metadata' not in config:
            config['reward_metadata'] = {}
        
        config['reward_metadata'][reward_name] = {
            'audio_path': audio_path,
            'twitch_id': twitch_id,
            'cost': cost,
            'created_at': datetime.now().isoformat()
        }
        
        return self.save_config(config)
    
    def remove_reward_from_config(self, reward_name: str) -> bool:
        """Remove recompensa do config"""
        config = self.load_config()
        
        removed = False
        if reward_name in config.get('recompensas_audio', {}):
            del config['recompensas_audio'][reward_name]
            removed = True
        
        if reward_name in config.get('reward_metadata', {}):
            del config['reward_metadata'][reward_name]
            removed = True
        
        if removed:
            return self.save_config(config)
        else:
            logger.warning(f"⚠️ Recompensa '{reward_name}' não encontrada no config")
            return False
    
    def get_rewards_from_config(self) -> Dict[str, Dict]:
        """Obtém todas as recompensas do config"""
        config = self.load_config()
        rewards = {}
        
        audio_rewards = config.get('recompensas_audio', {})
        metadata = config.get('reward_metadata', {})
        
        for name, audio_path in audio_rewards.items():
            rewards[name] = {
                'audio_path': audio_path,
                'metadata': metadata.get(name, {})
            }
        
        return rewards

class RewardManager:
    """Gerenciador principal de recompensas"""
    
    def __init__(self):
        self.twitch = TwitchAPI()
        self.config = ConfigManager()
    
    def validate_audio_file(self, audio_path: str) -> bool:
        """Valida se o arquivo de áudio existe"""
        if not Path(audio_path).exists():
            logger.error(f"❌ Arquivo de áudio não encontrado: {audio_path}")
            return False
        return True
    
    def create_reward(self, title: str, cost: int, audio_path: str, 
                     prompt: str = "", **kwargs) -> bool:
        """Cria recompensa na Twitch e adiciona ao config"""
        
        # Valida arquivo de áudio
        if not self.validate_audio_file(audio_path):
            return False
        
        logger.info(f"🎯 Criando recompensa '{title}'...")
        
        # Cria na Twitch
        reward_data = self.twitch.create_custom_reward(title, cost, prompt, **kwargs)
        if not reward_data:
            return False
        
        # Adiciona ao config
        twitch_id = reward_data.get('id')
        success = self.config.add_reward_to_config(title, audio_path, twitch_id, cost)
        
        if success:
            logger.info(f"🎉 Recompensa '{title}' criada e configurada com sucesso!")
            return True
        else:
            logger.error(f"❌ Recompensa criada na Twitch, mas falha ao salvar no config")
            return False
    
    def list_rewards(self, show_details: bool = True) -> None:
        """Lista todas as recompensas"""
        logger.info("📋 Listando recompensas...")
        
        # Recompensas da Twitch
        twitch_rewards = self.twitch.get_custom_rewards()
        twitch_dict = {r['title']: r for r in twitch_rewards}
        
        # Recompensas do config
        config_rewards = self.config.get_rewards_from_config()
        
        print("\n" + "="*80)
        print("🎁 RECOMPENSAS CONFIGURADAS")
        print("="*80)
        
        all_reward_names = set(twitch_dict.keys()) | set(config_rewards.keys())
        
        if not all_reward_names:
            print("❌ Nenhuma recompensa encontrada")
            return
        
        for name in sorted(all_reward_names):
            twitch_data = twitch_dict.get(name)
            config_data = config_rewards.get(name)
            
            print(f"\n🏷️  {name}")
            
            if twitch_data and config_data:
                status = "✅ SINCRONIZADA"
            elif twitch_data:
                status = "⚠️  APENAS NA TWITCH"
            else:
                status = "⚠️  APENAS NO CONFIG"
            
            print(f"   Status: {status}")
            
            if show_details:
                if twitch_data:
                    print(f"   💰 Custo: {twitch_data.get('cost', 'N/A')} pontos")
                    print(f"   🆔 ID Twitch: {twitch_data.get('id', 'N/A')}")
                    print(f"   🔄 Ativa: {'Sim' if twitch_data.get('is_enabled') else 'Não'}")
                
                if config_data:
                    print(f"   🎵 Áudio: {config_data.get('audio_path', 'N/A')}")
                    if Path(config_data.get('audio_path', '')).exists():
                        print(f"   📁 Arquivo: ✅ Encontrado")
                    else:
                        print(f"   📁 Arquivo: ❌ Não encontrado")
    
    def remove_reward(self, title: str) -> bool:
        """Remove recompensa da Twitch e do config"""
        logger.info(f"🗑️ Removendo recompensa '{title}'...")
        
        # Busca ID na Twitch
        twitch_rewards = self.twitch.get_custom_rewards()
        twitch_reward = next((r for r in twitch_rewards if r['title'] == title), None)
        
        success = True
        
        # Remove da Twitch se existir
        if twitch_reward:
            if not self.twitch.delete_custom_reward(twitch_reward['id']):
                success = False
        else:
            logger.warning(f"⚠️ Recompensa '{title}' não encontrada na Twitch")
        
        # Remove do config
        if not self.config.remove_reward_from_config(title):
            success = False
        
        if success:
            logger.info(f"🗑️ Recompensa '{title}' removida com sucesso!")
        
        return success
    
    def sync_rewards(self) -> None:
        """Sincroniza recompensas entre Twitch e config"""
        logger.info("🔄 Sincronizando recompensas...")
        
        twitch_rewards = self.twitch.get_custom_rewards()
        twitch_dict = {r['title']: r for r in twitch_rewards}
        
        config_rewards = self.config.get_rewards_from_config()
        
        # Recompensas órfãs (na Twitch, mas não no config)
        orphaned = set(twitch_dict.keys()) - set(config_rewards.keys())
        if orphaned:
            print(f"\n⚠️  Encontradas {len(orphaned)} recompensas órfãs (apenas na Twitch):")
            for name in orphaned:
                print(f"   - {name}")
            print("💡 Use 'remove' para excluir da Twitch ou configure manualmente o áudio")
        
        # Recompensas perdidas (no config, mas não na Twitch)
        missing = set(config_rewards.keys()) - set(twitch_dict.keys())
        if missing:
            print(f"\n⚠️  Encontradas {len(missing)} recompensas perdidas (apenas no config):")
            for name in missing:
                print(f"   - {name}")
            print("💡 Essas recompensas podem ter sido removidas manualmente da Twitch")
        
        # Arquivos de áudio faltando
        missing_audio = []
        for name, data in config_rewards.items():
            audio_path = data.get('audio_path', '')
            if audio_path and not Path(audio_path).exists():
                missing_audio.append((name, audio_path))
        
        if missing_audio:
            print(f"\n❌ Encontrados {len(missing_audio)} arquivos de áudio faltando:")
            for name, path in missing_audio:
                print(f"   - {name}: {path}")
        
        if not orphaned and not missing and not missing_audio:
            print("\n✅ Todas as recompensas estão sincronizadas!")

def main():
    parser = argparse.ArgumentParser(description="Gerenciador de Recompensas do Texuguito Bot")
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando: create
    create_parser = subparsers.add_parser('create', help='Criar nova recompensa')
    create_parser.add_argument('title', help='Nome da recompensa')
    create_parser.add_argument('--cost', type=int, required=True, help='Custo em pontos')
    create_parser.add_argument('--audio', required=True, help='Caminho do arquivo de áudio')
    create_parser.add_argument('--prompt', default="", help='Descrição da recompensa')
    create_parser.add_argument('--color', help='Cor de fundo (hex)')
    create_parser.add_argument('--max-stream', type=int, help='Máximo por stream')
    create_parser.add_argument('--max-user', type=int, help='Máximo por usuário por stream')
    create_parser.add_argument('--cooldown', type=int, help='Cooldown global em segundos')
    
    # Comando: list
    list_parser = subparsers.add_parser('list', help='Listar recompensas')
    list_parser.add_argument('--simple', action='store_true', help='Listagem simplificada')
    
    # Comando: remove
    remove_parser = subparsers.add_parser('remove', help='Remover recompensa')
    remove_parser.add_argument('title', help='Nome da recompensa para remover')
    
    # Comando: sync
    sync_parser = subparsers.add_parser('sync', help='Sincronizar e verificar inconsistências')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = RewardManager()
    
    if args.command == 'create':
        kwargs = {}
        if args.color:
            kwargs['background_color'] = args.color
        if args.max_stream:
            kwargs['max_per_stream'] = args.max_stream
        if args.max_user:
            kwargs['max_per_user_per_stream'] = args.max_user
        if args.cooldown:
            kwargs['global_cooldown'] = args.cooldown
            
        success = manager.create_reward(
            args.title, 
            args.cost, 
            args.audio, 
            args.prompt,
            **kwargs
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'list':
        manager.list_rewards(show_details=not args.simple)
    
    elif args.command == 'remove':
        success = manager.remove_reward(args.title)
        sys.exit(0 if success else 1)
    
    elif args.command == 'sync':
        manager.sync_rewards()

if __name__ == "__main__":
    main()
