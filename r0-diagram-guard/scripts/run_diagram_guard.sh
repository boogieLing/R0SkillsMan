#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/diagram_guard.py"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <article-dir> [--mode check|fix|gate-fix] [--drop-unfixable-refs]" >&2
  exit 1
fi

ARTICLE_DIR="$1"
shift || true

exec "$PY_SCRIPT" --article-dir "$ARTICLE_DIR" "$@"
