#!/usr/bin/env bash
# Единая сборка Infinity Xray. Ничего не устанавливает на ноды.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$HERE/build.py" "$@"
