@echo off
chcp 65001 > nul
cd /d "%~dp0"
cls
echo ======================================================
echo 🎉 Chat Parade - Instalando, configurando e iniciando
echo ======================================================
echo.

echo ⏳ Instalando dependencias...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo ❌ ERRO ao instalar as dependencias!
    echo 📌 Confira se o Python 3.10+ esta instalado e no PATH.
    echo.
    pause
    exit /b 1
)
echo ✅ Dependencias instaladas.
echo.

if exist ".env" (
    echo ✅ Arquivo .env ja existe, usando as credenciais atuais.
    goto :run
)

echo ⚠️  Nenhum .env encontrado. Configurando...

set "SIBLING_ENV=%~dp0..\texuguito-seu-bot-amigo\.env"
if exist "%SIBLING_ENV%" (
    echo 🔄 Reaproveitando credenciais do texuguito-seu-bot-amigo...
    python -c "from pathlib import Path; import re; src=Path(r'%SIBLING_ENV%').read_text(encoding='utf-8'); values=dict(re.findall(r'^(\w+)=(.*)$', src, re.MULTILINE)); wanted=['CLIENT_ID','TOKEN','BROADCASTER_ID','CHANNEL']; lines=[f'{k}={values[k]}' for k in wanted if k in values]; lines += ['DATA_DIR=data','OVERLAY_PORT=8901']; Path('.env').write_text(chr(10).join(lines) + chr(10), encoding='utf-8'); print('Copiado:', [k for k in wanted if k in values])"
    if errorlevel 1 (
        echo.
        echo ❌ ERRO ao copiar as credenciais do projeto texuguito.
        pause
        exit /b 1
    )
    echo ✅ .env criado a partir do texuguito-seu-bot-amigo.
    echo.
    goto :run
)

echo 📄 Criando .env a partir do .env.example...
copy /y ".env.example" ".env" > nul
echo.
echo ======================================================
echo ⚠️  Preencha o arquivo .env com suas credenciais da Twitch
echo    antes de rodar este script de novo.
echo    (CLIENT_ID, TOKEN, BROADCASTER_ID, CHANNEL)
echo ======================================================
echo.
pause
exit /b 0

:run
echo ======================================================
echo 🚀 Iniciando o chat-parade...
echo ======================================================
echo.
python -m chat_parade.main
echo.
echo ======================================================
echo ⚠️  O chat-parade foi encerrado.
echo ======================================================
echo.
pause
