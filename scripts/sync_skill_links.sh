#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
WITH_PULL="false"
BACKUP_ROOT=""
SYNC_COUNT=0

usage() {
  cat <<'EOF'
用法:
  sync_skill_links.sh [--pull]

说明:
  - 默认仅重建软链接，不执行 git pull
  - --pull: 先在仓库根目录执行 git pull --ff-only，再同步软链接

可选环境变量:
  CODEX_SKILLS_DIR   覆盖 Codex 目标目录（默认: ~/.codex/skills）
  CLAUDE_SKILLS_DIR  覆盖 Claude 目标目录（默认: ~/.claude/skills）
EOF
}

ensure_link() {
  local src="$1"
  local dst="$2"
  local parent
  parent="$(dirname "$dst")"
  mkdir -p "$parent"

  if [[ -L "$dst" ]]; then
    ln -sfn "$src" "$dst"
    return
  fi

  if [[ -e "$dst" ]]; then
    if [[ -z "$BACKUP_ROOT" ]]; then
      BACKUP_ROOT="$HOME/.skills_link_backup/$(date +%Y%m%d_%H%M%S)"
      mkdir -p "$BACKUP_ROOT"
    fi
    mv "$dst" "$BACKUP_ROOT/$(basename "$dst")"
  fi

  ln -s "$src" "$dst"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      WITH_PULL="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$WITH_PULL" == "true" ]]; then
  git -C "$ROOT_DIR" pull --ff-only
fi

for skill_dir in "$ROOT_DIR"/r0-*; do
  [[ -d "$skill_dir" ]] || continue
  skill_name="$(basename "$skill_dir")"

  ensure_link "$skill_dir" "$CODEX_DIR/$skill_name"
  ensure_link "$skill_dir" "$CLAUDE_DIR/$skill_name"
  SYNC_COUNT=$((SYNC_COUNT + 1))
done

echo "同步完成: $SYNC_COUNT 个 skills"
echo "Codex 目录: $CODEX_DIR"
echo "Claude 目录: $CLAUDE_DIR"
if [[ -n "$BACKUP_ROOT" ]]; then
  echo "备份目录: $BACKUP_ROOT"
fi
