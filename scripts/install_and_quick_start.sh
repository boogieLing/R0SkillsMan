#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${R0_INSTALL_TEMP_RUNNER:-}" ]]; then
  TMP_BASE="${TMPDIR:-/tmp}"
  TMP_BASE="${TMP_BASE%/}"
  ORIG_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  TEMP_RUNNER="$(mktemp "$TMP_BASE/install_and_quick_start.XXXXXX")"
  cp "$ORIG_SCRIPT" "$TEMP_RUNNER"
  chmod +x "$TEMP_RUNNER"
  exec env R0_INSTALL_TEMP_RUNNER=1 bash "$TEMP_RUNNER" "$@"
fi

DEFAULT_REMOTE="github"
DEFAULT_BRANCH="main"
DEFAULT_REPO_NAME="r0-skills"
DEFAULT_INSTALL_BASE="${HOME}/.local/share"

REMOTE="$DEFAULT_REMOTE"
BRANCH="$DEFAULT_BRANCH"
REPO_NAME="$DEFAULT_REPO_NAME"
INSTALL_DIR=""
DRY_RUN="false"

declare -a QUICK_START_ARGS=()

parse_key() {
  local key="$1"
  local text="$2"
  printf '%s\n' "$text" | sed -n "s/^${key}=//p" | head -n 1
}

get_remote_url() {
  case "$1" in
    github)
      printf '%s' 'git@github.com:boogieLing/R0SkillsMan.git'
      ;;
    origin)
      printf '%s' 'git@gl.quanyougame.net:lynsan/skills-man.git'
      ;;
    cggame)
      printf '%s' 'git@gl.cggame123.com:lynsan/skills-man.git'
      ;;
    *)
      return 1
      ;;
  esac
}

usage() {
  cat <<'EOF'
用法:
  install_and_quick_start.sh [--remote <name>] [--branch <name>] [--install-dir <path>] [--repo-name <name>] [--name <prefix>] [--allow-dirty] [--allow-partial] [--dry-run]

说明:
  - 可单独下载后执行，不要求当前目录已经有仓库
  - 默认从 github/main 拉取
  - 若本地没有仓库则 clone；若已有仓库则 fetch + pull --ff-only
  - clone / 更新完成后自动执行仓库内的 scripts/quick_start.sh

默认值:
  remote      github
  branch      main
  install-dir ~/.local/share/r0-skills

示例:
  bash install_and_quick_start.sh
  bash install_and_quick_start.sh --name lyn
  bash install_and_quick_start.sh --remote origin --install-dir ~/work/r0-skills --name lyn
  curl -L "<raw-url>" -o /tmp/install_and_quick_start.sh
  bash /tmp/install_and_quick_start.sh --name lyn
EOF
}

ensure_quick_start_arg() {
  local needle="$1"
  local item
  for item in "${QUICK_START_ARGS[@]}"; do
    if [[ "$item" == "$needle" ]]; then
      return 0
    fi
  done
  QUICK_START_ARGS+=("$needle")
}

ensure_remote_known() {
  if ! get_remote_url "$REMOTE" >/dev/null; then
    echo "未知远端: $REMOTE" >&2
    echo "可用远端: github / origin / cggame" >&2
    exit 1
  fi
}

ensure_repo_remotes() {
  local repo_dir="$1"
  local name url
  for name in github origin cggame; do
    url="$(get_remote_url "$name")"
    if git -C "$repo_dir" remote get-url "$name" >/dev/null 2>&1; then
      git -C "$repo_dir" remote set-url "$name" "$url"
    else
      git -C "$repo_dir" remote add "$name" "$url"
    fi
  done
}

clone_repo() {
  local repo_dir="$1"
  local remote_url
  remote_url="$(get_remote_url "$REMOTE")"
  mkdir -p "$(dirname "$repo_dir")"
  git clone --origin "$REMOTE" --branch "$BRANCH" "$remote_url" "$repo_dir"
  ensure_repo_remotes "$repo_dir"
}

update_repo() {
  local repo_dir="$1"
  ensure_repo_remotes "$repo_dir"
  git -C "$repo_dir" fetch --prune "$REMOTE" "$BRANCH"
  if git -C "$repo_dir" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git -C "$repo_dir" checkout "$BRANCH"
  else
    git -C "$repo_dir" checkout -B "$BRANCH" --track "$REMOTE/$BRANCH"
  fi
  git -C "$repo_dir" pull --ff-only "$REMOTE" "$BRANCH"
}

print_plan() {
  local repo_dir="$1"
  local remote_url
  remote_url="$(get_remote_url "$REMOTE")"
  echo "mode=dry-run"
  echo "remote=$REMOTE"
  echo "branch=$BRANCH"
  echo "remote_url=$remote_url"
  echo "install_dir=$repo_dir"
  if [[ -d "$repo_dir/.git" ]]; then
    echo "repo_action=update"
    echo "fetch_cmd=git -C $repo_dir fetch --prune $REMOTE $BRANCH"
    echo "checkout_cmd=git -C $repo_dir checkout $BRANCH"
    echo "pull_cmd=git -C $repo_dir pull --ff-only $REMOTE $BRANCH"
  else
    echo "repo_action=clone"
    echo "clone_cmd=git clone --origin $REMOTE --branch $BRANCH $remote_url $repo_dir"
  fi
  echo "quick_start_cmd=bash $repo_dir/scripts/quick_start.sh ${QUICK_START_ARGS[*]}"
}

run_quick_start() {
  local repo_dir="$1"
  if [[ ${#QUICK_START_ARGS[@]} -gt 0 ]]; then
    bash "$repo_dir/scripts/quick_start.sh" "${QUICK_START_ARGS[@]}"
  else
    bash "$repo_dir/scripts/quick_start.sh"
  fi
}

print_intro() {
  local repo_dir="$1"
  local quick_start_output="$2"
  local target_prefix pinned_push_tool

  target_prefix="$(parse_key "target_prefix" "$quick_start_output")"
  pinned_push_tool="$(parse_key "pinned_push_tool" "$quick_start_output")"
  if [[ -z "$target_prefix" ]]; then
    target_prefix="r0"
  fi
  if [[ -z "$pinned_push_tool" ]]; then
    pinned_push_tool="$HOME/.local/bin/${target_prefix}push"
  fi

  cat <<EOF

安装完成。

- 仓库位置: $repo_dir
- 当前前缀: $target_prefix
- 固定 push 工具: $pinned_push_tool
- README: $repo_dir/README.md

下一步建议：

1. 打开 Codex 或 Claude Code
2. 开一个新会话，确认新的 skill 前缀已经可见
3. 直接试一下：

  \$${target_prefix}-request 把这个需求整理成 DSL
  /${target_prefix}-request 把这个需求整理成 DSL

附加命令：

  cd "$repo_dir"
  $pinned_push_tool help

如果只是想重新同步技能或刷新固定路径，回到仓库里重跑：

  bash "$repo_dir/scripts/quick_start.sh"
EOF
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
    --install-dir)
      [[ $# -ge 2 ]] || {
        echo "--install-dir 缺少参数" >&2
        exit 1
      }
      INSTALL_DIR="$2"
      shift 2
      ;;
    --repo-name)
      [[ $# -ge 2 ]] || {
        echo "--repo-name 缺少参数" >&2
        exit 1
      }
      REPO_NAME="$2"
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

ensure_remote_known

if [[ -z "$INSTALL_DIR" ]]; then
  INSTALL_DIR="${DEFAULT_INSTALL_BASE}/${REPO_NAME}"
fi
INSTALL_DIR="$(
  python3 - "$INSTALL_DIR" <<'PY'
from pathlib import Path
import sys

print(Path(sys.argv[1]).expanduser().resolve())
PY
)"

if [[ "$DRY_RUN" == "true" ]]; then
  ensure_quick_start_arg "--allow-dirty"
  print_plan "$INSTALL_DIR"
  if [[ -x "$INSTALL_DIR/scripts/quick_start.sh" ]]; then
    run_quick_start "$INSTALL_DIR"
  fi
  exit 0
fi

if [[ -e "$INSTALL_DIR" && ! -d "$INSTALL_DIR/.git" ]]; then
  echo "安装目录已存在且不是 Git 仓库: $INSTALL_DIR" >&2
  exit 1
fi

if [[ -d "$INSTALL_DIR/.git" ]]; then
  update_repo "$INSTALL_DIR"
else
  clone_repo "$INSTALL_DIR"
fi

if [[ ! -x "$INSTALL_DIR/scripts/quick_start.sh" ]]; then
  echo "未找到 quick_start.sh: $INSTALL_DIR/scripts/quick_start.sh" >&2
  exit 1
fi

echo "remote=$REMOTE"
echo "branch=$BRANCH"
echo "install_dir=$INSTALL_DIR"
QUICK_START_OUTPUT="$(run_quick_start "$INSTALL_DIR")"
printf '%s\n' "$QUICK_START_OUTPUT"
print_intro "$INSTALL_DIR" "$QUICK_START_OUTPUT"
