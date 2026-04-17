#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${R0_UNINSTALL_TEMP_RUNNER:-}" ]]; then
  TMP_BASE="${TMPDIR:-/tmp}"
  TMP_BASE="${TMP_BASE%/}"
  ORIG_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  TEMP_RUNNER="$(mktemp "$TMP_BASE/uninstall.XXXXXX")"
  cp "$ORIG_SCRIPT" "$TEMP_RUNNER"
  chmod +x "$TEMP_RUNNER"
  exec env R0_UNINSTALL_TEMP_RUNNER=1 bash "$TEMP_RUNNER" "$@"
fi

DEFAULT_REPO_ROOT="${HOME}/.local/share/r0-skills"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
LOCAL_BIN_DIR="${LOCAL_BIN_DIR:-$HOME/.local/bin}"

REPO_ROOT="$DEFAULT_REPO_ROOT"
KEEP_REPO="false"
DRY_RUN="false"
PREFIX=""

declare -a REMOVE_PATHS=()

usage() {
  cat <<'EOF'
用法:
  uninstall.sh [--repo-root <path>] [--keep-repo] [--dry-run]

说明:
  - 默认卸载标准安装路径 ~/.local/share/r0-skills
  - 会清理 Codex / Claude Code 的已安装 skill 软链
  - 会清理固定到 ~/.local/bin/<prefix>push 的 push 工具
  - 默认最后删除仓库目录；如只想移除本地安装入口，可加 --keep-repo

可选环境变量:
  CODEX_SKILLS_DIR   覆盖 Codex 技能安装目录（默认: ~/.codex/skills）
  CLAUDE_SKILLS_DIR  覆盖 Claude 技能安装目录（默认: ~/.claude/skills）
  LOCAL_BIN_DIR      覆盖 push 工具固定目录（默认: ~/.local/bin）
EOF
}

resolve_path() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

print(Path(sys.argv[1]).expanduser().resolve(strict=False))
PY
}

detect_prefix() {
  local repo_root="$1"
  local contract_file skill_dir

  shopt -s nullglob
  for contract_file in "$repo_root"/shared/*-core-contract.md; do
    PREFIX="$(basename "$contract_file")"
    PREFIX="${PREFIX%-core-contract.md}"
    if [[ -n "$PREFIX" ]]; then
      return
    fi
  done

  for skill_dir in "$repo_root"/*-request; do
    [[ -d "$skill_dir" ]] || continue
    PREFIX="$(basename "$skill_dir")"
    PREFIX="${PREFIX%-request}"
    if [[ -n "$PREFIX" ]]; then
      return
    fi
  done

  echo "无法探测当前 skill 前缀: $repo_root" >&2
  exit 1
}

queue_path() {
  local path="$1"
  local existing
  if [[ ${#REMOVE_PATHS[@]} -gt 0 ]]; then
    for existing in "${REMOVE_PATHS[@]}"; do
      if [[ "$existing" == "$path" ]]; then
        return
      fi
    done
  fi
  REMOVE_PATHS+=("$path")
}

print_remove_paths() {
  if [[ ${#REMOVE_PATHS[@]} -eq 0 ]]; then
    echo "link_cleanup=<none>"
    return
  fi
  printf '%s\n' "${REMOVE_PATHS[@]}" | sed 's/^/remove_path=/'
}

run_remove_paths() {
  local path
  if [[ ${#REMOVE_PATHS[@]} -eq 0 ]]; then
    return
  fi
  for path in "${REMOVE_PATHS[@]}"; do
    remove_path "$path"
  done
}

queue_skill_links() {
  local base_dir="$1"
  local repo_root="$2"
  local entry entry_name entry_resolved expected_target

  [[ -d "$base_dir" ]] || return

  while IFS= read -r entry; do
    [[ -n "$entry" ]] || continue
    entry_name="$(basename "$entry")"
    expected_target="$(resolve_path "$repo_root/$entry_name")"
    entry_resolved="$(resolve_path "$entry")"
    if [[ "$entry_resolved" == "$expected_target" ]]; then
      queue_path "$entry"
    fi
  done < <(find "$base_dir" -maxdepth 1 -mindepth 1 -type l -name "${PREFIX}-*" | sort)
}

queue_pinned_push_tool() {
  local repo_root="$1"
  local push_name pinned_push entry_resolved expected_repo_push expected_synced_push

  push_name="${PREFIX}push"
  pinned_push="$LOCAL_BIN_DIR/$push_name"
  [[ -L "$pinned_push" ]] || return

  entry_resolved="$(resolve_path "$pinned_push")"
  expected_repo_push="$(resolve_path "$repo_root/${PREFIX}-submit/scripts/$push_name")"
  expected_synced_push="$(resolve_path "$CODEX_DIR/${PREFIX}-submit/scripts/$push_name")"

  if [[ "$entry_resolved" == "$expected_repo_push" || "$entry_resolved" == "$expected_synced_push" ]]; then
    queue_path "$pinned_push"
  fi
}

assert_safe_repo_root() {
  local repo_root="$1"
  case "$repo_root" in
    ""|"/"|"$HOME"|"$HOME/"|"$HOME/.local"|"$HOME/.local/"|"$HOME/.local/share"|"$HOME/.local/share/")
      echo "拒绝对危险路径执行卸载: $repo_root" >&2
      exit 1
      ;;
  esac
}

remove_path() {
  local path="$1"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "would_remove=$path"
    return
  fi
  rm -rf "$path"
  echo "removed=$path"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      [[ $# -ge 2 ]] || {
        echo "--repo-root 缺少参数" >&2
        exit 1
      }
      REPO_ROOT="$2"
      shift 2
      ;;
    --keep-repo)
      KEEP_REPO="true"
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

REPO_ROOT="$(resolve_path "$REPO_ROOT")"
assert_safe_repo_root "$REPO_ROOT"

if [[ ! -d "$REPO_ROOT" ]]; then
  echo "目标仓库不存在: $REPO_ROOT" >&2
  exit 1
fi
if [[ ! -d "$REPO_ROOT/shared" ]]; then
  echo "目标目录不是 skill 仓库: $REPO_ROOT" >&2
  exit 1
fi

detect_prefix "$REPO_ROOT"
queue_skill_links "$CODEX_DIR" "$REPO_ROOT"
queue_skill_links "$CLAUDE_DIR" "$REPO_ROOT"
queue_pinned_push_tool "$REPO_ROOT"

echo "repo_root=$REPO_ROOT"
echo "prefix=$PREFIX"
echo "codex_dir=$CODEX_DIR"
echo "claude_dir=$CLAUDE_DIR"
echo "local_bin_dir=$LOCAL_BIN_DIR"
echo "keep_repo=$KEEP_REPO"
echo "dry_run=$DRY_RUN"

print_remove_paths
run_remove_paths

if [[ "$KEEP_REPO" == "false" ]]; then
  remove_path "$REPO_ROOT"
else
  echo "kept_repo=$REPO_ROOT"
fi

echo "[OK] uninstall completed."
