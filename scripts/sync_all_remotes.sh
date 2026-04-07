#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
BRANCH=""
ALLOW_PARTIAL_SCOPE="false"
declare -a TARGET_REMOTES=()
declare -a TRACKED_SKILLS=()
declare -a SCOPE_BLOCKERS=()

usage() {
  cat <<'EOF'
用法:
  sync_all_remotes.sh [--branch <name>] [--remote <name>]... [--allow-partial-scope]

说明:
  - 默认同步当前分支到全部已配置远端
  - 可通过 --branch 指定分支
  - 可重复使用 --remote，只同步指定远端
  - 默认先做 skill scope 与远端连通性预检；若当前仓库只是裁剪/部分来源，会阻断远端同步
  - --allow-partial-scope: 明确允许在 partial skill source 上继续远端同步，仅建议在你确认风险时使用

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
    --allow-partial-scope)
      ALLOW_PARTIAL_SCOPE="true"
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

has_tracked_skill() {
  local needle="$1"
  local item
  for item in "${TRACKED_SKILLS[@]}"; do
    if [[ "$item" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

collect_tracked_skills() {
  TRACKED_SKILLS=()
  while IFS= read -r skill_name; do
    [[ -n "$skill_name" ]] || continue
    TRACKED_SKILLS+=("$skill_name")
  done < <(git -C "$ROOT_DIR" ls-files 'r0-*' | cut -d/ -f1 | sort -u)
}

inspect_link_scope() {
  local label="$1"
  local base_dir="$2"
  local entry skill_name target

  [[ -d "$base_dir" ]] || return 0

  while IFS= read -r entry; do
    [[ -L "$entry" ]] || continue
    skill_name="$(basename "$entry")"
    target="$(readlink "$entry")"
    [[ "$target" == "$ROOT_DIR/"* ]] || continue

    if ! has_tracked_skill "$skill_name"; then
      if [[ -e "$entry" ]]; then
        SCOPE_BLOCKERS+=("$label: $skill_name -> $target (当前仓库未追踪该 skill)")
      else
        SCOPE_BLOCKERS+=("$label: $skill_name -> $target (失效软链，且当前仓库未追踪该 skill)")
      fi
      continue
    fi

    if [[ ! -e "$entry" ]]; then
      SCOPE_BLOCKERS+=("$label: $skill_name -> $target (当前指向本仓库，但软链已失效)")
    fi
  done < <(find "$base_dir" -maxdepth 1 -mindepth 1 -name 'r0-*' | sort)
}

run_scope_preflight() {
  collect_tracked_skills
  SCOPE_BLOCKERS=()

  if [[ ${#TRACKED_SKILLS[@]} -eq 0 ]]; then
    echo "未找到任何被 Git 追踪的 r0-* skill 目录，停止远端同步。" >&2
    exit 1
  fi

  echo "skill scope preflight:"
  echo "tracked_skills: ${TRACKED_SKILLS[*]}"

  inspect_link_scope "codex" "$CODEX_DIR"
  inspect_link_scope "claude" "$CLAUDE_DIR"

  if [[ ${#SCOPE_BLOCKERS[@]} -gt 0 ]]; then
    echo "检测到当前仓库与本地 skill 根目录的受管范围不一致：" >&2
    printf '%s\n' "${SCOPE_BLOCKERS[@]}" | sed 's/^/- /' >&2
    echo "为避免把 partial skill source 误判成“已全量同步”，默认停止远端同步。" >&2
    if [[ "$ALLOW_PARTIAL_SCOPE" != "true" ]]; then
      echo "如确认只想同步当前仓库已追踪的这部分 skills，请显式添加 --allow-partial-scope。" >&2
      exit 2
    fi
    echo "[WARN] 已显式允许 partial scope，继续执行远端同步。" >&2
  fi
}

extract_remote_host() {
  local remote_url="$1"
  if [[ "$remote_url" =~ ^ssh://([^@/]+@)?([^/:]+)(:[0-9]+)?/.*$ ]]; then
    echo "${BASH_REMATCH[2]}"
    return 0
  fi
  if [[ "$remote_url" =~ ^([^@/]+@)?([^:]+):.+$ ]]; then
    echo "${BASH_REMATCH[2]}"
    return 0
  fi
  return 1
}

check_remote_host_resolution() {
  local remote_name="$1"
  local remote_url="$2"
  local remote_host

  if ! remote_host="$(extract_remote_host "$remote_url")"; then
    echo "[INFO] 跳过 DNS 预检: $remote_name ($remote_url)"
    return 0
  fi

  if ! python3 - "$remote_host" <<'PY'
import socket
import sys

host = sys.argv[1]
try:
    socket.getaddrinfo(host, None)
except OSError as exc:
    print(exc)
    raise SystemExit(1)
PY
  then
    echo "远端主机不可解析: $remote_name ($remote_host)" >&2
    return 1
  fi

  echo "[OK] remote DNS: $remote_name -> $remote_host"
}

resolve_branch_name() {
  local current_branch

  current_branch="$(git -C "$ROOT_DIR" branch --show-current)"
  if [[ -n "$current_branch" ]]; then
    echo "$current_branch"
    return 0
  fi

  current_branch="$(git -C "$ROOT_DIR" for-each-ref --points-at HEAD refs/heads --format='%(refname:short)' | head -n 1)"
  if [[ -n "$current_branch" ]]; then
    echo "$current_branch"
    return 0
  fi

  return 1
}

if ! git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "当前目录不是 Git 仓库: $ROOT_DIR" >&2
  exit 1
fi

if [[ -z "$BRANCH" ]]; then
  BRANCH="$(resolve_branch_name || true)"
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

run_scope_preflight

echo "准备同步分支: $BRANCH"
echo "目标远端: ${TARGET_REMOTES[*]}"

for remote_name in "${TARGET_REMOTES[@]}"; do
  remote_url=""
  if ! git -C "$ROOT_DIR" remote get-url "$remote_name" >/dev/null 2>&1; then
    echo "远端不存在: $remote_name" >&2
    exit 1
  fi
  remote_url="$(git -C "$ROOT_DIR" remote get-url "$remote_name")"
  check_remote_host_resolution "$remote_name" "$remote_url"

  echo "推送到远端: $remote_name"
  git -C "$ROOT_DIR" push "$remote_name" "$BRANCH"
done

echo "全部远端同步完成。"
