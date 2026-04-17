#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_REMOTE="github"
DEFAULT_BRANCH="main"
REMOTE="$DEFAULT_REMOTE"
BRANCH="$DEFAULT_BRANCH"
DRY_RUN="false"

declare -a QUICK_START_ARGS=()

has_quick_start_arg() {
  local needle="$1"
  local item
  for item in "${QUICK_START_ARGS[@]}"; do
    if [[ "$item" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

usage() {
  cat <<'EOF'
用法:
  install_and_quick_start.sh [--remote <name>] [--branch <name>] [--name <prefix>] [--allow-dirty] [--allow-partial] [--dry-run]

说明:
  - 一次完成 git 拉取 + quick start
  - 默认远端: github
  - 默认分支: main
  - 远端可选值按当前仓库配置，当前通常为: github / origin / cggame
  - quick start 参数会继续传给 scripts/quick_start.sh

示例:
  ./scripts/install_and_quick_start.sh
  ./scripts/install_and_quick_start.sh --remote origin --name lyn
  ./scripts/install_and_quick_start.sh --remote cggame --branch main --allow-dirty
EOF
}

ensure_remote_exists() {
  if ! git -C "$ROOT_DIR" remote get-url "$REMOTE" >/dev/null 2>&1; then
    echo "远端不存在: $REMOTE" >&2
    echo "可用远端:" >&2
    git -C "$ROOT_DIR" remote >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      [[ $# -ge 2 ]] || {
        echo "--remote 缺少参数" >&2
        exit 1
      }
      REMOTE="$2"
      shift 2
      ;;
    --branch)
      [[ $# -ge 2 ]] || {
        echo "--branch 缺少参数" >&2
        exit 1
      }
      BRANCH="$2"
      shift 2
      ;;
    --name|--allow-dirty|--allow-partial)
      QUICK_START_ARGS+=("$1")
      if [[ "$1" == "--name" ]]; then
        [[ $# -ge 2 ]] || {
          echo "--name 缺少参数" >&2
          exit 1
        }
        QUICK_START_ARGS+=("$2")
        shift 2
      else
        shift
      fi
      ;;
    --dry-run)
      DRY_RUN="true"
      QUICK_START_ARGS+=("--dry-run")
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

ensure_remote_exists

if [[ "$DRY_RUN" == "true" ]]; then
  if ! has_quick_start_arg "--allow-dirty"; then
    QUICK_START_ARGS+=("--allow-dirty")
  fi
  echo "mode=dry-run"
  echo "repo_root=$ROOT_DIR"
  echo "remote=$REMOTE"
  echo "branch=$BRANCH"
  echo "fetch_cmd=git -C $ROOT_DIR fetch --prune $REMOTE $BRANCH"
  echo "pull_cmd=git -C $ROOT_DIR pull --ff-only $REMOTE $BRANCH"
  echo "quick_start_cmd=bash $ROOT_DIR/scripts/quick_start.sh ${QUICK_START_ARGS[*]}"
  bash "$ROOT_DIR/scripts/quick_start.sh" "${QUICK_START_ARGS[@]}"
  exit 0
fi

echo "remote=$REMOTE"
echo "branch=$BRANCH"
git -C "$ROOT_DIR" fetch --prune "$REMOTE" "$BRANCH"
git -C "$ROOT_DIR" pull --ff-only "$REMOTE" "$BRANCH"
bash "$ROOT_DIR/scripts/quick_start.sh" "${QUICK_START_ARGS[@]}"
