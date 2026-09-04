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

python -c "import sys; from pathlib import Path; from chat_parade.config import env_is_complete; sys.exit(0 if env_is_complete(Path('.env')) else 1)"
if not errorlevel 1 (
    echo ✅ Arquivo .env ja existe e completo, usando as credenciais atuais.
    goto :run
)

echo ⚠️  .env ausente ou incompleto. Iniciando configuracao...
echo.
python -m chat_parade.oauth_setup
python -c "import sys; from pathlib import Path; from chat_parade.config import env_is_complete; sys.exit(0 if env_is_complete(Path('.env')) else 1)"
if errorlevel 1 (
    echo.
    echo ❌ Configuracao nao foi concluida, .env continua incompleto.
    pause
    exit /b 1
)

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
