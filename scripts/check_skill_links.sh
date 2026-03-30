#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
declare -a SOURCE_SKILLS=()

collect_source_skills() {
  local skill_dir
  SOURCE_SKILLS=()
  for skill_dir in "$ROOT_DIR"/r0-*; do
    [[ -d "$skill_dir" ]] || continue
    SOURCE_SKILLS+=("$(basename "$skill_dir")")
  done
}

count_skill_entries() {
  local base_dir="$1"
  [[ -d "$base_dir" ]] || {
    echo 0
    return
  }
  find "$base_dir" -maxdepth 1 -mindepth 1 -name 'r0-*' | wc -l | tr -d ' '
}

print_list() {
  local title="$1"
  shift
  local -a items=("$@")
  echo "$title"
  if [[ ${#items[@]} -eq 0 ]]; then
    echo "- <none>"
    return
  fi
  printf '%s\n' "${items[@]}" | sed 's/^/- /'
}

inspect_target_dir() {
  local label="$1"
  local base_dir="$2"
  local entry target broken_count=0
  local -a entries=()
  local -a broken=()

  if [[ -d "$base_dir" ]]; then
    while IFS= read -r entry; do
      [[ -n "$entry" ]] || continue
      entries+=("$(basename "$entry")")
      if [[ -L "$entry" ]]; then
        target="$(readlink "$entry")"
        if [[ ! -e "$entry" ]]; then
          broken+=("$(basename "$entry") -> $target")
          broken_count=$((broken_count + 1))
        fi
      fi
    done < <(find "$base_dir" -maxdepth 1 -mindepth 1 -name 'r0-*' | sort)
  fi

  echo "[$label]"
  echo "dir=$base_dir"
  echo "count=${#entries[@]}"
  if [[ ${#entries[@]} -gt 0 ]]; then
    print_list "entries:" "${entries[@]}"
  else
    print_list "entries:"
  fi
  if [[ ${#broken[@]} -gt 0 ]]; then
    print_list "broken_links:" "${broken[@]}"
  else
    print_list "broken_links:"
  fi
  echo "broken_count=$broken_count"
  echo

  return "$broken_count"
}

main() {
  local source_count codex_count claude_count status=0

  collect_source_skills
  source_count="${#SOURCE_SKILLS[@]}"
  codex_count="$(count_skill_entries "$CODEX_DIR")"
  claude_count="$(count_skill_entries "$CLAUDE_DIR")"

  echo "[source]"
  echo "root_dir=$ROOT_DIR"
  echo "source_count=$source_count"
  print_list "source_skills:" "${SOURCE_SKILLS[@]}"
  echo

  if (( source_count == 0 )); then
    echo "[FAIL] 当前仓库未找到任何 r0-* skill 目录。" >&2
    status=1
  fi

  if (( codex_count > source_count || claude_count > source_count )); then
    echo "[WARN] 当前来源包含的 r0-* skills 少于目标目录现有条目，疑似部分镜像或来源不完整。" >&2
    status=2
  fi

  if ! inspect_target_dir "codex" "$CODEX_DIR"; then
    status=3
  fi
  if ! inspect_target_dir "claude" "$CLAUDE_DIR"; then
    status=3
  fi

  if (( status == 0 )); then
    echo "[OK] 未发现来源数量异常或失效软链接。"
  else
    echo "[FAIL] skill 链接校验未通过，exit_code=$status" >&2
  fi
  return "$status"
}

main "$@"
