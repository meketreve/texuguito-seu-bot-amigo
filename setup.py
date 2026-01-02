import json
import requests
import webbrowser
import os
<<<<<<< HEAD
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Configurações
REDIRECT_PORT = 3000
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"

# Variáveis globais para capturar o código
auth_code = None
auth_state = None
server_should_stop = False

class OAuthHandler(BaseHTTPRequestHandler):
    """Handler para capturar o callback OAuth"""
    
    def do_GET(self):
        global auth_code, auth_state, server_should_stop
        
        # Parse da URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            auth_state = params.get('state', [None])[0]
            
            # Resposta de sucesso
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write("""
            <html>
            <head><title>Texuguito - Autorizacao</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px; background: #1a1a2e; color: white;">
                <h1>✅ Autorização concluída!</h1>
                <p>Você pode fechar esta janela e voltar ao terminal.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
            </body>
            </html>
            """.encode('utf-8'))
            server_should_stop = True
        else:
            # Erro
            error = params.get('error', ['Erro desconhecido'])[0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"""
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px; background: #2d1b1b; color: white;">
                <h1>❌ Erro na autorização</h1>
                <p>{error}</p>
            </body>
            </html>
            """.encode('utf-8'))
            server_should_stop = True
    
    def log_message(self, format, *args):
        pass  # Silencia logs do servidor

def main():
    global auth_code, auth_state, server_should_stop
    
    print("=" * 50)
    print("🦡 Texuguito - Configuração Inicial")
    print("=" * 50)
    print()
    print("📋 Instruções:")
    print("1. Acesse: https://dev.twitch.tv/console/apps")
    print("2. Crie um novo app ou use um existente")
    print(f"3. Adicione '{REDIRECT_URI}' nas URLs de redirecionamento OAuth")
    print()
    
    CLIENT_ID = input("📝 Digite seu CLIENT_ID: ").strip()
    CLIENT_SECRET = input("📝 Digite seu CLIENT_SECRET: ").strip()
    CHANNEL = input("📺 Digite o nome do seu canal: ").strip().lower()
    
    if not CLIENT_ID or not CLIENT_SECRET or not CHANNEL:
        print("❌ Todos os campos são obrigatórios!")
        return
    
    # Gera state para segurança CSRF
    state = secrets.token_urlsafe(16)
    
    # URL de autorização - Todos os escopos comuns
    scopes = " ".join([
        "channel:read:redemptions",
        "channel:manage:redemptions",
        "chat:read",
        "chat:edit",
        "user:read:chat",
        "user:write:chat",
        "user:bot",
        "channel:bot",
        "moderator:read:chatters",
        "bits:read",
        "channel:read:subscriptions",
    ])
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scopes}"
        f"&state={state}"
    )
    
    # Inicia servidor local
    print()
    print(f"🌐 Iniciando servidor local na porta {REDIRECT_PORT}...")
    server = HTTPServer(('localhost', REDIRECT_PORT), OAuthHandler)
    server.timeout = 1
    
    # Abre navegador
    print("🔗 Abrindo navegador para autorização...")
    webbrowser.open(auth_url)
    print("⏳ Aguardando autorização... (feche o terminal para cancelar)")
    
    # Aguarda callback
    while not server_should_stop:
        server.handle_request()
    
    server.server_close()
    
    if not auth_code:
        print("❌ Não foi possível obter o código de autorização.")
        return
    
    # Verifica state
    if auth_state != state:
        print("⚠️ Aviso: State não corresponde (possível CSRF)")
    
    print()
    print("✅ Código recebido! Obtendo tokens...")
    
    # Troca código por tokens
    token_url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    
    try:
        response = requests.post(token_url, data=payload, timeout=10)
        token_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return
    
    if "access_token" not in token_data:
        print(f"❌ Erro ao obter token: {token_data.get('message', token_data)}")
        return
    
    TOKEN = token_data["access_token"]
    REFRESH_TOKEN = token_data.get("refresh_token", "")
    
    print("✅ Token obtido com sucesso!")
    
    # Obtém ID do canal
    print("🔄 Obtendo ID do canal...")
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {TOKEN}"
    }
    
    try:
        user_response = requests.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            timeout=10
        ).json()
        BROADCASTER_ID = user_response["data"][0]["id"]
        print(f"✅ ID do canal: {BROADCASTER_ID}")
    except (requests.exceptions.RequestException, KeyError, IndexError) as e:
        print(f"❌ Erro ao obter ID: {e}")
        return
    
    # Salva .env
    print()
    print("💾 Salvando configurações...")
    with open(".env", "w") as f:
        f.write(f"CLIENT_ID={CLIENT_ID}\n")
        f.write(f"CLIENT_SECRET={CLIENT_SECRET}\n")
        f.write(f"TOKEN={TOKEN}\n")
        f.write(f"REFRESH_TOKEN={REFRESH_TOKEN}\n")
        f.write(f"BROADCASTER_ID={BROADCASTER_ID}\n")
        f.write(f"CHANNEL={CHANNEL}\n")
    
    # Cria config.json se não existir
    if not os.path.exists("config.json"):
        print("📁 Criando config.json...")
        config = {
            "recompensas": {
                "exemplo": "files/audio10/exemplo.mp3"
            }
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    print()
    print("=" * 50)
    print("🎉 Configuração concluída!")
    print("=" * 50)
    print()
    print("📌 Próximos passos:")
    print("1. Edite config.json para mapear suas recompensas")
    print("2. Execute: python bot.py (ou run.bat)")
    print()
    print("Bom streaming! 🦡")

if __name__ == "__main__":
    main()
    input("\nPressione Enter para sair...")
=======
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
>>>>>>> 15c8251eb3496dfa0aece22efad0b288d44b94ab
