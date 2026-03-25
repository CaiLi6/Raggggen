#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLIENT_VENV="$REPO_ROOT/.venv_client"
SERVER_VENV="$REPO_ROOT/.venv_server"

ensure_venv() {
  if [ ! -d "$1" ]; then
    echo "Creating venv: $1"
    python3 -m venv "$1"
  else
    echo "Venv exists: $1"
  fi
}

ensure_venv "$CLIENT_VENV"
ensure_venv "$SERVER_VENV"

if [ "${NO_INSTALL:-}" != "1" ]; then
  echo "Installing client dependencies..."
  source "$CLIENT_VENV/bin/activate"
  pip install --upgrade pip
  pip install -r "$REPO_ROOT/Financial-Agent-Client/requirements.txt"
  deactivate

  echo "Installing server package into server venv..."
  source "$SERVER_VENV/bin/activate"
  pip install --upgrade pip
  pip install -e "$REPO_ROOT/MODULAR-RAG-MCP-SERVER"
  deactivate
fi

echo "Starting RAG Server..."
"$SERVER_VENV/bin/python" "$REPO_ROOT/MODULAR-RAG-MCP-SERVER/main.py" &
SERVER_PID=$!

sleep 0.5

echo "Starting Client..."
"$CLIENT_VENV/bin/python" "$REPO_ROOT/Financial-Agent-Client/run_app.py" &
CLIENT_PID=$!

echo "Server PID: $SERVER_PID"
echo "Client PID: $CLIENT_PID"

echo "To stop: kill $SERVER_PID $CLIENT_PID"
