import json
import requests
import webbrowser
import os
from pathlib import Path

def print_header():
    """Exibe cabeçalho do setup"""
    print("="*60)
    print("🦡 TEXUGUITO BOT - CONFIGURAÇÃO INICIAL")
    print("="*60)
    print()

def print_instructions():
    """Exibe instruções de configuração"""
    print("📋 MÉTODO SIMPLIFICADO:")
    print()
    print("1️⃣ O site será aberto com os scopes já pré-selecionados")
    print("2️⃣ Cole seu Client ID (do https://dev.twitch.tv/console/apps)")
    print("3️⃣ ✅ Scopes necessários já estarão marcados automaticamente")
    print("4️⃣ Clique em 'Generate Token!'")
    print("5️⃣ Copie o Access Token e Client ID gerados")
    print()
    print("⚠️  IMPORTANTE: Você precisará do TOKEN e CLIENT_ID gerados pelo site!")
    print("-"*60)
    print()

def validate_input(value, field_name):
    """Valida entrada do usuário"""
    if not value or not value.strip():
        print(f"❌ {field_name} não pode estar vazio!")
        return False
    return True

def check_existing_config():
    """Verifica se já existe configuração"""
    if Path(".env").exists():
        print("⚠️  Arquivo .env já existe!")
        choice = input("Deseja sobrescrever a configuração existente? (s/N): ").strip().lower()
        if choice not in ['s', 'sim', 'y', 'yes']:
            print("❌ Configuração cancelada.")
            return False
        print("💾 Criando backup da configuração existente...")
        try:
            backup_name = ".env.backup"
            Path(".env").rename(backup_name)
            print(f"✅ Backup salvo como: {backup_name}")
        except Exception as e:
            print(f"⚠️  Não foi possível criar backup: {e}")
    return True

# Início do script
print_header()

if not check_existing_config():
    exit(0)

print_instructions()

print("🔗 Abrindo https://twitchtokengenerator.com com scopes pré-selecionados...")
try:
    webbrowser.open("https://twitchtokengenerator.com/?code=y0piiclp4zczva3u6nzs8jnsim4w8f&scope=chat%3Aread+chat%3Aedit+channel%3Aread%3Aredemptions+channel%3Amanage%3Aredemptions")
except Exception as e:
    print(f"⚠️  Não foi possível abrir o navegador: {e}")

print("\n" + "="*60)
print("🎯 GERAÇÃO DE TOKEN")
print("="*60)
print("📝 INSTRUÇÕES NO SITE:")
print("1. Cole seu Client ID (do https://dev.twitch.tv/console/apps)")
print("2. ✅ Os scopes necessários já estão pré-selecionados!")
print("3. Clique em 'Generate Token!'")
print("4. Copie o ACCESS TOKEN gerado")
print("5. Copie o CLIENT ID mostrado (pode ser diferente do seu)")
print()

# Coleta o CLIENT_ID gerado pelo site
while True:
    CLIENT_ID = input("🔑 Cole o CLIENT_ID gerado pelo site: ").strip()
    if validate_input(CLIENT_ID, "CLIENT_ID"):
        break

# Coleta o token gerado pelo site
while True:
    TOKEN = input("🔐 Cole o ACCESS TOKEN gerado pelo site: ").strip()
    if validate_input(TOKEN, "ACCESS TOKEN"):
        break

print("\n✅ Dados recebidos com sucesso!")

# Obtém informações do usuário
print("📄 Obtendo informações do canal...")
headers = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {TOKEN}"
}

try:
    user_response = requests.get("https://api.twitch.tv/helix/users", headers=headers, timeout=10)
    user_data = user_response.json()
    
    if "data" in user_data and len(user_data["data"]) > 0:
        user_info = user_data["data"][0]
        BROADCASTER_ID = user_info["id"]
        display_name = user_info["display_name"]
        login = user_info["login"]
        
        print(f"✅ Canal identificado:")
        print(f"   📄 Nome: {display_name}")
        print(f"   🔖 Login: {login}")
        print(f"   🆔 ID: {BROADCASTER_ID}")
    else:
        print("❌ ERRO: Não foi possível obter informações do usuário.")
        print(f"📊 Resposta da API: {user_data}")
        input("\nPressione Enter para sair...")
        exit(1)
except requests.RequestException as e:
    print(f"❌ ERRO ao obter informações do usuário: {e}")
    input("\nPressione Enter para sair...")
    exit(1)

# Salva configuração
print("\n💾 Salvando configuração...")
try:
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"CLIENT_ID={CLIENT_ID}\n")
        f.write(f"TOKEN={TOKEN}\n")
        f.write(f"BROADCASTER_ID={BROADCASTER_ID}\n")
    
    print("✅ Arquivo .env criado com sucesso!")
except Exception as e:
    print(f"❌ ERRO ao salvar arquivo .env: {e}")
    input("\nPressione Enter para sair...")
    exit(1)

# Sucesso!
print("\n" + "="*60)
print("🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
print("="*60)
print("🚀 Próximos passos:")
print("1. python bot.py                    # Executar o bot")
print("2. python manage_rewards.py list    # Gerenciar recompensas")
print("3. python exemplo_uso.py            # Ver exemplos")
print()
print("📝 O bot está pronto para uso! Divirta-se! 🎆")
print("="*60)

input("\nPressione Enter para sair...")
