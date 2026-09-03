@echo off
chcp 65001 > nul
cd /d "%~dp0"
cls
echo ======================================================
echo 🦡 Texuguito Bot - Instalando, configurando e iniciando
echo ======================================================
echo.

echo ⏳ Instalando dependencias...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo ❌ ERRO na instalacao das dependencias!
    echo 📌 Leia as mensagens acima. Se o erro for do pygame, use Python 3.13 ou 3.12.
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

echo ⚠️  Nenhum .env encontrado. Iniciando assistente de configuracao...
echo 💡 Siga as instrucoes no navegador que sera aberto.
echo.
python setup.py
if not exist ".env" (
    echo.
    echo ❌ Configuracao nao foi concluida, .env nao foi criado.
    pause
    exit /b 1
)

:run
echo ======================================================
echo 🦡 Texuguito Bot - Iniciando...
echo ======================================================
echo.
python bot.py
echo.
echo ======================================================
echo ⚠️  O bot foi encerrado.
echo ======================================================
echo.
pause
