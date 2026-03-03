#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  sync_article.sh "同步提示词指导的文章"

Options:
  --articles-dir <dir>   文章集合目录（每篇文章一个子目录）
  --article-root <dir>   同 --articles-dir（兼容别名）
  --server-name <name>   MCP 服务器名（默认: lark）
  --client <name>        客户端（默认: codex，仅支持 codex）
  --title <name>         导入到 Lark 的文档标题（默认从文件名推断）
  --auto-reauth <bool>   token 失效时自动拉起 lark-mcp login 并重试一次（默认: true）
  --lark-app-id <id>     可选，自动登录使用的 Lark App ID（或环境变量 WRITE_LARK_APP_ID）
  --lark-app-secret <s>  可选，自动登录使用的 Lark App Secret（或环境变量 WRITE_LARK_APP_SECRET）
  --diagram-mode <mode>  流程图处理模式：external-image|keep（默认: external-image）
  --diagram-format <fmt> 外站流程图格式：png|svg（默认: png）
  --mermaid-plain <bool> Mermaid 导图是否转朴素风格（默认: true）
  --mermaid-base-url <u> Mermaid 外站地址（默认: https://mermaid.ink）
  --latex-mode <mode>    LaTeX 处理模式：external-image|keep（默认: external-image）
  --latex-format <fmt>   LaTeX 外站格式：png|svg（默认: png）
  --latex-base-url <u>   LaTeX 外站地址（默认: https://latex.codecogs.com）
  --use-uat <bool>       docx.builtin.import 的 useUAT（默认: true）
  --no-metadata          不回写 metadata.yaml
  --dry-run              只做匹配，不执行导入
  -v, --verbose          输出调试信息
  -h, --help             查看帮助

Examples:
  sync_article.sh "同步提示词指导的文章"
  sync_article.sh "把 API 设计指南 这篇同步到 Lark"
  sync_article.sh --articles-dir "<YOUR_ARTICLES_DIR>" "同步 提示词指导"
USAGE
}

log() {
  local prefix="${WRITE_LARK_LOG_PREFIX:-$(basename "$(dirname "$(dirname "$0")")")}"
  printf '[%s] %s\n' "$prefix" "$*"
}

err() {
  local prefix="${WRITE_LARK_LOG_PREFIX:-$(basename "$(dirname "$(dirname "$0")")")}"
  printf '[%s][ERROR] %s\n' "$prefix" "$*" >&2
}

trim() {
  local s="$1"
  s="${s#${s%%[![:space:]]*}}"
  s="${s%${s##*[![:space:]]}}"
  printf '%s' "$s"
}

escape_json() {
  local s="$1"
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\n'/\\n}
  printf '%s' "$s"
}

# UTF-8 安全截断到 27 个字符（Lark 侧 file_name 常见限制）
truncate_27_chars() {
  python3 - "$1" <<'PY'
import sys
s = sys.argv[1]
print(s[:27])
PY
}

detect_articles_dir() {
  # 优先使用显式环境变量（通用变量优先，兼容旧变量）
  local env_dir="${WRITE_LARK_ARTICLES_DIR:-${ARTICLES_DIR:-${WRITING_ARTICLES_DIR:-}}}"
  if [[ -n "$env_dir" && -d "$env_dir" ]]; then
    printf '%s' "$env_dir"
    return 0
  fi

  # 如果当前目录就是文章集合目录（含至少一个子目录，且子目录内有 md 文件）
  local has_candidate="0"
  local dsub
  while IFS= read -r -d '' dsub; do
    if find "$dsub" -maxdepth 1 -type f -name '*.md' | grep -q .; then
      has_candidate="1"
      break
    fi
  done < <(find "$PWD" -mindepth 1 -maxdepth 1 -type d -print0)
  if [[ "$has_candidate" == "1" ]]; then
    printf '%s' "$PWD"
    return 0
  fi

  local d="$PWD"
  while [[ "$d" != "/" ]]; do
    if [[ -d "$d/articles" ]]; then
      printf '%s/articles' "$d"
      return 0
    fi
    d="$(dirname "$d")"
  done

  return 1
}

normalize_query() {
  local q="$1"
  q="$(printf '%s' "$q" | tr '[:upper:]' '[:lower:]')"

  # 常见自然语言噪音词
  local stopwords=(
    "同步" "文章" "这篇" "那篇" "一下" "请" "帮我" "帮忙" "把" "给我"
    "导入" "飞书" "lark" "云文档" "发布" "到" "的" "一下子" "进行"
  )

  for w in "${stopwords[@]}"; do
    q="${q//$w/ }"
  done

  q="$(printf '%s' "$q" | sed -E 's/[“”"‘’'"'"'（）()，,。.!！？?：:；;、/\\_-]+/ /g; s/[[:space:]]+/ /g')"
  q="$(trim "$q")"
  printf '%s' "$q"
}

pick_article_file() {
  local dir="$1"
  local f
  local preferred=()

  while IFS= read -r -d '' f; do
    local bn
    bn="$(basename "$f")"
    case "$bn" in
      draft.md|outline.md|notes.md|style.md)
        ;;
      *)
        preferred+=("$f")
        ;;
    esac
  done < <(find "$dir" -maxdepth 1 -type f -name '*.md' -print0)

  if [[ ${#preferred[@]} -gt 0 ]]; then
    printf '%s' "${preferred[0]}"
    return 0
  fi

  if [[ -f "$dir/draft.md" ]]; then
    printf '%s' "$dir/draft.md"
    return 0
  fi

  local fallback
  fallback="$(find "$dir" -maxdepth 1 -type f -name '*.md' | head -n 1 || true)"
  if [[ -n "$fallback" ]]; then
    printf '%s' "$fallback"
    return 0
  fi

  return 1
}

infer_title() {
  local article_dir="$1"
  local source_file="$2"

  local bn
  bn="$(basename "$source_file")"
  local name="${bn%.md}"

  if [[ "$name" == "draft" || "$name" == "" ]]; then
    name="$(basename "$article_dir")"
    # 去掉日期前缀：YYYY-MM-DD-
    name="$(printf '%s' "$name" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//')"
  fi

  if [[ -z "$name" ]]; then
    name="文章同步"
  fi

  truncate_27_chars "$name"
}

preprocess_markdown_for_import() {
  local input_file="$1"
  local output_file="$2"
  local mermaid_mode="$3"
  local mermaid_fmt="$4"
  local mermaid_base_url="$5"
  local latex_mode="$6"
  local latex_fmt="$7"
  local latex_base_url="$8"
  local mermaid_plain="$9"

  python3 - "$input_file" "$output_file" "$mermaid_mode" "$mermaid_fmt" "$mermaid_base_url" "$latex_mode" "$latex_fmt" "$latex_base_url" "$mermaid_plain" <<'PY'
import base64
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Optional

src_path, dst_path, mermaid_mode, mermaid_fmt, mermaid_base_url, latex_mode, latex_fmt, latex_base_url, mermaid_plain_raw = sys.argv[1:10]
src_file = Path(src_path)
src_dir = src_file.parent
text = src_file.read_text(encoding="utf-8")
text = text.replace("\r\n", "\n")
mermaid_plain = str(mermaid_plain_raw).lower() in {"1", "true", "yes", "on"}

if mermaid_mode not in {"external-image", "keep"}:
    raise SystemExit(f"unsupported mermaid mode: {mermaid_mode}")
if mermaid_fmt not in {"png", "svg"}:
    raise SystemExit(f"unsupported mermaid format: {mermaid_fmt}")
if latex_mode not in {"external-image", "keep"}:
    raise SystemExit(f"unsupported latex mode: {latex_mode}")
if latex_fmt not in {"png", "svg"}:
    raise SystemExit(f"unsupported latex format: {latex_fmt}")

mermaid_base_url = mermaid_base_url.rstrip("/")
latex_base_url = latex_base_url.rstrip("/")

fence_pattern = re.compile(r"```[^\n]*\n.*?\n```", re.DOTALL)
mermaid_fence_pattern = re.compile(r"^```mermaid[^\n]*\n(.*?)\n```$", re.IGNORECASE | re.DOTALL)

latex_block_dollar = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
latex_block_bracket = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
inline_latex = re.compile(r"(?<!\\)\$([^\n$]+?)(?<!\\)\$")
image_md = re.compile(r"!\[([^\]]*)\]\(([^)\n]+)\)")
styled_span = re.compile(r'<span\s+style="([^"]*)">(.*?)</span>', re.IGNORECASE | re.DOTALL)
div_tag = re.compile(r"</?div[^>]*>", re.IGNORECASE)

counts = {
    "mermaid": 0,
    "latex": 0,
    "local_images_seen": 0,
    "local_images_fixed": 0,
    "local_images_unresolved": 0,
    "styled_spans_converted": 0,
    "inline_svg_blocks": 0,
}
unresolved_local_images = []

def make_mermaid_url(code: str) -> str:
    if mermaid_plain:
        code = simplify_mermaid_code(code)
    encoded = base64.urlsafe_b64encode(code.encode("utf-8")).decode("ascii")
    if mermaid_fmt == "png":
        return f"{mermaid_base_url}/img/{encoded}?type=png&bgColor=transparent"
    return f"{mermaid_base_url}/svg/{encoded}"

def simplify_mermaid_code(code: str) -> str:
    lines = []
    for raw in code.splitlines():
        s = raw.strip()
        if s.startswith("classDef "):
            continue
        if s.startswith("class "):
            continue
        if s.startswith("style "):
            continue
        if s.startswith("linkStyle "):
            continue
        lines.append(raw)
    body = "\n".join(lines).strip("\n")
    if not body:
        body = "flowchart TD\n  A[\"流程\"]"
    init = "%%{init: {'theme':'neutral'}}%%"
    return f"{init}\n{body}"

def should_convert_inline(expr: str) -> bool:
    # 避免把普通金额或文本误判为公式
    return any(ch in expr for ch in ("\\", "^", "_", "=", "{", "}"))

def make_latex_url(expr: str) -> str:
    expr = expr.strip()
    if latex_fmt == "png":
        # codecogs 的 \bg_transparent 会产出绿底调色板图，这里改为默认透明背景
        payload = r"\dpi{220} " + expr
        return f"{latex_base_url}/png.image?{urllib.parse.quote(payload, safe='')}"
    return f"{latex_base_url}/svg.image?{urllib.parse.quote(expr, safe='')}"

def _resolve_local_image(target: str) -> Optional[Path]:
    target = target.strip()
    if not target:
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()

    lower = target.lower()
    if lower.startswith(("http://", "https://", "data:", "mailto:")):
        return None
    if target.startswith("#"):
        return None

    # 支持可选 title：![alt](path "title")
    path_part = target.split()[0]
    path_part = urllib.parse.unquote(path_part)
    path = Path(path_part)
    if not path.is_absolute():
        path = (src_dir / path).resolve()
    if not path.is_file():
        return None
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}:
        return None
    return path

def _try_fix_local_image(path: Path) -> Optional[str]:
    # 优先尝试用同名 .mmd 生成可外链的 Mermaid 图，规避 Lark MCP 当前不支持图片上传的问题。
    sidecar_mmd = path.with_suffix(".mmd")
    if sidecar_mmd.is_file():
        code = sidecar_mmd.read_text(encoding="utf-8").strip("\n")
        if code:
            counts["local_images_fixed"] += 1
            return make_mermaid_url(code)
    return None

def replace_local_images(segment: str) -> str:
    def repl(match):
        alt = match.group(1)
        target = match.group(2)
        local_path = _resolve_local_image(target)
        if local_path is None:
            return match.group(0)
        counts["local_images_seen"] += 1
        fixed_url = _try_fix_local_image(local_path)
        if fixed_url is not None:
            return f"![{alt}]({fixed_url})"
        counts["local_images_unresolved"] += 1
        unresolved_local_images.append(str(local_path))
        return match.group(0)
    return image_md.sub(repl, segment)

def replace_latex(segment: str) -> str:
    if latex_mode == "keep":
        return segment

    def repl_block(match):
        counts["latex"] += 1
        idx = counts["latex"]
        url = make_latex_url(match.group(1))
        return f"\n![公式{idx}]({url})\n"

    def repl_inline(match):
        expr = match.group(1).strip()
        if not should_convert_inline(expr):
            return match.group(0)
        counts["latex"] += 1
        idx = counts["latex"]
        url = make_latex_url(expr)
        return f"![公式{idx}]({url})"

    segment = latex_block_dollar.sub(repl_block, segment)
    segment = latex_block_bracket.sub(repl_block, segment)
    segment = inline_latex.sub(repl_inline, segment)
    return segment

def replace_styled_spans(segment: str) -> str:
    path_like_pattern = re.compile(r"^[A-Za-z0-9_./~{}:-]+$")

    def repl(match):
        style = (match.group(1) or "").lower()
        raw_text = match.group(2) or ""
        text = raw_text.strip()
        if not text:
            return ""

        counts["styled_spans_converted"] += 1
        # 路径与类代码术语优先转为行内 code，避免导入后丢失识别度。
        if "font-family:menlo" in style or "font-family:consolas" in style or "monospace" in style:
            cleaned = text.strip("`")
            return f"`{cleaned}`"
        # 仅对“短且纯路径/标识符”的文本启用 code，避免把整句误转为 code。
        if len(text) <= 80 and path_like_pattern.fullmatch(text) and any(ch in text for ch in ("/", "~", ".", "{", "}")):
            cleaned = text.strip("`")
            return f"`{cleaned}`"

        # 其余高亮回退为纯粗体，保持导入链路简单稳定。
        return f"**{text}**"

    segment = styled_span.sub(repl, segment)
    segment = div_tag.sub("", segment)
    return segment

pieces = []
last = 0
for m in fence_pattern.finditer(text):
    plain = text[last:m.start()]
    if plain:
        plain = replace_styled_spans(plain)
        pieces.append(replace_local_images(replace_latex(plain)))

    fence = m.group(0)
    mm = mermaid_fence_pattern.match(fence)
    if mm and mermaid_mode == "external-image":
        counts["mermaid"] += 1
        idx = counts["mermaid"]
        url = make_mermaid_url(mm.group(1).strip("\n"))
        pieces.append(f"![流程图{idx}]({url})")
    else:
        pieces.append(fence)
    last = m.end()

tail = text[last:]
if tail:
    tail = replace_styled_spans(tail)
    pieces.append(replace_local_images(replace_latex(tail)))

result = "".join(pieces)
counts["inline_svg_blocks"] = len(re.findall(r"<svg\b", result, re.IGNORECASE))
Path(dst_path).write_text(result, encoding="utf-8")
payload = dict(counts)
payload["unresolved_local_images"] = sorted(set(unresolved_local_images))
print(json.dumps(payload, ensure_ascii=False))
PY
}

score_article_dir() {
  local dir="$1"
  local query_raw="$2"
  local query_norm="$3"

  local base
  base="$(basename "$dir")"
  local score=0

  if [[ "$base" == _* ]]; then
    printf '%s' "-1"
    return 0
  fi

  # 原始短语命中加高权重
  if [[ -n "$query_raw" && "$base" == *"$query_raw"* ]]; then
    score=$((score + 100))
  fi
  if [[ -n "$query_norm" && "$base" == *"$query_norm"* ]]; then
    score=$((score + 80))
  fi

  # 分词命中
  local tok
  for tok in $query_norm; do
    [[ -z "$tok" ]] && continue
    if [[ "$base" == *"$tok"* ]]; then
      score=$((score + 20))
    fi
  done

  # 目录内文件名辅助匹配
  local f
  while IFS= read -r -d '' f; do
    local bn
    bn="$(basename "$f")"
    if [[ -n "$query_raw" && "$bn" == *"$query_raw"* ]]; then
      score=$((score + 30))
    fi
    if [[ -n "$query_norm" && "$bn" == *"$query_norm"* ]]; then
      score=$((score + 20))
    fi
  done < <(find "$dir" -maxdepth 1 -type f -name '*.md' -print0)

  printf '%s' "$score"
}

upsert_yaml_kv() {
  local file="$1"
  local key="$2"
  local value="$3"

  local escaped
  escaped="${value//\\/\\\\}"
  escaped="${escaped//\"/\\\"}"

  if [[ ! -f "$file" ]]; then
    printf '%s: "%s"\n' "$key" "$escaped" > "$file"
    return 0
  fi

  if grep -qE "^${key}:" "$file"; then
    sed -i '' -E "s#^${key}:.*#${key}: \"${escaped}\"#" "$file"
  else
    printf '\n%s: "%s"\n' "$key" "$escaped" >> "$file"
  fi
}

print_reauth_hint() {
  local host="$1"
  local port="$2"
  local domain="$3"
  local scope="$4"

  err "检测到 Lark 用户令牌可能已过期，请先重新登录后重试同步。"
  err "注意：当前应用未申请 offline_access 时，不要在 scope 中包含 offline_access。"
  err "重登命令（将 <APP_ID>/<APP_SECRET> 替换为你的应用凭证）："
  printf '%s\n' "npx -y @larksuiteoapi/lark-mcp login -a <APP_ID> -s <APP_SECRET> -d ${domain} --host ${host} -p ${port} --scope \"${scope}\"" >&2
}

CLIENT="codex"
SERVER_NAME="${LARK_MCP_SERVER_NAME:-lark}"
USE_UAT="true"
WRITE_METADATA="1"
DRY_RUN="0"
VERBOSE="0"
ARTICLES_DIR=""
TITLE_OVERRIDE=""
DIAGRAM_MODE="${WRITE_LARK_DIAGRAM_MODE:-external-image}"
DIAGRAM_FORMAT="${WRITE_LARK_DIAGRAM_FORMAT:-png}"
MERMAID_BASE_URL="${WRITE_LARK_MERMAID_BASE_URL:-https://mermaid.ink}"
LATEX_MODE="${WRITE_LARK_LATEX_MODE:-external-image}"
LATEX_FORMAT="${WRITE_LARK_LATEX_FORMAT:-png}"
LATEX_BASE_URL="${WRITE_LARK_LATEX_BASE_URL:-https://latex.codecogs.com}"
MERMAID_PLAIN="${WRITE_LARK_MERMAID_PLAIN:-true}"
OAUTH_HOST="${WRITE_LARK_OAUTH_HOST:-127.0.0.1}"
OAUTH_PORT="${WRITE_LARK_OAUTH_PORT:-3000}"
OAUTH_DOMAIN="${WRITE_LARK_OAUTH_DOMAIN:-https://open.larksuite.com}"
OAUTH_SCOPE="${WRITE_LARK_OAUTH_SCOPE:-docs:doc drive:drive docs:document.media:upload}"
AUTO_REAUTH_ON_EXPIRED_TOKEN="${WRITE_LARK_AUTO_REAUTH:-true}"
LARK_APP_ID="${WRITE_LARK_APP_ID:-}"
LARK_APP_SECRET="${WRITE_LARK_APP_SECRET:-}"
QUERY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --articles-dir|--article-root)
      ARTICLES_DIR="$2"; shift 2 ;;
    --server-name)
      SERVER_NAME="$2"; shift 2 ;;
    --client)
      CLIENT="$2"; shift 2 ;;
    --title)
      TITLE_OVERRIDE="$2"; shift 2 ;;
    --auto-reauth)
      AUTO_REAUTH_ON_EXPIRED_TOKEN="$2"; shift 2 ;;
    --lark-app-id)
      LARK_APP_ID="$2"; shift 2 ;;
    --lark-app-secret)
      LARK_APP_SECRET="$2"; shift 2 ;;
    --diagram-mode)
      DIAGRAM_MODE="$2"; shift 2 ;;
    --diagram-format)
      DIAGRAM_FORMAT="$2"; shift 2 ;;
    --mermaid-base-url)
      MERMAID_BASE_URL="$2"; shift 2 ;;
    --mermaid-plain)
      MERMAID_PLAIN="$2"; shift 2 ;;
    --latex-mode)
      LATEX_MODE="$2"; shift 2 ;;
    --latex-format)
      LATEX_FORMAT="$2"; shift 2 ;;
    --latex-base-url)
      LATEX_BASE_URL="$2"; shift 2 ;;
    --use-uat)
      USE_UAT="$2"; shift 2 ;;
    --no-metadata)
      WRITE_METADATA="0"; shift ;;
    --dry-run)
      DRY_RUN="1"; shift ;;
    -v|--verbose)
      VERBOSE="1"; shift ;;
    -h|--help)
      usage; exit 0 ;;
    --)
      shift
      QUERY="$*"
      break ;;
    *)
      if [[ -z "$QUERY" ]]; then
        QUERY="$1"
      else
        QUERY+=" $1"
      fi
      shift ;;
  esac
done

normalize_bool() {
  local raw="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | xargs)"
  case "$raw" in
    1|true|yes|y|on) printf '1' ;;
    0|false|no|n|off) printf '0' ;;
    *)
      err "非法布尔值: $1（期望 true/false）"
      exit 1
      ;;
  esac
}

is_auth_error() {
  local msg="$1"
  printf '%s' "$msg" | grep -qiE 'invalid or expired|access_token|unauthorized|reauthorize|authorization'
}

run_auto_lark_login() {
  if ! command -v npx >/dev/null 2>&1; then
    err "自动重登失败：未找到 npx 命令"
    return 1
  fi

  local cmd=(
    npx -y @larksuiteoapi/lark-mcp login
    -d "$OAUTH_DOMAIN"
    --host "$OAUTH_HOST"
    -p "$OAUTH_PORT"
    --scope "$OAUTH_SCOPE"
  )

  if [[ -n "$LARK_APP_ID" && -n "$LARK_APP_SECRET" ]]; then
    cmd+=(-a "$LARK_APP_ID" -s "$LARK_APP_SECRET")
    log "检测到令牌异常，自动拉起 Lark MCP 登录（使用显式 App 凭证）..."
  else
    log "检测到令牌异常，自动拉起 Lark MCP 登录（使用本地已配置凭证）..."
  fi

  "${cmd[@]}"
}

QUERY="$(trim "$QUERY")"
if [[ -z "$QUERY" ]]; then
  err "缺少自然语言指令，例如：同步提示词指导的文章"
  usage
  exit 1
fi

AUTO_REAUTH_ON_EXPIRED_TOKEN="$(normalize_bool "$AUTO_REAUTH_ON_EXPIRED_TOKEN")"

if [[ -z "$ARTICLES_DIR" ]]; then
  if ! ARTICLES_DIR="$(detect_articles_dir)"; then
    err "无法自动定位文章集合目录，请使用 --articles-dir 或 WRITE_LARK_ARTICLES_DIR 显式指定"
    exit 1
  fi
fi

if [[ ! -d "$ARTICLES_DIR" ]]; then
  err "文章集合目录不存在: $ARTICLES_DIR"
  exit 1
fi

if [[ "$CLIENT" != "codex" ]]; then
  err "当前脚本仅支持 --client codex"
  exit 1
fi

if [[ "$DIAGRAM_MODE" != "external-image" && "$DIAGRAM_MODE" != "keep" ]]; then
  err "不支持的 --diagram-mode: $DIAGRAM_MODE（可选: external-image|keep）"
  exit 1
fi

if [[ "$DIAGRAM_FORMAT" != "png" && "$DIAGRAM_FORMAT" != "svg" ]]; then
  err "不支持的 --diagram-format: $DIAGRAM_FORMAT（可选: png|svg）"
  exit 1
fi

if [[ "$LATEX_MODE" != "external-image" && "$LATEX_MODE" != "keep" ]]; then
  err "不支持的 --latex-mode: $LATEX_MODE（可选: external-image|keep）"
  exit 1
fi

if [[ "$LATEX_FORMAT" != "png" && "$LATEX_FORMAT" != "svg" ]]; then
  err "不支持的 --latex-format: $LATEX_FORMAT（可选: png|svg）"
  exit 1
fi

MERMAID_PLAIN="$(normalize_bool "$MERMAID_PLAIN")"

if ! command -v codex >/dev/null 2>&1; then
  err "未找到 codex 命令"
  exit 1
fi

query_norm="$(normalize_query "$QUERY")"
if [[ -z "$query_norm" ]]; then
  query_norm="$QUERY"
fi

best_score=-1
best_dir=""

while IFS= read -r -d '' dir; do
  score="$(score_article_dir "$dir" "$QUERY" "$query_norm")"
  if [[ "$VERBOSE" == "1" ]]; then
    log "候选: $(basename "$dir") | score=$score"
  fi

  if (( score > best_score )); then
    best_score=$score
    best_dir="$dir"
  fi
done < <(find "$ARTICLES_DIR" -mindepth 1 -maxdepth 1 -type d -print0)

if [[ -z "$best_dir" || "$best_score" -le 0 ]]; then
  err "没有找到匹配文章。查询词：$QUERY"
  log "可选目录："
  find "$ARTICLES_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sed 's/^/- /'
  exit 1
fi

if ! source_file="$(pick_article_file "$best_dir")"; then
  err "目录中没有可同步的 markdown 文件: $best_dir"
  exit 1
fi

if [[ -n "$TITLE_OVERRIDE" ]]; then
  title="$(truncate_27_chars "$TITLE_OVERRIDE")"
else
  title="$(infer_title "$best_dir" "$source_file")"
fi

log "匹配文章目录: $best_dir"
log "同步文件: $source_file"
log "导入标题: $title"

if [[ "$DRY_RUN" == "1" ]]; then
  log "dry-run 模式，未执行导入"
  exit 0
fi

project_root="$(dirname "$ARTICLES_DIR")"
out_file="$(mktemp)"
schema_file="$(mktemp)"
import_file="$(mktemp)"

cleanup_tmp() {
  rm -f "$out_file" "$schema_file" "$import_file"
}

if ! preprocess_stats="$(preprocess_markdown_for_import "$source_file" "$import_file" "$DIAGRAM_MODE" "$DIAGRAM_FORMAT" "$MERMAID_BASE_URL" "$LATEX_MODE" "$LATEX_FORMAT" "$LATEX_BASE_URL" "$MERMAID_PLAIN")"; then
  err "Markdown 预处理失败"
  cleanup_tmp
  exit 1
fi
log "兼容预处理仅作用于本次飞书导入临时文件，不会改动原始 markdown。"

mermaid_count="$(printf '%s' "$preprocess_stats" | jq -r '.mermaid // 0' 2>/dev/null || echo 0)"
latex_count="$(printf '%s' "$preprocess_stats" | jq -r '.latex // 0' 2>/dev/null || echo 0)"
local_images_fixed_count="$(printf '%s' "$preprocess_stats" | jq -r '.local_images_fixed // 0' 2>/dev/null || echo 0)"
local_images_unresolved_count="$(printf '%s' "$preprocess_stats" | jq -r '.local_images_unresolved // 0' 2>/dev/null || echo 0)"
styled_spans_converted_count="$(printf '%s' "$preprocess_stats" | jq -r '.styled_spans_converted // 0' 2>/dev/null || echo 0)"
inline_svg_blocks_count="$(printf '%s' "$preprocess_stats" | jq -r '.inline_svg_blocks // 0' 2>/dev/null || echo 0)"

if [[ "${mermaid_count:-0}" =~ ^[0-9]+$ ]] && (( mermaid_count > 0 )); then
  log "检测到 Mermaid 代码块 ${mermaid_count} 个，已转换为外站透明底流程图（${DIAGRAM_FORMAT}）"
  log "Mermaid 外站: ${MERMAID_BASE_URL}"
  if [[ "$MERMAID_PLAIN" == "1" ]]; then
    log "Mermaid 导图模式：朴素风格（已移除 class/style 颜色定义）"
  fi
fi

if [[ "${latex_count:-0}" =~ ^[0-9]+$ ]] && (( latex_count > 0 )); then
  log "检测到 LaTeX 公式 ${latex_count} 处，已转换为外站透明底公式图（${LATEX_FORMAT}）"
  log "LaTeX 外站: ${LATEX_BASE_URL}"
fi

if [[ "${local_images_fixed_count:-0}" =~ ^[0-9]+$ ]] && (( local_images_fixed_count > 0 )); then
  log "检测到本地图片 ${local_images_fixed_count} 个，已自动修复为可访问外链（基于同名 .mmd 生成 Mermaid 图）"
fi

if [[ "${styled_spans_converted_count:-0}" =~ ^[0-9]+$ ]] && (( styled_spans_converted_count > 0 )); then
  log "检测到样式高亮 ${styled_spans_converted_count} 处，已自动转换为 Lark 可保留的强调格式"
fi

if [[ "${local_images_unresolved_count:-0}" =~ ^[0-9]+$ ]] && (( local_images_unresolved_count > 0 )); then
  err "检测到本地图片 ${local_images_unresolved_count} 个无法自动修复，已触发门禁，避免导入后丢图。"
  err "请将下列图片替换为 https 外链，或提供同名 .mmd 以便自动转 Mermaid 外链："
  printf '%s' "$preprocess_stats" | jq -r '.unresolved_local_images[]?' | sed 's/^/- /' >&2 || true
  cleanup_tmp
  exit 1
fi

if [[ "${inline_svg_blocks_count:-0}" =~ ^[0-9]+$ ]] && (( inline_svg_blocks_count > 0 )); then
  err "检测到内嵌 SVG ${inline_svg_blocks_count} 处。Lark 导入会清洗其样式并导致展示异常。"
  err "请将内嵌 SVG 改为 Mermaid 代码块（推荐）或可访问的 https 图片后重试。"
  cleanup_tmp
  exit 1
fi

cat > "$schema_file" <<'JSON'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["status", "article_dir", "source_file", "title", "import_status", "token", "url", "error"],
  "properties": {
    "status": {"type": "string", "enum": ["ok", "failed"]},
    "article_dir": {"type": "string"},
    "source_file": {"type": "string"},
    "title": {"type": "string"},
    "import_status": {"type": "string"},
    "token": {"type": "string"},
    "url": {"type": "string"},
    "error": {"type": "string"}
  },
  "additionalProperties": false
}
JSON

read -r -d '' prompt <<PROMPT || true
你是文章同步助手。请完成一次 Lark 文档导入，并且只返回 JSON 对象。

硬性要求：
1) 仅允许执行一次 shell 读取命令：cat ${import_file} 。禁止执行任何其他 shell 命令。
2) 优先使用名为 "${SERVER_NAME}" 的 MCP 服务器中的工具 docx.builtin.import。
3) 读取文件 ${import_file} 的全文作为 markdown 内容。
4) 调用参数：
   - data.markdown: 文件全文
   - data.file_name: "${title}"
   - useUAT: ${USE_UAT}
5) 最终只输出一个 JSON 对象，不要加代码块。
6) 严禁执行以下无关操作：spawn_agent、list_mcp_resources、npx、codex mcp、任何网络探测或环境探测。
7) 若导入失败，直接返回 failed JSON，不要重试，不要输出额外说明。

返回格式：
{
  "status": "ok" 或 "failed",
  "article_dir": "${best_dir}",
  "source_file": "${source_file}",
  "title": "${title}",
  "import_status": "success 或 failed",
  "token": "文档 token，失败时为空字符串",
  "url": "文档链接，失败时为空字符串",
  "error": "错误原因，成功时为空字符串"
}
PROMPT

log "开始调用 Codex + MCP 导入..."

run_import_once() {
  if ! codex exec \
    --skip-git-repo-check \
    -C "$project_root" \
    --output-schema "$schema_file" \
    --output-last-message "$out_file" \
    "$prompt"; then
    status="failed"
    url=""
    token=""
    import_status="failed"
    error_msg="codex exec failed"
    return 1
  fi

  if ! jq -e . "$out_file" >/dev/null 2>&1; then
    status="failed"
    url=""
    token=""
    import_status="failed"
    error_msg="invalid json output from codex exec"
    return 1
  fi

  status="$(jq -r '.status' "$out_file")"
  url="$(jq -r '.url' "$out_file")"
  token="$(jq -r '.token' "$out_file")"
  import_status="$(jq -r '.import_status' "$out_file")"
  error_msg="$(jq -r '.error' "$out_file")"

  [[ "$status" == "ok" && -n "$url" ]]
}

status="failed"
url=""
token=""
import_status="failed"
error_msg=""
attempt=1
max_attempts=2

while true; do
  if run_import_once; then
    break
  fi

  err "同步失败: ${error_msg:-unknown error}"

  if [[ "$AUTO_REAUTH_ON_EXPIRED_TOKEN" == "1" ]] && (( attempt < max_attempts )) && is_auth_error "${error_msg:-}"; then
    if run_auto_lark_login; then
      attempt=$((attempt + 1))
      log "Lark MCP 登录成功，开始重试导入（第 ${attempt} 次）..."
      continue
    fi
    print_reauth_hint "$OAUTH_HOST" "$OAUTH_PORT" "$OAUTH_DOMAIN" "$OAUTH_SCOPE"
  elif is_auth_error "${error_msg:-}"; then
    print_reauth_hint "$OAUTH_HOST" "$OAUTH_PORT" "$OAUTH_DOMAIN" "$OAUTH_SCOPE"
  fi

  if [[ -s "$out_file" ]]; then
    cat "$out_file"
  fi
  cleanup_tmp
  exit 1
done

if [[ "$status" == "ok" && -n "$url" ]]; then
  log "同步成功"
  log "文档链接: $url"
  log "文档 token: $token"

  if [[ "$WRITE_METADATA" == "1" ]]; then
    metadata_file="$best_dir/metadata.yaml"
    upsert_yaml_kv "$metadata_file" "lark_doc_url" "$url"
    upsert_yaml_kv "$metadata_file" "lark_doc_token" "$token"
    upsert_yaml_kv "$metadata_file" "lark_import_status" "$import_status"
    upsert_yaml_kv "$metadata_file" "lark_sync_at" "$(date '+%Y-%m-%d %H:%M:%S')"
    log "已回写 metadata: $metadata_file"
  fi
fi

# 固定收尾输出，便于在任何调用链中稳定提取 Lark 地址
printf 'LARK_DOC_URL=%s\n' "$url"
printf 'LARK_DOC_TOKEN=%s\n' "$token"
printf 'LARK_IMPORT_STATUS=%s\n' "$import_status"

cat "$out_file"
cleanup_tmp
