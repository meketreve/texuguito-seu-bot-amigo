@echo off
chcp 65001 >nul
title Texuguito - Gerenciador de Recompensas

:menu
cls
echo ══════════════════════════════════════════════════════════
echo      🦡 TEXUGUITO - GERENCIADOR DE RECOMPENSAS 🎁
echo ══════════════════════════════════════════════════════════
echo.
echo   [1] Listar recompensas
echo   [2] Criar nova recompensa
echo   [3] Remover recompensa
echo   [4] Sincronizar com Twitch
echo   [5] Executar comando personalizado
echo   [0] Sair
echo.
echo ══════════════════════════════════════════════════════════
echo.

set /p opcao="Escolha uma opcao: "

if "%opcao%"=="1" goto listar
if "%opcao%"=="2" goto criar
if "%opcao%"=="3" goto remover
if "%opcao%"=="4" goto sync
if "%opcao%"=="5" goto personalizado
if "%opcao%"=="0" goto sair
goto menu

:listar
cls
echo 📋 Listando recompensas...
echo.
python manage_rewards.py list
echo.
pause
goto menu

:criar
cls
echo 🎁 CRIAR NOVA RECOMPENSA
echo ════════════════════════
echo.
set /p nome="Nome da recompensa: "
set /p custo="Custo em pontos: "
set /p audio="Caminho do audio (ex: files/audio/som.mp3): "
echo.
echo Criando recompensa "%nome%" por %custo% pontos...
python manage_rewards.py create "%nome%" --cost %custo% --audio "%audio%"
echo.
pause
goto menu

:remover
cls
echo ❌ REMOVER RECOMPENSA
echo ═════════════════════
echo.
set /p nome="Nome da recompensa a remover: "
echo.
echo Removendo "%nome%"...
python manage_rewards.py remove "%nome%"
echo.
pause
goto menu

:sync
cls
echo 🔄 Sincronizando com Twitch...
echo.
python manage_rewards.py sync
echo.
pause
goto menu

:personalizado
cls
echo 💻 COMANDO PERSONALIZADO
echo ════════════════════════
echo.
echo Comandos disponiveis:
echo   list              - Lista todas as recompensas
echo   create "Nome" --cost X --audio "caminho"
echo   remove "Nome"     - Remove uma recompensa
echo   sync              - Sincroniza com a Twitch
echo.
set /p cmd="Digite o comando: python manage_rewards.py "
python manage_rewards.py %cmd%
echo.
pause
goto menu

:sair
echo.
echo 👋 Ate mais!
timeout /t 2 >nul
exit
