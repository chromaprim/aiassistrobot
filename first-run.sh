#!/usr/bin/env bash
# Logging is implemented by manage.py so hidden Key input keeps its terminal.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec bash setup.sh "$@"
