#!/usr/bin/env bash
set -euo pipefail

# One-click dev: start backend (FastAPI) and frontend (Vite) together
# - Creates Python venv under backend-v2/.venv if missing
# - Installs backend/ frontend deps when needed
# - Exposes env vars with sensible defaults for local dev
# - Gracefully cleans up on exit

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
BACKEND_DIR="$ROOT_DIR/backend-v2"
FRONTEND_DIR="$ROOT_DIR/frontend-v2"
VENV_DIR="$BACKEND_DIR/.venv"

# Defaults (can be overridden via env)
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
CORS_ORIGINS="${CORS_ORIGINS:-http://127.0.0.1:5173,http://localhost:5173}"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:${API_PORT}}"

# Colors
c_green="\033[32m"; c_yellow="\033[33m"; c_cyan="\033[36m"; c_reset="\033[0m"

echo -e "${c_cyan}==> J-Traders dev start (backend + frontend)${c_reset}"

echo -e "${c_yellow}API_HOST=${API_HOST} API_PORT=${API_PORT} LOG_LEVEL=${LOG_LEVEL}${c_reset}"
echo -e "${c_yellow}CORS_ORIGINS=${CORS_ORIGINS}${c_reset}"
echo -e "${c_yellow}VITE_API_BASE_URL=${VITE_API_BASE_URL}${c_reset}"

ensure_python_venv() {
  if command -v python3 >/dev/null 2>&1; then
    if [ ! -d "$VENV_DIR" ]; then
      echo -e "${c_cyan}[*] Creating Python venv at ${VENV_DIR}${c_reset}"
      python3 -m venv "$VENV_DIR" || {
        echo -e "${c_yellow}[!] Failed to create venv; continuing without venv (using system Python/pip)${c_reset}"
        return 0
      }
    fi
    # shellcheck disable=SC1091
    [ -f "$VENV_DIR/bin/activate" ] && source "$VENV_DIR/bin/activate"
  else
    echo -e "${c_yellow}[!] python3 not found; skipping venv step${c_reset}"
  fi
}

start_backend() {
  echo -e "${c_cyan}[*] Installing backend deps${c_reset}"
  if command -v pip >/dev/null 2>&1; then
    pip install -U pip setuptools wheel >/dev/null 2>&1 || true
    pip install -r "$BACKEND_DIR/requirements.txt"
  elif command -v pip3 >/dev/null 2>&1; then
    pip3 install -U pip setuptools wheel >/dev/null 2>&1 || true
    pip3 install -r "$BACKEND_DIR/requirements.txt"
  else
    echo -e "${c_yellow}[!] pip not found; assuming deps already available${c_reset}"
  fi

  echo -e "${c_cyan}[*] Starting backend: http://${API_HOST}:${API_PORT}${c_reset}"
  ( \
    cd "$BACKEND_DIR" && \
    # Load backend-v2/.env if present, so TUSHARE_TOKEN and others are available for dev
    if [ -f .env ]; then set -a; source .env; set +a; fi; \
    export API_HOST="$API_HOST" API_PORT="$API_PORT" LOG_LEVEL="$LOG_LEVEL" CORS_ORIGINS="$CORS_ORIGINS" && \
    exec uvicorn app.main:app \
      --host "$API_HOST" --port "$API_PORT" --reload \
      --reload-dir . \
  ) &
  BACKEND_PID=$!
}

start_frontend() {
  if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${c_yellow}[!] frontend-v2 not found. Please scaffold it first.${c_reset}"
    return 1
  fi

  echo -e "${c_cyan}[*] Installing frontend deps${c_reset}"
  (cd "$FRONTEND_DIR" && npm i --silent)

  echo -e "${c_cyan}[*] Starting frontend (Vite) on http://127.0.0.1:5173${c_reset}"
  ( \
    cd "$FRONTEND_DIR" && \
    export VITE_API_BASE_URL="$VITE_API_BASE_URL" && \
    exec npm run dev -- --host \
  ) &
  FRONTEND_PID=$!
}

cleanup() {
  echo -e "\n${c_cyan}[*] Shutting down...${c_reset}"
  [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID"  >/dev/null 2>&1 || true
  wait >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

ensure_python_venv
start_backend
start_frontend

# Summary
echo -e "${c_green}Backend:${c_reset} http://${API_HOST}:${API_PORT}    (docs: http://${API_HOST}:${API_PORT}/docs)"
echo -e "${c_green}Frontend:${c_reset} http://127.0.0.1:5173"

echo -e "${c_cyan}[*] Press Ctrl+C to stop both.${c_reset}"

# Wait for either process to exit
wait -n || true
