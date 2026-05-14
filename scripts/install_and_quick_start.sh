#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${R0_INSTALL_TEMP_RUNNER:-}" && -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  TMP_BASE="${TMPDIR:-/tmp}"
  TMP_BASE="${TMP_BASE%/}"
  ORIG_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  ORIG_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  TEMP_RUNNER="$(mktemp "$TMP_BASE/skills_man.XXXXXX")"
  cp "$ORIG_SCRIPT" "$TEMP_RUNNER"
  chmod +x "$TEMP_RUNNER"
  exec env \
    R0_INSTALL_TEMP_RUNNER=1 \
    R0_INSTALL_SOURCE_SCRIPT="$ORIG_SCRIPT" \
    R0_INSTALL_SOURCE_ROOT="$ORIG_ROOT_DIR" \
    bash "$TEMP_RUNNER" "$@"
fi

DEFAULT_REMOTE="github"
DEFAULT_BRANCH="main"
DEFAULT_REPO_NAME="r0-skills"
DEFAULT_INSTALL_BASE="${HOME}/.local/share"
DEFAULT_COMMAND_NAME="skills_man"
INSTALLER_URL="${R0_SKILLS_MAN_URL:-https://f.shine-shy.com/skills_man.sh}"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
LOCAL_BIN_DIR="${LOCAL_BIN_DIR:-$HOME/.local/bin}"

ACTION="install"
REMOTE="$DEFAULT_REMOTE"
BRANCH="$DEFAULT_BRANCH"
REPO_NAME="$DEFAULT_REPO_NAME"
INSTALL_DIR=""
INSTALL_DIR_EXPLICIT="false"
INSTALL_DIR_SELECTION=""
COMMAND_NAME="${R0_SKILLS_MAN_COMMAND:-$DEFAULT_COMMAND_NAME}"
COMMAND_PATH=""
DRY_RUN="false"
SELF_INSTALL="true"
OVERWRITE_EXISTING="false"
UPDATE_EXISTING="false"
SKIP_EXISTING="false"
SELECTED_REMOTE=""

declare -a QUICK_START_ARGS=()
declare -a UNINSTALL_PATHS=()
declare -a LINKED_REPO_CANDIDATES=()
declare -a REMOTE_CANDIDATES=()

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  UI_RESET=$'\033[0m'
  UI_BOLD=$'\033[1m'
  UI_DIM=$'\033[2m'
  UI_CYAN=$'\033[36m'
  UI_GREEN=$'\033[32m'
  UI_YELLOW=$'\033[33m'
  UI_MAGENTA=$'\033[35m'
else
  UI_RESET=""
  UI_BOLD=""
  UI_DIM=""
  UI_CYAN=""
  UI_GREEN=""
  UI_YELLOW=""
  UI_MAGENTA=""
fi

parse_key() {
  local key="$1"
  local text="$2"
  printf '%s\n' "$text" | sed -n "s/^${key}=//p" | head -n 1
}

get_remote_url() {
  case "$1" in
    github)
      printf '%s' "${R0_REMOTE_URL_GITHUB:-git@github.com:boogieLing/R0SkillsMan.git}"
      ;;
    origin)
      printf '%s' "${R0_REMOTE_URL_ORIGIN:-git@gl.quanyougame.net:lynsan/skills-man.git}"
      ;;
    cggame)
      printf '%s' "${R0_REMOTE_URL_CGGAME:-git@gl.cggame123.com:lynsan/skills-man.git}"
      ;;
    *)
      return 1
      ;;
  esac
}

usage() {
  cat <<'EOF'
用法:
  skills_man [install] [--remote <name>] [--branch <name>] [--install-dir <path>] [--repo-name <name>] [--name <prefix>] [--overwrite] [--update-existing] [--allow-dirty] [--allow-partial] [--dry-run]
  skills_man uninstall [--install-dir <path>] [--dry-run]
  skills_man self-install [--dry-run]

说明:
  - 可直接通过 curl 管道执行，首次执行会先安装为 ~/.local/bin/skills_man 命令
  - 默认先从 github/main 拉取；若无权限或失败，会立刻尝试 origin、cggame
  - 若直接从本地 skill 仓库执行脚本，默认复用当前仓库，兼容旧版直接执行方式
  - 若已存在旧 skill 软链，默认反推出旧安装仓库并复用
  - 若安装目录已有 skill 仓库，默认更新；可显式选择跳过或覆盖
  - clone / 更新完成后自动执行仓库内的 scripts/quick_start.sh
  - uninstall 会清理 skill 软链、固定 push 工具、安装仓库目录和 skills_man 命令

默认值:
  remote      github
              拉取失败时自动按 github -> origin -> cggame 回退
  branch      main
  install-dir ~/.local/share/r0-skills
              直接本地仓库执行或检测到旧软链时，会自动复用对应仓库
  command     ~/.local/bin/skills_man

示例:
  curl -fsSL "https://f.shine-shy.com/skills_man.sh" | bash -s --
  curl -fsSL "https://f.shine-shy.com/skills_man.sh" | bash -s -- --name lyn
  skills_man install --overwrite
  skills_man uninstall
  curl -fsSL "https://f.shine-shy.com/skills_man.sh" | bash -s -- --remote cggame --install-dir ~/work/r0-skills --name lyn
  bash scripts/install_and_quick_start.sh --dry-run

可选环境变量:
  R0_SKILLS_MAN_URL      覆盖自安装下载地址
  R0_SKILLS_MAN_COMMAND  覆盖安装后的命令名
  LOCAL_BIN_DIR          覆盖命令安装目录（默认: ~/.local/bin）
  CODEX_SKILLS_DIR       覆盖 Codex skill 目录
  CLAUDE_SKILLS_DIR      覆盖 Claude skill 目录
  R0_REMOTE_URL_GITHUB   覆盖 github 仓库地址
  R0_REMOTE_URL_ORIGIN   覆盖 origin 仓库地址
  R0_REMOTE_URL_CGGAME   覆盖 cggame 仓库地址
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

build_remote_candidates() {
  local name existing item
  REMOTE_CANDIDATES=()
  for name in "$REMOTE" github origin cggame; do
    get_remote_url "$name" >/dev/null || continue
    existing="false"
    if (( ${#REMOTE_CANDIDATES[@]} > 0 )); then
      for item in "${REMOTE_CANDIDATES[@]}"; do
        if [[ "$item" == "$name" ]]; then
          existing="true"
          break
        fi
      done
    fi
    if [[ "$existing" == "false" ]]; then
      REMOTE_CANDIDATES+=("$name")
    fi
  done
}

remote_candidates_text() {
  build_remote_candidates
  printf '%s' "${REMOTE_CANDIDATES[*]}"
}

resolve_path() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

print(Path(sys.argv[1]).expanduser().resolve(strict=False))
PY
}

path_is_under() {
  local path="$1"
  local root="$2"
  case "$path" in
    "$root"|"$root"/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

assert_safe_remove_root() {
  local path="$1"
  case "$path" in
    ""|"/"|"$HOME"|"$HOME/"|"$HOME/.local"|"$HOME/.local/"|"$HOME/.local/share"|"$HOME/.local/share/")
      echo "拒绝对危险路径执行删除: $path" >&2
      exit 1
      ;;
  esac
}

has_skill_install() {
  local repo_dir="$1"
  local skill_dir
  [[ -d "$repo_dir" ]] || return 1
  [[ -d "$repo_dir/shared" || -x "$repo_dir/scripts/quick_start.sh" ]] || return 1
  shopt -s nullglob
  for skill_dir in "$repo_dir"/*-request "$repo_dir"/*-submit "$repo_dir"/*-work; do
    [[ -d "$skill_dir" ]] || continue
    return 0
  done
  return 1
}

add_linked_repo_candidate() {
  local repo_dir="$1"
  local existing
  [[ -n "$repo_dir" ]] || return 0
  repo_dir="$(resolve_path "$repo_dir")"
  has_skill_install "$repo_dir" || return 0
  if (( ${#LINKED_REPO_CANDIDATES[@]} > 0 )); then
    for existing in "${LINKED_REPO_CANDIDATES[@]}"; do
      if [[ "$existing" == "$repo_dir" ]]; then
        return 0
      fi
    done
  fi
  LINKED_REPO_CANDIDATES+=("$repo_dir")
}

collect_linked_repo_candidates() {
  local base_dir entry resolved repo_dir
  LINKED_REPO_CANDIDATES=()

  for base_dir in "$CODEX_DIR" "$CLAUDE_DIR"; do
    [[ -d "$base_dir" ]] || continue
    while IFS= read -r entry; do
      [[ -L "$entry" ]] || continue
      resolved="$(resolve_path "$entry")"
      repo_dir="$(dirname "$resolved")"
      add_linked_repo_candidate "$repo_dir"
    done < <(find "$base_dir" -maxdepth 1 -mindepth 1 -type l -name '*-*' | sort)
  done
}

detect_default_install_dir() {
  local default_dir source_root home_local
  default_dir="$(resolve_path "${DEFAULT_INSTALL_BASE}/${REPO_NAME}")"
  home_local="$(resolve_path "$HOME/.local")"
  source_root="${R0_INSTALL_SOURCE_ROOT:-}"
  if [[ -n "$source_root" ]]; then
    source_root="$(resolve_path "$source_root")"
  fi

  if [[ -n "$source_root" && "$source_root" != "$home_local" ]]; then
    if has_skill_install "$source_root"; then
      INSTALL_DIR_SELECTION="source_root"
      INSTALL_DIR="$source_root"
      return
    fi
  fi

  collect_linked_repo_candidates
  if [[ ${#LINKED_REPO_CANDIDATES[@]} -eq 1 ]]; then
    INSTALL_DIR_SELECTION="existing_skill_links"
    INSTALL_DIR="${LINKED_REPO_CANDIDATES[0]}"
    return
  fi

  INSTALL_DIR_SELECTION="default"
  INSTALL_DIR="$default_dir"
}

install_command_tool() {
  local source_script
  mkdir -p "$(dirname "$COMMAND_PATH")"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "command_action=install"
    echo "command_path=$COMMAND_PATH"
    echo "command_source=$INSTALLER_URL"
    return
  fi

  source_script="${BASH_SOURCE[0]:-}"
  if [[ -n "$source_script" && -f "$source_script" ]]; then
    cp "$source_script" "$COMMAND_PATH"
  else
    command -v curl >/dev/null 2>&1 || {
      echo "缺少 curl，无法安装命令工具: $COMMAND_PATH" >&2
      exit 1
    }
    curl -fsSL "$INSTALLER_URL" -o "$COMMAND_PATH"
  fi
  chmod +x "$COMMAND_PATH"
  echo "command_installed=$COMMAND_PATH"
  case ":$PATH:" in
    *":$(dirname "$COMMAND_PATH"):"*)
      ;;
    *)
      echo "command_path_warning=$(dirname "$COMMAND_PATH") 不在 PATH 中；可手动加入 shell 配置" >&2
      ;;
  esac
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
  local remote_name remote_url tmp_clone
  mkdir -p "$(dirname "$repo_dir")"
  build_remote_candidates
  for remote_name in "${REMOTE_CANDIDATES[@]}"; do
    remote_url="$(get_remote_url "$remote_name")"
    tmp_clone="${repo_dir}.tmp.${remote_name}.$$"
    rm -rf "$tmp_clone"
    echo "clone_attempt_remote=$remote_name"
    if git clone --origin "$remote_name" --branch "$BRANCH" "$remote_url" "$tmp_clone"; then
      mv "$tmp_clone" "$repo_dir"
      SELECTED_REMOTE="$remote_name"
      REMOTE="$remote_name"
      ensure_repo_remotes "$repo_dir"
      echo "selected_remote=$remote_name"
      return 0
    fi
    echo "clone_attempt_failed=$remote_name" >&2
    rm -rf "$tmp_clone"
  done
  echo "所有远端 clone 均失败: ${REMOTE_CANDIDATES[*]}" >&2
  exit 1
}

update_repo() {
  local repo_dir="$1"
  local remote_name remote_ref
  ensure_repo_remotes "$repo_dir"
  build_remote_candidates
  SELECTED_REMOTE=""
  for remote_name in "${REMOTE_CANDIDATES[@]}"; do
    remote_ref="refs/remotes/$remote_name/$BRANCH"
    echo "fetch_attempt_remote=$remote_name"
    if git -C "$repo_dir" fetch --prune "$remote_name" "+refs/heads/$BRANCH:$remote_ref"; then
      SELECTED_REMOTE="$remote_name"
      REMOTE="$remote_name"
      echo "selected_remote=$remote_name"
      break
    fi
    echo "fetch_attempt_failed=$remote_name" >&2
  done
  if [[ -z "$SELECTED_REMOTE" ]]; then
    echo "所有远端 fetch 均失败: ${REMOTE_CANDIDATES[*]}" >&2
    exit 1
  fi
  remote_ref="refs/remotes/$SELECTED_REMOTE/$BRANCH"
  if git -C "$repo_dir" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git -C "$repo_dir" checkout "$BRANCH"
  else
    git -C "$repo_dir" checkout -B "$BRANCH" --track "$SELECTED_REMOTE/$BRANCH"
  fi
  git -C "$repo_dir" merge --ff-only "$remote_ref"
}

overwrite_repo() {
  local repo_dir="$1"
  assert_safe_remove_root "$repo_dir"
  rm -rf "$repo_dir"
  clone_repo "$repo_dir"
}

select_existing_repo_action() {
  local repo_dir="$1"

  if [[ "$OVERWRITE_EXISTING" == "true" ]]; then
    printf '%s\n' "overwrite"
    return
  fi
  if [[ "$SKIP_EXISTING" == "true" ]]; then
    printf '%s\n' "skip"
    return
  fi
  printf '%s\n' "update"
}

prepare_repo() {
  local repo_dir="$1"
  local action

  if has_skill_install "$repo_dir"; then
    action="$(select_existing_repo_action "$repo_dir")"
    echo "existing_install_action=$action"
    case "$action" in
      overwrite)
        overwrite_repo "$repo_dir"
        ;;
      update)
        update_repo "$repo_dir"
        ;;
      skip)
        echo "install_skipped=$repo_dir"
        return 1
        ;;
    esac
    return 0
  fi

  if [[ -e "$repo_dir" && ! -d "$repo_dir/.git" ]]; then
    echo "安装目录已存在且不是 Git 仓库: $repo_dir" >&2
    exit 1
  fi

  if [[ -d "$repo_dir/.git" ]]; then
    update_repo "$repo_dir"
  else
    clone_repo "$repo_dir"
  fi
}

print_plan() {
  local repo_dir="$1"
  local remote_url
  remote_url="$(get_remote_url "$REMOTE")"
  build_remote_candidates
  echo "mode=dry-run"
  echo "action=$ACTION"
  echo "command_path=$COMMAND_PATH"
  echo "installer_url=$INSTALLER_URL"
  echo "remote=$REMOTE"
  echo "remote_fallback_order=${REMOTE_CANDIDATES[*]}"
  echo "branch=$BRANCH"
  echo "remote_url=$remote_url"
  echo "install_dir=$repo_dir"
  echo "install_dir_selection=$INSTALL_DIR_SELECTION"
  echo "install_dir_explicit=$INSTALL_DIR_EXPLICIT"
  if has_skill_install "$repo_dir"; then
    if [[ "$OVERWRITE_EXISTING" == "true" ]]; then
      echo "repo_action=overwrite"
    elif [[ "$SKIP_EXISTING" == "true" ]]; then
      echo "repo_action=skip_existing"
    else
      echo "repo_action=update"
    fi
  elif [[ -d "$repo_dir/.git" ]]; then
    echo "repo_action=update_existing_git"
    echo "fetch_fallback=try ${REMOTE_CANDIDATES[*]}"
    echo "fetch_cmd=git -C $repo_dir fetch --prune <remote> +refs/heads/$BRANCH:refs/remotes/<remote>/$BRANCH"
    echo "checkout_cmd=git -C $repo_dir checkout $BRANCH"
    echo "merge_cmd=git -C $repo_dir merge --ff-only refs/remotes/<selected_remote>/$BRANCH"
  else
    echo "repo_action=clone"
    echo "clone_fallback=try ${REMOTE_CANDIDATES[*]}"
    echo "clone_cmd=git clone --origin <remote> --branch $BRANCH <remote_url> $repo_dir"
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

remove_path() {
  local path="$1"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "would_remove=$path"
    return
  fi
  rm -rf "$path"
  echo "removed=$path"
}

queue_fallback_uninstall_paths() {
  local repo_dir="$1"
  local entry resolved
  UNINSTALL_PATHS=()

  for base_dir in "$CODEX_DIR" "$CLAUDE_DIR" "$LOCAL_BIN_DIR"; do
    [[ -d "$base_dir" ]] || continue
    while IFS= read -r entry; do
      [[ -n "$entry" ]] || continue
      resolved="$(resolve_path "$entry")"
      if path_is_under "$resolved" "$repo_dir"; then
        UNINSTALL_PATHS+=("$entry")
      fi
    done < <(find "$base_dir" -maxdepth 1 -mindepth 1 -type l | sort)
  done

  if [[ -e "$COMMAND_PATH" || -L "$COMMAND_PATH" ]]; then
    UNINSTALL_PATHS+=("$COMMAND_PATH")
  fi
}

fallback_uninstall() {
  local repo_dir="$1"
  local path
  assert_safe_remove_root "$repo_dir"
  queue_fallback_uninstall_paths "$repo_dir"
  echo "repo_root=$repo_dir"
  echo "command_path=$COMMAND_PATH"
  echo "dry_run=$DRY_RUN"

  if [[ ${#UNINSTALL_PATHS[@]} -eq 0 ]]; then
    echo "link_cleanup=<none>"
  else
    for path in "${UNINSTALL_PATHS[@]}"; do
      remove_path "$path"
    done
  fi

  if [[ -d "$repo_dir" ]]; then
    remove_path "$repo_dir"
  else
    echo "repo_missing=$repo_dir"
  fi
  echo "[OK] uninstall completed."
}

run_uninstall() {
  local repo_dir="$1"
  local uninstall_script="$repo_dir/scripts/uninstall.sh"

  if [[ -x "$uninstall_script" ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
      bash "$uninstall_script" --repo-root "$repo_dir" --dry-run
    else
      bash "$uninstall_script" --repo-root "$repo_dir"
    fi
  else
    fallback_uninstall "$repo_dir"
  fi

  if [[ -e "$COMMAND_PATH" || -L "$COMMAND_PATH" ]]; then
    remove_path "$COMMAND_PATH"
  elif [[ "$DRY_RUN" == "true" ]]; then
    echo "command_missing=$COMMAND_PATH"
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

  printf '\n'
  printf '%b\n' "${UI_CYAN}${UI_BOLD}╔════════════════════════════════════════════════════════════╗${UI_RESET}"
  printf '%b\n' "${UI_CYAN}${UI_BOLD}║  🎉 Skills 安装完成  (•̀ᴗ•́)و ̑̑                           ║${UI_RESET}"
  printf '%b\n' "${UI_CYAN}${UI_BOLD}╚════════════════════════════════════════════════════════════╝${UI_RESET}"
  printf '%b\n' "${UI_GREEN}${UI_BOLD}📦 安装信息${UI_RESET}"
  printf '  %b仓库位置%b  %s\n' "${UI_DIM}" "${UI_RESET}" "$repo_dir"
  printf '  %b当前前缀%b  %s\n' "${UI_DIM}" "${UI_RESET}" "$target_prefix"
  printf '  %bPush 工具%b  %s\n' "${UI_DIM}" "${UI_RESET}" "$pinned_push_tool"
  printf '  %bREADME%b    %s\n' "${UI_DIM}" "${UI_RESET}" "$repo_dir/README.md"
  printf '\n'
  printf '%b\n' "${UI_YELLOW}${UI_BOLD}🚀 下一步建议${UI_RESET}"
  printf '  1. 打开 Codex 或 Claude Code\n'
  printf '  2. 新开一个会话，确认新的 skill 前缀已经出现\n'
  printf '  3. 先试下面入口，看看新 skill 是否已经生效\n'
  printf '\n'
  printf '%b\n' "${UI_MAGENTA}${UI_BOLD}▶ 直接可用${UI_RESET}"
  printf '  $%s-request 把这个需求整理成 DSL\n' "$target_prefix"
  printf '  $%s-tech-graph 画一个浅色 HTML 系统架构图\n' "$target_prefix"
  printf '  /%s-request 把这个需求整理成 DSL\n' "$target_prefix"
  printf '  /%s-tech-graph 画一个浅色 HTML 系统架构图\n' "$target_prefix"
  printf '\n'
  printf '%b\n' "${UI_CYAN}${UI_BOLD}🧰 附加命令${UI_RESET}"
  printf '  cd "%s"\n' "$repo_dir"
  printf '  %s help\n' "$pinned_push_tool"
  printf '\n'
  printf '%b\n' "${UI_GREEN}${UI_BOLD}🔁 需要重跑时${UI_RESET}"
  printf '  bash "%s/scripts/quick_start.sh"\n' "$repo_dir"
  printf '\n'
  printf '%b\n' "${UI_DIM}小提示: 如果 Codex / Claude Code 里还没看到新 skill，重新开一个新会话通常就够了。 (¬‿¬)${UI_RESET}"
}

if [[ $# -gt 0 ]]; then
  case "$1" in
    install|uninstall|self-install)
      ACTION="$1"
      shift
      ;;
    help)
      usage
      exit 0
      ;;
  esac
fi

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
      INSTALL_DIR_EXPLICIT="true"
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
    --command-name)
      [[ $# -ge 2 ]] || {
        echo "--command-name 缺少参数" >&2
        exit 1
      }
      COMMAND_NAME="$2"
      shift 2
      ;;
    --overwrite|--force|--yes)
      OVERWRITE_EXISTING="true"
      shift
      ;;
    --update-existing)
      UPDATE_EXISTING="true"
      shift
      ;;
    --skip-existing)
      SKIP_EXISTING="true"
      shift
      ;;
    --no-self-install)
      SELF_INSTALL="false"
      shift
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

if [[ -z "$INSTALL_DIR" ]]; then
  detect_default_install_dir
else
  INSTALL_DIR_SELECTION="explicit"
fi
INSTALL_DIR="$(resolve_path "$INSTALL_DIR")"
COMMAND_PATH="$(resolve_path "$LOCAL_BIN_DIR/$COMMAND_NAME")"

case "$ACTION" in
  self-install)
    install_command_tool
    exit 0
    ;;
  uninstall)
    run_uninstall "$INSTALL_DIR"
    exit 0
    ;;
  install)
    ;;
  *)
    echo "未知动作: $ACTION" >&2
    usage
    exit 1
    ;;
esac

ensure_remote_known

if [[ "$DRY_RUN" == "true" ]]; then
  if [[ "$SELF_INSTALL" == "true" ]]; then
    install_command_tool
  fi
  ensure_quick_start_arg "--allow-dirty"
  print_plan "$INSTALL_DIR"
  if [[ -x "$INSTALL_DIR/scripts/quick_start.sh" ]]; then
    if ! has_skill_install "$INSTALL_DIR"; then
      run_quick_start "$INSTALL_DIR"
    fi
  fi
  exit 0
fi

if [[ "$SELF_INSTALL" == "true" ]]; then
  install_command_tool
fi

prepare_repo "$INSTALL_DIR" || exit 0

if [[ ! -x "$INSTALL_DIR/scripts/quick_start.sh" ]]; then
  echo "未找到 quick_start.sh: $INSTALL_DIR/scripts/quick_start.sh" >&2
  exit 1
fi

echo "remote=$REMOTE"
echo "selected_remote=${SELECTED_REMOTE:-$REMOTE}"
echo "branch=$BRANCH"
echo "install_dir=$INSTALL_DIR"
echo "install_dir_selection=$INSTALL_DIR_SELECTION"
QUICK_START_OUTPUT="$(run_quick_start "$INSTALL_DIR")"
printf '%s\n' "$QUICK_START_OUTPUT"
print_intro "$INSTALL_DIR" "$QUICK_START_OUTPUT"
