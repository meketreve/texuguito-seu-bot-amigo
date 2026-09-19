#!/usr/bin/env bash
# Inicia o Texuguito no Linux/Mac, instalando o que faltar.
#
# Uso: ./run.sh          instala o que faltar, confere a Twitch e inicia
#      ./run.sh setup    refaz a conexão com a Twitch antes de iniciar
#      ./run.sh test     roda a suíte de testes e sai
#
# Equivalente ao run.bat do Windows.
set -u

cd "$(dirname "$0")" || exit 1

VENV_PY=".venv/bin/python"
STAMP=".venv/requirements.installed"

say() { printf '%s\n' "$*"; }

fail() {
    say ""
    say "❌ $*"
    say ""
    exit 1
}

say "======================================================"
say "🎉 Texuguito"
say "======================================================"
say ""

# --- 1. Python 3.10+ ---------------------------------------------------------
PYTHON=""
for candidate in python3 python python3.13 python3.12 python3.11 python3.10; do
    if command -v "$candidate" > /dev/null 2>&1 \
        && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' > /dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    say "❌ O Python 3.10 ou mais novo não foi encontrado neste computador."
    say ""
    if command -v apt > /dev/null 2>&1; then
        say "📌 Instale com:  sudo apt install python3 python3-venv"
    elif command -v dnf > /dev/null 2>&1; then
        say "📌 Instale com:  sudo dnf install python3"
    elif command -v pacman > /dev/null 2>&1; then
        say "📌 Instale com:  sudo pacman -S python"
    elif command -v zypper > /dev/null 2>&1; then
        say "📌 Instale com:  sudo zypper install python3"
    elif command -v brew > /dev/null 2>&1; then
        say "📌 Instale com:  brew install python"
    else
        say "📌 Baixe o Python em https://www.python.org/downloads/"
    fi
    say "   Depois de instalar, rode o ./run.sh de novo."
    say ""
    exit 1
fi

# --- 2. Ambiente isolado em .venv (não mexe no Python do sistema) ------------
if [ -x "$VENV_PY" ] && ! "$VENV_PY" -c 'import sys' > /dev/null 2>&1; then
    say "⚠️  A pasta .venv está quebrada; refazendo..."
    rm -rf .venv
fi

if [ ! -x "$VENV_PY" ]; then
    say "⏳ Preparando tudo pela primeira vez, pode levar alguns minutos..."
    if ! "$PYTHON" -m venv .venv; then
        rm -rf .venv
        say ""
        say "❌ Não deu pra criar o ambiente do Texuguito na pasta .venv."
        if command -v apt > /dev/null 2>&1; then
            say "   No Debian/Ubuntu costuma faltar o pacote do venv:"
            say "   sudo apt install python3-venv"
        fi
        say ""
        exit 1
    fi
fi

# --- 3. Dependências: só reinstala quando o requirements.txt muda ------------
if ! cmp -s requirements.txt "$STAMP"; then
    say "⏳ Instalando dependências..."
    "$VENV_PY" -m pip install -r requirements.txt --quiet --disable-pip-version-check \
        || fail "Falha ao instalar as dependências. Confira a internet e rode o ./run.sh de novo."
    cp requirements.txt "$STAMP"
    say "✅ Dependências instaladas."
    say ""
fi

# --- 3b. Atalho: ./run.sh test ----------------------------------------------
if [ "${1:-}" = "test" ]; then
    exec "$VENV_PY" -m pytest
fi

# --- 4. Conexão com a Twitch -------------------------------------------------
run_setup() {
    say ""
    "$VENV_PY" -m texuguito.oauth_setup \
        || fail "A conexão com a Twitch não foi concluída. Rode o ./run.sh de novo pra tentar outra vez."
    say ""
    "$VENV_PY" -m texuguito.check_setup
    case $? in
        0 | 2) ;;
        3) exit 1 ;;
        *) fail "A conexão com a Twitch não foi concluída. Rode o ./run.sh de novo pra tentar outra vez." ;;
    esac
}

if [ "${1:-}" = "setup" ]; then
    run_setup
else
    say "🔎 Conferindo a conexão com a Twitch..."
    "$VENV_PY" -m texuguito.check_setup
    case $? in
        0 | 2) ;;          # ok, ou sem internet: inicia mesmo assim
        3) exit 1 ;;       # porta ocupada: já está aberto em outra janela
        *) run_setup ;;    # precisa configurar
    esac
fi

# --- 5. Inicia ---------------------------------------------------------------
say ""
say "======================================================"
say "🚀 Iniciando o Texuguito. Aperte Ctrl+C pra encerrar."
say "======================================================"
say ""
exec "$VENV_PY" -m texuguito.main
