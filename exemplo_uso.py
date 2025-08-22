#!/usr/bin/env python3
"""
Exemplo de Uso do Sistema de Gerenciamento de Recompensas
========================================================

Este script demonstra como usar o sistema de gerenciamento 
de recompensas do Texuguito Bot programaticamente.

Execute: python exemplo_uso.py
"""

import os
from pathlib import Path
from manage_rewards import RewardManager

def main():
    print("🎁 Exemplo de Uso - Sistema de Gerenciamento de Recompensas")
    print("=" * 60)
    
    # Verifica se as credenciais estão configuradas
    required_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'TOKEN', 'BROADCASTER_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Credenciais faltando: {', '.join(missing_vars)}")
        print("💡 Execute 'python setup.py' primeiro!")
        return
    
    # Cria instância do gerenciador
    manager = RewardManager()
    
    print("\n1️⃣ Listando recompensas existentes...")
    print("-" * 40)
    manager.list_rewards()
    
    print("\n2️⃣ Criando estrutura de exemplo...")
    print("-" * 40)
    
    # Cria pastas de exemplo
    example_dirs = [
        "files/audio",
        "files/epic", 
        "files/funny",
        "files/victory"
    ]
    
    for dir_path in example_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Pasta criada: {dir_path}")
    
    # Cria arquivos de áudio de exemplo (vazios, só para demonstrar)
    example_files = [
        "files/audio/oof.mp3",
        "files/audio/bell.wav",
        "files/epic/epic_horn.mp3",
        "files/funny/laugh.wav",
        "files/victory/victory_fanfare.mp3"
    ]
    
    for file_path in example_files:
        if not Path(file_path).exists():
            # Cria arquivo vazio só para exemplo
            Path(file_path).touch()
            print(f"🎵 Arquivo criado (exemplo): {file_path}")
    
    print("\n3️⃣ Exemplos de criação de recompensas...")
    print("-" * 40)
    
    # Lista de recompensas de exemplo
    example_rewards = [
        {
            "title": "Oof Sound", 
            "cost": 50, 
            "audio": "files/audio/oof.mp3",
            "prompt": "O clássico som de oof!"
        },
        {
            "title": "Epic Horn", 
            "cost": 300, 
            "audio": "files/epic/epic_horn.mp3",
            "prompt": "Para momentos épicos! 🎺",
            "max_per_stream": 5,
            "global_cooldown": 30,
            "background_color": "#FFD700"
        },
        {
            "title": "Risada", 
            "cost": 100, 
            "audio": "files/funny/laugh.wav",
            "prompt": "Uma risada para alegrar o chat! 😄",
            "max_per_user_per_stream": 3
        },
        {
            "title": "Vitória", 
            "cost": 250, 
            "audio": "files/victory/victory_fanfare.mp3",
            "prompt": "Celebre suas vitórias! 🏆",
            "max_per_stream": 10,
            "global_cooldown": 60
        }
    ]
    
    print("Demonstrando criação de recompensas:")
    print("(Remova o comentário para executar de verdade)\n")
    
    for reward in example_rewards:
        title = reward.pop("title")
        cost = reward.pop("cost")
        audio = reward.pop("audio")
        prompt = reward.pop("prompt", "")
        
        print(f"🎯 Recompensa: {title}")
        print(f"   💰 Custo: {cost} pontos")
        print(f"   🎵 Áudio: {audio}")
        print(f"   📝 Descrição: {prompt}")
        
        if reward:  # Se há configurações extras
            print(f"   ⚙️ Configurações extras: {reward}")
        
        # Descomente a linha abaixo para criar de verdade:
        # success = manager.create_reward(title, cost, audio, prompt, **reward)
        # print(f"   {'✅ Criada!' if success else '❌ Falha!'}")
        
        print()
    
    print("\n4️⃣ Demonstração de sincronização...")
    print("-" * 40)
    print("Para sincronizar e detectar problemas, execute:")
    print("python manage_rewards.py sync")
    
    print("\n5️⃣ Comandos úteis via linha de comando...")
    print("-" * 40)
    
    commands = [
        ("Listar recompensas", "python manage_rewards.py list"),
        ("Criar recompensa", 'python manage_rewards.py create "Nome" --cost 100 --audio "files/som.mp3"'),
        ("Remover recompensa", 'python manage_rewards.py remove "Nome"'),
        ("Sincronizar", "python manage_rewards.py sync"),
    ]
    
    for desc, cmd in commands:
        print(f"📋 {desc}:")
        print(f"   {cmd}")
        print()
    
    print("\n6️⃣ Comandos do bot no chat...")
    print("-" * 40)
    
    bot_commands = [
        ("Status do bot", "!status"),
        ("Listar recompensas", "!list_rewards"),
        ("Adicionar recompensa", '!add_reward "Nome" 100 "files/som.mp3"'),
        ("Remover recompensa", '!remove_reward "Nome"'),
        ("Sincronizar", "!sync_rewards"),
    ]
    
    for desc, cmd in bot_commands:
        admin_only = " (admin only)" if cmd != "!status" else ""
        print(f"💬 {desc}{admin_only}:")
        print(f"   {cmd}")
        print()
    
    print("\n✨ Sistema pronto para uso!")
    print("=" * 60)
    print("📖 Consulte GERENCIAMENTO_RECOMPENSAS.md para documentação completa")
    print("🚀 Execute 'python bot.py' para iniciar o bot!")

if __name__ == "__main__":
    main()
