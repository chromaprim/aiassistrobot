#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null 2>&1; then
  echo '需要 Python 3.9+。Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y python3'
  exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
  echo '需要 Docker Engine。Ubuntu/Debian 可运行 sudo bash install-docker.sh。'
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo '需要 Docker Compose v2，请按 docs/INSTALL_LINUX.md 补齐。'
  exit 1
fi
exec python3 -u manage.py setup "$@"
