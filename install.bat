@echo off
chcp 65001 > nul
cls
echo ======================================================
echo 🦡 Texuguito Bot - Instalador de Dependências
echo ======================================================
echo.
echo ⏳ Instalando bibliotecas necessárias...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo ✅ Instalação concluída com sucesso!
echo 📌 Agora você pode rodar o setup.bat ou o run.bat.
echo.
pause