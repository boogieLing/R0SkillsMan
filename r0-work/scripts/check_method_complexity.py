#!/usr/bin/env python3
"""检查方法长度、分支复杂度和嵌套深度是否超标。"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_SUFFIXES = {".go", ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".swift", ".rs"}

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
class ComplexityFinding:
    path: Path
    name: str
    start_line: int
    total_lines: int
    branch_signals: int
    max_nesting: int
    reasons: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查方法长度、圈复杂度和嵌套深度")
    parser.add_argument("--scope", choices=("changed", "all"), default="changed")
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--max-lines", type=int, default=80)
    parser.add_argument("--max-branches", type=int, default=10)
    parser.add_argument("--max-nesting", type=int, default=4)
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


def analyze_python_block(lines: list[str], start: int, name: str) -> ComplexityFinding | None:
    base_indent = len(lines[start]) - len(lines[start].lstrip())
    body_start = start + 1
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    if body_start >= len(lines):
        return None
    end = body_start
    max_nesting = 0
    while end < len(lines):
        line = lines[end]
        if line.strip():
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent and not line.lstrip().startswith(("@", "#")):
                break
            nesting = max(0, (indent - base_indent) // 4)
            max_nesting = max(max_nesting, nesting)
        end += 1
    body_lines = lines[body_start:end]
    branch_signals = sum(1 for line in body_lines if BRANCH_PATTERNS[".py"].search(line))
    return ComplexityFinding(
        path=Path(),
        name=name,
        start_line=start + 1,
        total_lines=end - start,
        branch_signals=branch_signals,
        max_nesting=max_nesting,
        reasons=(),
    )


def analyze_brace_block(lines: list[str], start: int, name: str, suffix: str) -> ComplexityFinding | None:
    depth = 0
    seen_open = False
    max_nesting = 0
    body_start = None
    for idx in range(start, len(lines)):
        line = lines[idx]
        for ch in line:
            if ch == "{":
                depth += 1
                if not seen_open:
                    seen_open = True
                    body_start = idx + 1
                else:
                    max_nesting = max(max_nesting, depth - 1)
            elif ch == "}":
                if seen_open:
                    max_nesting = max(max_nesting, depth - 1)
                depth -= 1
                if seen_open and depth == 0:
                    end = idx + 1
                    if body_start is None:
                        return None
                    body_lines = lines[body_start:end - 1]
                    branch_signals = sum(1 for body_line in body_lines if BRANCH_PATTERNS[suffix].search(body_line))
                    return ComplexityFinding(
                        path=Path(),
                        name=name,
                        start_line=start + 1,
                        total_lines=end - start,
                        branch_signals=branch_signals,
                        max_nesting=max_nesting,
                        reasons=(),
                    )
        if seen_open and depth < 0:
            return None
    return None


def collect_findings(path: Path, args: argparse.Namespace) -> list[ComplexityFinding]:
    lines = path.read_text(encoding="utf-8").splitlines()
    findings: list[ComplexityFinding] = []
    for idx, line in enumerate(lines):
        name = match_definition(line, path.suffix)
        if not name:
            continue
        if path.suffix == ".py":
            item = analyze_python_block(lines, idx, name)
        else:
            item = analyze_brace_block(lines, idx, name, path.suffix)
        if not item:
            continue

        reasons: list[str] = []
        if item.total_lines > args.max_lines:
            reasons.append(f"lines={item.total_lines}>{args.max_lines}")
        if item.branch_signals > args.max_branches:
            reasons.append(f"branches={item.branch_signals}>{args.max_branches}")
        if item.max_nesting > args.max_nesting:
            reasons.append(f"nesting={item.max_nesting}>{args.max_nesting}")
        if not reasons:
            continue

        findings.append(
            ComplexityFinding(
                path=path,
                name=item.name,
                start_line=item.start_line,
                total_lines=item.total_lines,
                branch_signals=item.branch_signals,
                max_nesting=item.max_nesting,
                reasons=tuple(reasons),
            )
        )
    return findings


def main() -> int:
    args = parse_args()
    repo_root = resolve_git_root()
    files = collect_candidate_files(repo_root, args)
    candidates = [path for path in files if path.exists() and path.suffix in SUPPORTED_SUFFIXES]
    findings: list[ComplexityFinding] = []

    for path in candidates:
        findings.extend(collect_findings(path, args))

    if not findings:
        print("COMPLEXITY_STATUS=PASS")
        print("FINDING_COUNT=0")
        return 0

    print("COMPLEXITY_STATUS=FAIL")
    print(f"FINDING_COUNT={len(findings)}")
    for finding in findings:
        reasons = ", ".join(finding.reasons)
        print(
            f"FINDING: {finding.path}:{finding.start_line} {finding.name} "
            f"(lines={finding.total_lines}, branches={finding.branch_signals}, nesting={finding.max_nesting}) "
            f"=> {reasons}"
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
