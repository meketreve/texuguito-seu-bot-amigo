import json
import requests
import webbrowser
import re

# Configurações iniciais
print("Caso não tenha um app da Twitch pronto, precisa criar um.")
print("Para criar um novo ou ver os dados de um existente, acesse: https://dev.twitch.tv/console/eventsub/subscriptions")
print("Caso crie um novo, use https://twitchtokengenerator.com no campo 'URLs de redirecionamento OAuth'")

CLIENT_ID = input("Digite seu CLIENT_ID da Twitch: ")
CLIENT_SECRET = input("Digite seu CLIENT_SECRET da Twitch: ")
REDIRECT_URI = "https://twitchtokengenerator.com"  # Defina no app da Twitch
AUTH_URL = f"https://id.twitch.tv/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=channel:read:redemptions channel:manage:redemptions"

# Abre a URL de autorização no navegador
print("\nAcesse este link, autorize a aplicação e copie o link gerado:")
print(AUTH_URL)
webbrowser.open(AUTH_URL)

# Solicita o link completo do usuário
full_link = input("\nCole o link completo aqui: ")

# Extrai apenas o código de autorização usando regex
match = re.search(r'code=([^&]+)', full_link)
if match:
    AUTH_CODE = match.group(1)
    print(f"\nCódigo de autorização extraído: {AUTH_CODE}")
else:
    print("\nErro: Código de autorização não encontrado no link.")
    exit()

# Troca o código pelo token OAuth
TOKEN_URL = "https://id.twitch.tv/oauth2/token"
payload = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": AUTH_CODE,
    "grant_type": "authorization_code",
    "redirect_uri": REDIRECT_URI
}
response = requests.post(TOKEN_URL, data=payload)
token_data = response.json()
TOKEN = token_data.get("access_token")

if TOKEN:
    print(f"\nToken OAuth obtido: {TOKEN}")
else:
    print(f"\nErro ao obter token: {token_data}")
    exit()

# Obtém ID do canal
headers = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {TOKEN}"
}
url_user = "https://api.twitch.tv/helix/users"
user_response = requests.get(url_user, headers=headers).json()
BROADCASTER_ID = user_response["data"][0]["id"]

print(f"\nID do canal obtido: {BROADCASTER_ID}")

# Salva tudo no `.env`
with open(".env", "w") as f:
    f.write(f"CLIENT_ID={CLIENT_ID}\n")
    f.write(f"CLIENT_SECRET={CLIENT_SECRET}\n")
    f.write(f"TOKEN={TOKEN}\n")
    f.write(f"BROADCASTER_ID={BROADCASTER_ID}\n")

print("\nConfiguração concluída! Agora rode o bot normalmente.")