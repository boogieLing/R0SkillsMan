#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH=""
declare -a TARGET_REMOTES=()

usage() {
  cat <<'EOF'
用法:
  sync_all_remotes.sh [--branch <name>] [--remote <name>]...

说明:
  - 默认同步当前分支到全部已配置远端
  - 可通过 --branch 指定分支
  - 可重复使用 --remote，只同步指定远端

示例:
  ./scripts/sync_all_remotes.sh
  ./scripts/sync_all_remotes.sh --branch main
  ./scripts/sync_all_remotes.sh --remote origin --remote github
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      [[ $# -ge 2 ]] || {
        echo "--branch 缺少参数" >&2
        exit 1
      }
      BRANCH="$2"
      shift 2
      ;;
    --remote)
      [[ $# -ge 2 ]] || {
        echo "--remote 缺少参数" >&2
        exit 1
      }
      TARGET_REMOTES+=("$2")
      shift 2
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

if ! git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "当前目录不是 Git 仓库: $ROOT_DIR" >&2
  exit 1
fi

if [[ -z "$BRANCH" ]]; then
  BRANCH="$(git -C "$ROOT_DIR" branch --show-current)"
fi

if [[ -z "$BRANCH" ]]; then
  echo "无法识别当前分支，请使用 --branch 指定。" >&2
  exit 1
fi

if [[ ${#TARGET_REMOTES[@]} -eq 0 ]]; then
  while IFS= read -r remote_name; do
    [[ -n "$remote_name" ]] || continue
    TARGET_REMOTES+=("$remote_name")
  done < <(git -C "$ROOT_DIR" remote)
fi

if [[ ${#TARGET_REMOTES[@]} -eq 0 ]]; then
  echo "未找到任何 Git 远端。" >&2
  exit 1
fi

echo "准备同步分支: $BRANCH"
echo "目标远端: ${TARGET_REMOTES[*]}"

for remote_name in "${TARGET_REMOTES[@]}"; do
  if ! git -C "$ROOT_DIR" remote get-url "$remote_name" >/dev/null 2>&1; then
    echo "远端不存在: $remote_name" >&2
    exit 1
  fi

  echo "推送到远端: $remote_name"
  git -C "$ROOT_DIR" push "$remote_name" "$BRANCH"
done

echo "全部远端同步完成。"
