@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0"
title Chat Parade
cls
echo ======================================================
echo 🎉 Chat Parade
echo ======================================================
echo.

rem Uso: run.bat            instala o que faltar, confere a Twitch e inicia
rem      run.bat setup      refaz a conexao com a Twitch antes de iniciar

rem --- 1. Python 3.10+ -------------------------------------------------------
set "PYTHON="
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PYTHON=py -3"
)
if not defined PYTHON goto :no_python

rem --- 2. Ambiente isolado em .venv (nao mexe no Python do sistema) ----------
set "VENV_PY=.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
    "%VENV_PY%" -c "import sys" >nul 2>&1 || rmdir /s /q .venv
)
if not exist "%VENV_PY%" (
    echo ⏳ Preparando tudo pela primeira vez, pode levar alguns minutos...
    %PYTHON% -m venv .venv
    if errorlevel 1 goto :venv_failed
)

rem --- 3. Dependencias: so reinstala quando o requirements.txt muda ----------
fc /b requirements.txt .venv\requirements.installed >nul 2>&1
if errorlevel 1 (
    echo ⏳ Instalando dependencias...
    "%VENV_PY%" -m pip install -r requirements.txt --quiet --disable-pip-version-check
    if errorlevel 1 goto :pip_failed
    copy /y requirements.txt .venv\requirements.installed >nul
    echo ✅ Dependencias instaladas.
    echo.
)

rem --- 4. Conexao com a Twitch -----------------------------------------------
if /i "%~1"=="setup" goto :setup

echo 🔎 Conferindo a conexao com a Twitch...
"%VENV_PY%" -m chat_parade.check_setup
if errorlevel 3 goto :already_running
if errorlevel 2 goto :run
if errorlevel 1 goto :setup
goto :run

:setup
echo.
"%VENV_PY%" -m chat_parade.oauth_setup
if errorlevel 1 goto :setup_failed
echo.
"%VENV_PY%" -m chat_parade.check_setup
if errorlevel 3 goto :already_running
if errorlevel 2 goto :run
if errorlevel 1 goto :setup_failed

rem --- 5. Inicia -------------------------------------------------------------
:run
echo.
echo ======================================================
echo 🚀 Iniciando o chat-parade. Feche esta janela pra encerrar.
echo ======================================================
echo.
"%VENV_PY%" -m chat_parade.main
echo.
echo ⚠️  O chat-parade foi encerrado.
echo.
pause
exit /b 0

rem --- Problemas -------------------------------------------------------------
:no_python
echo ❌ O Python 3.10 ou mais novo nao foi encontrado neste computador.
echo.
where winget >nul 2>&1
if errorlevel 1 goto :python_manual
choice /c SN /m "Quer instalar o Python agora pelo winget"
if errorlevel 2 goto :python_manual
winget install -e --id Python.Python.3.12
if errorlevel 1 goto :python_manual
echo.
echo ✅ Python instalado. Feche esta janela e abra o run.bat de novo.
echo.
pause
exit /b 0

:python_manual
echo.
echo 📌 Baixe o Python em https://www.python.org/downloads/ - abrindo no navegador...
echo    IMPORTANTE: na primeira tela do instalador, marque "Add python.exe to PATH".
echo    Depois de instalar, abra o run.bat de novo.
start "" https://www.python.org/downloads/
echo.
pause
exit /b 1

:venv_failed
echo.
echo ❌ Nao deu pra criar o ambiente do chat-parade na pasta .venv.
echo    Reinstale o Python pelo python.org e abra o run.bat de novo.
echo.
pause
exit /b 1

:pip_failed
echo.
echo ❌ Falha ao instalar as dependencias. Confira a internet e abra o run.bat de novo.
echo.
pause
exit /b 1

:setup_failed
echo.
echo ❌ A conexao com a Twitch nao foi concluida. Abra o run.bat de novo pra tentar outra vez.
echo.
pause
exit /b 1

:already_running
echo.
pause
exit /b 1
