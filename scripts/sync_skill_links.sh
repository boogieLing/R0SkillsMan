#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
WITH_PULL="false"
ALLOW_PARTIAL="false"
BACKUP_ROOT=""
SYNC_COUNT=0
declare -a SKILL_DIRS=()

usage() {
  cat <<'EOF'
用法:
  sync_skill_links.sh [--pull] [--allow-partial]

说明:
  - 默认仅重建软链接，不执行 git pull
  - --pull: 先在仓库根目录执行 git pull --ff-only，再同步软链接
  - 若检测到当前仓库只包含部分 r0-* skills，脚本会默认阻断，避免把已有链接切到错误来源
  - --allow-partial: 明确允许在部分技能镜像上执行，仅建议在你确认目标行为时使用

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

collect_skill_dirs() {
  local skill_dir
  SKILL_DIRS=()
  for skill_dir in "$ROOT_DIR"/r0-*; do
    [[ -d "$skill_dir" ]] || continue
    SKILL_DIRS+=("$skill_dir")
  done
}

count_existing_skill_links() {
  local base_dir="$1"
  [[ -d "$base_dir" ]] || return 0
  find "$base_dir" -maxdepth 1 -mindepth 1 -name 'r0-*' | wc -l | tr -d ' '
}

assert_safe_source_layout() {
  local current_count="$1"
  local codex_count claude_count existing_max

  if [[ "$current_count" -eq 0 ]]; then
    echo "未找到任何 r0-* skill 目录: $ROOT_DIR" >&2
    exit 1
  fi

  if [[ "$ALLOW_PARTIAL" == "true" ]]; then
    return
  fi

  codex_count="$(count_existing_skill_links "$CODEX_DIR")"
  claude_count="$(count_existing_skill_links "$CLAUDE_DIR")"
  existing_max="$codex_count"
  if (( claude_count > existing_max )); then
    existing_max="$claude_count"
  fi

  if (( existing_max > current_count )); then
    echo "检测到当前仓库仅含 $current_count 个 r0-* 目录，但目标技能根目录已有更多技能。" >&2
    echo "为避免把现有软链接切到不完整来源，默认停止同步。" >&2
    echo "ROOT_DIR=$ROOT_DIR" >&2
    echo "CODEX_DIR=$CODEX_DIR (count=$codex_count)" >&2
    echo "CLAUDE_DIR=$CLAUDE_DIR (count=$claude_count)" >&2
    echo "如确认只想同步当前这部分技能，请显式添加 --allow-partial。" >&2
    exit 2
  fi
}

assert_skill_entrypoints() {
  local skill_dir
  local -a missing=()

  for skill_dir in "${SKILL_DIRS[@]}"; do
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
      missing+=("$(basename "$skill_dir")")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "以下 r0-* 目录缺少 SKILL.md，停止同步：" >&2
    printf ' - %s\n' "${missing[@]}" >&2
    exit 3
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      WITH_PULL="true"
      shift
      ;;
    --allow-partial)
      ALLOW_PARTIAL="true"
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

collect_skill_dirs
assert_safe_source_layout "${#SKILL_DIRS[@]}"
assert_skill_entrypoints

for skill_dir in "${SKILL_DIRS[@]}"; do
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
