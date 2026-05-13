#!/usr/bin/env python3
"""检查复杂方法内部是否缺少关键逻辑注释。"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


COMMENT_PREFIXES = {
    ".go": ("//", "/*", "*"),
    ".py": ("#",),
    ".js": ("//", "/*", "*"),
    ".jsx": ("//", "/*", "*"),
    ".ts": ("//", "/*", "*"),
    ".tsx": ("//", "/*", "*"),
    ".java": ("//", "/*", "*"),
    ".swift": ("//", "/*", "*"),
    ".rs": ("//", "/*", "*"),
}

SUPPORTED_SUFFIXES = set(COMMENT_PREFIXES)

GO_PATTERN = re.compile(
    r"^\s*func\s*(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]+\])?\s*\("
)
PY_PATTERN = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
JS_FUNC_PATTERN = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\("
)
JS_EXPR_PATTERN = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:(?:async\s+)?function\s*\(|(?:async\s*)?\([^)]*\)\s*=>|(?:async\s+)?[A-Za-z_$][A-Za-z0-9_$]*\s*=>)"
)
JS_METHOD_PATTERN = re.compile(
    r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|async\s+|readonly\s+|abstract\s+|override\s+|get\s+|set\s+)*([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^;{}]*\)\s*\{\s*$"
)
JAVA_METHOD_PATTERN = re.compile(
    r"^\s*(?:public|protected|private|static|final|native|synchronized|abstract|default|strictfp)"
    r"(?:\s+(?:public|protected|private|static|final|native|synchronized|abstract|default|strictfp))*"
    r"\s+[A-Za-z_][A-Za-z0-9_<>,\[\]? ]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)"
    r"\s*(?:throws\s+[A-Za-z0-9_,\s.]+)?\s*\{\s*$"
)
SWIFT_FUNC_PATTERN = re.compile(
    r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*"
    r"(?:(?:public|private|fileprivate|internal|open|final|override|mutating|nonmutating|static|class|convenience|required|indirect|actorisolated|isolated|async|throws|rethrows)\s+)*"
    r"func\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]+>)?\s*\("
)
RUST_FUNC_PATTERN = re.compile(
    r'^\s*(?:(?:pub(?:\([^)]*\))?|async|const|unsafe|extern\s+"[^"]+"|default)\s+)*'
    r"fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]+>)?\s*\("
)

BRANCH_PATTERNS = {
    ".go": re.compile(r"\b(if|for|switch|case|select)\b|&&|\|\|"),
    ".py": re.compile(r"\b(if|elif|for|while|match|case|except)\b| and | or "),
    ".js": re.compile(r"\b(if|else if|for|while|switch|case|catch)\b|&&|\|\|"),
    ".jsx": re.compile(r"\b(if|else if|for|while|switch|case|catch)\b|&&|\|\|"),
    ".ts": re.compile(r"\b(if|else if|for|while|switch|case|catch)\b|&&|\|\|"),
    ".tsx": re.compile(r"\b(if|else if|for|while|switch|case|catch)\b|&&|\|\|"),
    ".java": re.compile(r"\b(if|else if|for|while|switch|case|catch)\b|&&|\|\|"),
    ".swift": re.compile(r"\b(if|guard|for|while|switch|case|catch)\b|&&|\|\|"),
    ".rs": re.compile(r"\b(if|match|for|while|loop)\b|&&|\|\|"),
}


@dataclass(frozen=True)
class FunctionBlock:
    name: str
    start_line: int
    total_lines: int
    branch_signals: int
    has_internal_comment: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查复杂方法内部是否缺少逻辑注释")
    parser.add_argument("--scope", choices=("changed", "all"), default="changed")
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--min-lines", type=int, default=12)
    parser.add_argument("--min-branches", type=int, default=2)
    return parser.parse_args()


def run_git(args: list[str], cwd: Path) -> list[str]:
    result = subprocess.run(["git", *args], cwd=str(cwd), check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} 执行失败")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def resolve_git_root() -> Path | None:
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def collect_candidate_files(repo_root: Path | None, args: argparse.Namespace) -> list[Path]:
    if args.files:
        base = Path.cwd()
        return sorted((base / path).resolve() for path in args.files)
    if repo_root is None:
        raise RuntimeError("当前目录不在 git 仓库中，请使用 --files 显式指定文件")
    if args.scope == "all":
        rel_paths = set(run_git(["ls-files"], cwd=repo_root))
    else:
        rel_paths = set(run_git(["diff", "--name-only"], cwd=repo_root))
        rel_paths |= set(run_git(["diff", "--cached", "--name-only"], cwd=repo_root))
        rel_paths |= set(run_git(["ls-files", "--others", "--exclude-standard"], cwd=repo_root))
    return sorted((repo_root / rel).resolve() for rel in rel_paths)


def match_definition(line: str, suffix: str) -> str | None:
    if suffix == ".go":
        match = GO_PATTERN.match(line)
    elif suffix == ".py":
        match = PY_PATTERN.match(line)
    elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
        match = JS_FUNC_PATTERN.match(line) or JS_EXPR_PATTERN.match(line) or JS_METHOD_PATTERN.match(line)
    elif suffix == ".java":
        match = JAVA_METHOD_PATTERN.match(line)
    elif suffix == ".swift":
        match = SWIFT_FUNC_PATTERN.match(line)
    elif suffix == ".rs":
        match = RUST_FUNC_PATTERN.match(line)
    else:
        match = None
    return match.group(1) if match else None


def is_comment_line(line: str, suffix: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return any(stripped.startswith(prefix) for prefix in COMMENT_PREFIXES[suffix])


def analyze_python_block(lines: list[str], start: int, name: str) -> FunctionBlock | None:
    base_indent = len(lines[start]) - len(lines[start].lstrip())
    body_start = start + 1
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    if body_start >= len(lines):
        return None
    end = body_start
    while end < len(lines):
        line = lines[end]
        if line.strip():
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent and not line.lstrip().startswith(("@", "#")):
                break
        end += 1
    body_lines = lines[body_start:end]
    branch_signals = sum(1 for line in body_lines if BRANCH_PATTERNS[".py"].search(line))
    has_comment = any(is_comment_line(line, ".py") for line in body_lines)
    return FunctionBlock(name=name, start_line=start + 1, total_lines=end - start, branch_signals=branch_signals, has_internal_comment=has_comment)


def analyze_brace_block(lines: list[str], start: int, name: str, suffix: str) -> FunctionBlock | None:
    depth = 0
    seen_open = False
    body_start = None
    for idx in range(start, len(lines)):
        line = lines[idx]
        for ch in line:
            if ch == "{":
                depth += 1
                if not seen_open:
                    seen_open = True
                    body_start = idx + 1
            elif ch == "}":
                depth -= 1
                if seen_open and depth == 0:
                    end = idx + 1
                    if body_start is None:
                        return None
                    body_lines = lines[body_start:end - 1]
                    branch_signals = sum(1 for body_line in body_lines if BRANCH_PATTERNS[suffix].search(body_line))
                    has_comment = any(is_comment_line(body_line, suffix) for body_line in body_lines)
                    return FunctionBlock(name=name, start_line=start + 1, total_lines=end - start, branch_signals=branch_signals, has_internal_comment=has_comment)
        if seen_open and depth < 0:
            return None
    return None


def collect_blocks(path: Path) -> list[FunctionBlock]:
    suffix = path.suffix
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[FunctionBlock] = []
    for idx, line in enumerate(lines):
        name = match_definition(line, suffix)
        if not name:
            continue
        if suffix == ".py":
            block = analyze_python_block(lines, idx, name)
        else:
            block = analyze_brace_block(lines, idx, name, suffix)
        if block:
            blocks.append(block)
    return blocks


def main() -> int:
    args = parse_args()
    repo_root = resolve_git_root()
    files = collect_candidate_files(repo_root, args)
    candidates = [path for path in files if path.exists() and path.suffix in SUPPORTED_SUFFIXES]
    findings: list[str] = []

    for path in candidates:
        for block in collect_blocks(path):
            if block.total_lines < args.min_lines and block.branch_signals < args.min_branches:
                continue
            if block.has_internal_comment:
                continue
            findings.append(
                f"{path}:{block.start_line} {block.name} 缺少方法内部逻辑注释 "
                f"(lines={block.total_lines}, branches={block.branch_signals})"
            )

    if not findings:
        print("LOGIC_COMMENT_STATUS=PASS")
        print("MISSING_COUNT=0")
        return 0

    print("LOGIC_COMMENT_STATUS=FAIL")
    print(f"MISSING_COUNT={len(findings)}")
    for finding in findings:
        print(f"MISSING: {finding}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
