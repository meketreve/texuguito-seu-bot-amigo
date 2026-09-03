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

echo ⚠️  Nenhum .env encontrado. Iniciando configuracao...
echo.
python -m chat_parade.oauth_setup
if not exist ".env" (
    echo.
    echo ❌ Configuracao nao foi concluida, .env nao foi criado.
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
