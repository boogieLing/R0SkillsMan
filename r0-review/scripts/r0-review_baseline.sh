#!/usr/bin/env bash
set -euo pipefail

MODE="quick"
OUT_DIR=""
TARGETS=()

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/r0-review_baseline.sh [--mode quick|full] [--out-dir <dir>] [--targets <file1> <file2> ...]

Notes:
  - If --targets is omitted and current directory is a git repository, changed files are used.
  - Output defaults to ./r0/review/_artifacts/<timestamp>/
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-quick}"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="${2:-}"
      shift 2
      ;;
    --targets)
      shift
      while [[ $# -gt 0 && "$1" != --* ]]; do
        TARGETS+=("$1")
        shift
      done
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$MODE" != "quick" && "$MODE" != "full" ]]; then
  echo "--mode must be quick or full" >&2
  exit 1
fi

if [[ -z "$OUT_DIR" ]]; then
  ts="$(date +%Y%m%d_%H%M%S)"
  OUT_DIR="./r0/review/_artifacts/$ts"
fi
mkdir -p "$OUT_DIR"

resolve_targets_from_git() {
  {
    git diff --name-only --diff-filter=ACMRTUXB
    git diff --cached --name-only --diff-filter=ACMRTUXB
    git ls-files --others --exclude-standard
  } | awk 'NF { seen[$0] = 1 } END { for (path in seen) print path }'
}

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    while IFS= read -r f; do
      [[ -n "$f" ]] && TARGETS+=("$f")
    done < <(resolve_targets_from_git)
  fi
fi

filter_text_targets() {
  local in=("$@")
  local out=()
  local f
  for f in "${in[@]}"; do
    [[ -f "$f" ]] || continue
    case "$f" in
      *.go|*.py|*.js|*.jsx|*.ts|*.tsx|*.java|*.rb|*.php|*.c|*.cc|*.cpp|*.cs|*.rs|*.kt|*.swift|*.sql|*.sh)
        out+=("$f")
        ;;
    esac
  done
  if [[ ${#out[@]} -gt 0 ]]; then
    printf '%s\n' "${out[@]}"
  fi
}

FILTERED=()
while IFS= read -r f; do
  [[ -n "$f" ]] && FILTERED+=("$f")
done < <(filter_text_targets "${TARGETS[@]}")
TARGETS=("${FILTERED[@]}")

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  {
    echo "# r0-review baseline"
    echo
    echo "- mode: $MODE"
    echo "- status: no target files"
    echo "- note: provide --targets or ensure git diff has changed files"
  } > "$OUT_DIR/summary.md"
  echo "No target files. Summary: $OUT_DIR/summary.md"
  exit 0
fi

{
  echo "# r0-review baseline"
  echo
  echo "- mode: $MODE"
  echo "- out_dir: $OUT_DIR"
  echo "- target_count: ${#TARGETS[@]}"
} > "$OUT_DIR/summary.md"

printf "file,total_lines,branch_signals,est_complexity,max_nesting\n" > "$OUT_DIR/complexity.csv"
printf "file,total_non_empty,comment_lines,comment_ratio\n" > "$OUT_DIR/comment_coverage.csv"
: > "$OUT_DIR/security_hits.txt"

count_comment_lines() {
  local file="$1"
  local ext="${file##*.}"
  local pattern
  case "$ext" in
    py|sh|rb|yaml|yml|toml)
      pattern='^[[:space:]]*#'
      ;;
    sql)
      pattern='^[[:space:]]*--'
      ;;
    go|js|jsx|ts|tsx|java|c|cc|cpp|cs|rs|kt|swift|php)
      pattern='^[[:space:]]*(//|/\\*|\\*)'
      ;;
    *)
      pattern='^$'
      ;;
  esac

  awk -v p="$pattern" '
    BEGIN {total=0; comment=0}
    {
      if ($0 ~ /^[[:space:]]*$/) next
      total++
      if (p != "^$" && $0 ~ p) comment++
    }
    END {
      ratio = (total == 0 ? 0 : comment / total)
      printf "%d,%d,%.4f\n", total, comment, ratio
    }
  ' "$file"
}

estimate_complexity() {
  local file="$1"
  awk '
    function has_kw(line, kw,    pattern) {
      pattern = "(^|[^[:alnum:]_])" kw "([^[:alnum:]_]|$)"
      return line ~ pattern
    }
    BEGIN {lines=0; branch=0; depth=0; maxd=0}
    {
      if ($0 ~ /^[[:space:]]*$/) next
      lines++

      s=$0
      while (match(s, /\{|\}/)) {
        token=substr(s, RSTART, RLENGTH)
        if (token == "{") depth++
        if (depth > maxd) maxd=depth
        if (token == "}") { depth--; if (depth < 0) depth=0 }
        s=substr(s, RSTART+RLENGTH)
      }

      t=$0
      if (has_kw(t, "if")) branch++
      if (t ~ /(^|[^[:alnum:]_])else[[:space:]]+if([^[:alnum:]_]|$)/) branch++
      if (has_kw(t, "for")) branch++
      if (has_kw(t, "while")) branch++
      if (has_kw(t, "switch")) branch++
      if (has_kw(t, "case")) branch++
      if (has_kw(t, "catch")) branch++
      if (t ~ /&&/) branch++
      if (t ~ /\|\|/) branch++
    }
    END {
      score = 1 + branch
      printf "%d,%d,%d,%d\n", lines, branch, score, maxd
    }
  ' "$file"
}

run_security_keyword_scan() {
  local file="$1"
  if ! command -v rg >/dev/null 2>&1; then
    return 0
  fi
  rg -n --no-heading \
    -e 'dangerouslySetInnerHTML' \
    -e 'innerHTML[[:space:]]*=' \
    -e '\beval\(' \
    -e '\bexec\(' \
    -e 'os\.system\(' \
    -e 'subprocess\.(Popen|call|run)\(' \
    -e 'InsecureSkipVerify[[:space:]]*:[[:space:]]*true' \
    -e 'SELECT.+\+' \
    -e 'http://[^ ]+' \
    -e '\.\./' \
    "$file" >> "$OUT_DIR/security_hits.txt" || true
}

for f in "${TARGETS[@]}"; do
  comp="$(estimate_complexity "$f")"
  cmt="$(count_comment_lines "$f")"
  printf "%s,%s\n" "$f" "$comp" >> "$OUT_DIR/complexity.csv"
  printf "%s,%s\n" "$f" "$cmt" >> "$OUT_DIR/comment_coverage.csv"
  run_security_keyword_scan "$f"
done

if [[ "$MODE" == "full" ]]; then
  if command -v gocyclo >/dev/null 2>&1; then
    {
      echo
      echo "## gocyclo"
      gocyclo -over 10 "${TARGETS[@]}" || true
    } > "$OUT_DIR/gocyclo.txt"
  fi

  if command -v gosec >/dev/null 2>&1 && [[ -f "go.mod" ]]; then
    gosec ./... > "$OUT_DIR/gosec.txt" 2>&1 || true
  fi

  if command -v golangci-lint >/dev/null 2>&1 && [[ -f "go.mod" ]]; then
    golangci-lint run ./... > "$OUT_DIR/golangci-lint.txt" 2>&1 || true
  fi

  if command -v bandit >/dev/null 2>&1; then
    bandit -q -r . > "$OUT_DIR/bandit.txt" 2>&1 || true
  fi
fi

{
  echo
  echo "## files"
  for f in "${TARGETS[@]}"; do
    echo "- $f"
  done
  echo
  echo "## generated"
  echo "- complexity.csv"
  echo "- comment_coverage.csv"
  echo "- security_hits.txt"
  if [[ "$MODE" == "full" ]]; then
    echo "- optional: gocyclo.txt / gosec.txt / golangci-lint.txt / bandit.txt"
  fi
} >> "$OUT_DIR/summary.md"

echo "Baseline finished. Summary: $OUT_DIR/summary.md"
