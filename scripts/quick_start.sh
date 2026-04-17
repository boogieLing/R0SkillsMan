#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${R0_TEMP_RUNNER:-}" ]]; then
  TMP_BASE="${TMPDIR:-/tmp}"
  TMP_BASE="${TMP_BASE%/}"
  ORIG_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  ORIG_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  TEMP_RUNNER="$(mktemp "$TMP_BASE/quick_start.XXXXXX")"
  cp "$ORIG_SCRIPT" "$TEMP_RUNNER"
  chmod +x "$TEMP_RUNNER"
  exec env R0_TEMP_RUNNER=1 R0_ROOT_DIR="$ORIG_ROOT_DIR" bash "$TEMP_RUNNER" "$@"
fi

ROOT_DIR="${R0_ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
LOCAL_BIN_DIR="${LOCAL_BIN_DIR:-$HOME/.local/bin}"
ALLOW_PARTIAL="false"
ALLOW_DIRTY="false"
WITH_PULL="false"
DRY_RUN="false"
NAME=""
BACKUP_ROOT=""

usage() {
  cat <<'EOF'
用法:
  quick_start.sh [--name <prefix>] [--pull] [--allow-dirty] [--allow-partial] [--dry-run]

说明:
  - 一次完成命名初始化、r0push 固定、skill 同步与链接校验
  - 默认前缀回退链：--name -> git user.name -> git user.email local-part -> ouo
  - 默认会阻断 dirty worktree；如确认要继续，请显式传 --allow-dirty

可选环境变量:
  CODEX_SKILLS_DIR   覆盖 Codex 技能安装目录（默认: ~/.codex/skills）
  CLAUDE_SKILLS_DIR  覆盖 Claude 技能安装目录（默认: ~/.claude/skills）
  LOCAL_BIN_DIR      覆盖 push 工具固定目录（默认: ~/.local/bin）
EOF
}

ensure_link() {
  local src="$1"
  local dst="$2"
  local parent current_target=""
  parent="$(dirname "$dst")"
  mkdir -p "$parent"

  if [[ -L "$dst" ]]; then
    current_target="$(readlink "$dst")"
    if [[ "$current_target" == "$src" ]]; then
      return
    fi
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

parse_key() {
  local key="$1"
  local text="$2"
  printf '%s\n' "$text" | sed -n "s/^${key}=//p" | head -n 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      NAME="${2:-}"
      if [[ -z "$NAME" ]]; then
        echo "缺少 --name 的参数值" >&2
        exit 1
      fi
      shift 2
      ;;
    --pull)
      WITH_PULL="true"
      shift
      ;;
    --allow-dirty)
      ALLOW_DIRTY="true"
      shift
      ;;
    --allow-partial)
      ALLOW_PARTIAL="true"
      shift
      ;;
    --dry-run)
      DRY_RUN="true"
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

declare -a INIT_CMD=("python3" "$ROOT_DIR/scripts/init_skill_namespace.py" "--repo-root" "$ROOT_DIR")
if [[ -n "$NAME" ]]; then
  INIT_CMD+=("--name" "$NAME")
fi
if [[ "$ALLOW_DIRTY" == "true" ]]; then
  INIT_CMD+=("--allow-dirty")
fi
if [[ "$DRY_RUN" == "true" ]]; then
  INIT_CMD+=("--dry-run")
fi

INIT_OUTPUT_FILE="$(mktemp)"
"${INIT_CMD[@]}" >"$INIT_OUTPUT_FILE"
INIT_OUTPUT="$(cat "$INIT_OUTPUT_FILE")"
rm -f "$INIT_OUTPUT_FILE"
printf '%s\n' "$INIT_OUTPUT"

TARGET_PREFIX="$(parse_key "target_prefix" "$INIT_OUTPUT")"
if [[ -z "$TARGET_PREFIX" ]]; then
  echo "未从 init_skill_namespace.py 输出中解析到 target_prefix" >&2
  exit 1
fi

PUSH_TOOL_NAME="${TARGET_PREFIX}push"
SYNCED_PUSH_TOOL="$CODEX_DIR/${TARGET_PREFIX}-submit/scripts/${PUSH_TOOL_NAME}"
PINNED_PUSH_TOOL="$LOCAL_BIN_DIR/${PUSH_TOOL_NAME}"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "planned_codex_dir=$CODEX_DIR"
  echo "planned_claude_dir=$CLAUDE_DIR"
  echo "planned_synced_push_tool=$SYNCED_PUSH_TOOL"
  echo "planned_pinned_push_tool=$PINNED_PUSH_TOOL"
  exit 0
fi

declare -a SYNC_CMD=("bash" "$ROOT_DIR/scripts/sync_skill_links.sh")
if [[ "$ALLOW_PARTIAL" == "true" ]]; then
  SYNC_CMD+=("--allow-partial")
fi
"${SYNC_CMD[@]}"

bash "$ROOT_DIR/scripts/check_skill_links.sh"

if [[ ! -x "$SYNCED_PUSH_TOOL" ]]; then
  echo "未找到可执行 push 工具: $SYNCED_PUSH_TOOL" >&2
  exit 1
fi

ensure_link "$SYNCED_PUSH_TOOL" "$PINNED_PUSH_TOOL"

echo "target_prefix=$TARGET_PREFIX"
echo "pinned_push_tool=$PINNED_PUSH_TOOL"
echo "synced_push_tool=$SYNCED_PUSH_TOOL"
echo "codex_dir=$CODEX_DIR"
echo "claude_dir=$CLAUDE_DIR"
if [[ -n "$BACKUP_ROOT" ]]; then
  echo "backup_dir=$BACKUP_ROOT"
fi
echo "[OK] quick start completed."
