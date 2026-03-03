#!/usr/bin/env python3
"""检查并补齐函数/方法头部注释。"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LangSpec:
    single_comment_prefix: str
    line_comment_tokens: tuple[str, ...]
    block_comment_start: str | None = None
    block_comment_end: str | None = None


LANG_SPECS: dict[str, LangSpec] = {
    '.go': LangSpec('//', ('//',), '/*', '*/'),
    '.py': LangSpec('#', ('#',)),
    '.js': LangSpec('//', ('//',), '/*', '*/'),
    '.jsx': LangSpec('//', ('//',), '/*', '*/'),
    '.ts': LangSpec('//', ('//',), '/*', '*/'),
    '.tsx': LangSpec('//', ('//',), '/*', '*/'),
    '.java': LangSpec('//', ('//',), '/*', '*/'),
}

GO_PATTERN = re.compile(
    r'^\s*func\s*(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]+\])?\s*\('
)
PY_PATTERN = re.compile(r'^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(')
JS_FUNC_PATTERN = re.compile(
    r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\('
)
JS_EXPR_PATTERN = re.compile(
    r'^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:(?:async\s+)?function\s*\(|(?:async\s*)?\([^)]*\)\s*=>|(?:async\s+)?[A-Za-z_$][A-Za-z0-9_$]*\s*=>)'
)
JS_METHOD_PATTERN = re.compile(
    r'^\s*(?:public\s+|private\s+|protected\s+|static\s+|async\s+|readonly\s+|abstract\s+|override\s+|get\s+|set\s+)*([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^;{}]*\)\s*\{\s*$'
)
JAVA_METHOD_PATTERN = re.compile(
    r'^\s*(?:public|protected|private|static|final|native|synchronized|abstract|default|strictfp)'
    r'(?:\s+(?:public|protected|private|static|final|native|synchronized|abstract|default|strictfp))*'
    r'\s+[A-Za-z_][A-Za-z0-9_<>,\[\]? ]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)'
    r'\s*(?:throws\s+[A-Za-z0-9_,\s.]+)?\s*\{\s*$'
)

JS_BLOCK_KEYWORDS = {
    'if',
    'for',
    'while',
    'switch',
    'catch',
    'else',
    'do',
    'try',
    'finally',
}


@dataclass(frozen=True)
class Definition:
    name: str
    line_index: int
    decl_start_index: int


@dataclass(frozen=True)
class MissingComment:
    name: str
    line_index: int
    insert_index: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='检查并补齐方法头部注释')
    parser.add_argument(
        '--scope',
        choices=('changed', 'all'),
        default='changed',
        help='changed: 仅检查 git 变更文件; all: 检查 git 跟踪文件',
    )
    parser.add_argument(
        '--files',
        nargs='*',
        default=[],
        help='显式传入待检查文件，传入后优先于 --scope',
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='自动补齐缺失注释（默认仅检查）',
    )
    return parser.parse_args()


def run_git(args: list[str], cwd: Path) -> list[str]:
    result = subprocess.run(
        ['git', *args],
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"git {' '.join(args)} 执行失败: {stderr}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def resolve_git_root() -> Path | None:
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def collect_candidate_files(repo_root: Path | None, args: argparse.Namespace) -> list[Path]:
    if args.files:
        base = Path.cwd()
        return sorted((base / path).resolve() for path in args.files)

    if repo_root is None:
        raise RuntimeError('当前目录不在 git 仓库中，请使用 --files 显式指定文件')

    if args.scope == 'all':
        tracked = run_git(['ls-files'], cwd=repo_root)
        rel_paths = set(tracked)
    else:
        changed = run_git(['diff', '--name-only'], cwd=repo_root)
        staged = run_git(['diff', '--cached', '--name-only'], cwd=repo_root)
        untracked = run_git(['ls-files', '--others', '--exclude-standard'], cwd=repo_root)
        rel_paths = set(changed) | set(staged) | set(untracked)

    return sorted((repo_root / rel_path).resolve() for rel_path in rel_paths)


def is_supported_file(path: Path) -> bool:
    return path.suffix in LANG_SPECS


def should_skip_file(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith('.min.js') or name.endswith('.min.ts'):
        return True
    return False


def declaration_start(lines: list[str], line_index: int) -> int:
    idx = line_index
    while idx > 0:
        prev = lines[idx - 1].strip()
        if prev.startswith('@'):
            idx -= 1
            continue
        break
    return idx


def iter_definitions(lines: list[str], suffix: str) -> list[Definition]:
    definitions: list[Definition] = []
    for idx, line in enumerate(lines):
        match: re.Match[str] | None = None
        if suffix == '.go':
            match = GO_PATTERN.match(line)
        elif suffix == '.py':
            match = PY_PATTERN.match(line)
        elif suffix in {'.js', '.jsx', '.ts', '.tsx'}:
            match = JS_FUNC_PATTERN.match(line) or JS_EXPR_PATTERN.match(line) or JS_METHOD_PATTERN.match(line)
            if match and match.group(1) in JS_BLOCK_KEYWORDS:
                continue
        elif suffix == '.java':
            match = JAVA_METHOD_PATTERN.match(line)

        if not match:
            continue

        name = match.group(1)
        start_idx = declaration_start(lines, idx)
        definitions.append(Definition(name=name, line_index=idx, decl_start_index=start_idx))

    return definitions


def has_comment_above(lines: list[str], decl_index: int, spec: LangSpec) -> bool:
    idx = decl_index - 1
    while idx >= 0 and lines[idx].strip() == '':
        idx -= 1

    if idx < 0:
        return False

    stripped = lines[idx].lstrip()
    if any(stripped.startswith(token) for token in spec.line_comment_tokens):
        return True

    if spec.block_comment_end and stripped.endswith(spec.block_comment_end):
        walk = idx
        while walk >= 0:
            current = lines[walk].strip()
            if spec.block_comment_start and spec.block_comment_start in current:
                return True
            if current and not current.startswith('*') and spec.block_comment_end not in current:
                return False
            walk -= 1

    return False


def collect_missing_comments(path: Path) -> tuple[list[str], list[MissingComment]]:
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    spec = LANG_SPECS[path.suffix]

    missing: list[MissingComment] = []
    for definition in iter_definitions(lines, path.suffix):
        if has_comment_above(lines, definition.decl_start_index, spec):
            continue
        missing.append(
            MissingComment(
                name=definition.name,
                line_index=definition.line_index,
                insert_index=definition.decl_start_index,
            )
        )

    return lines, missing


def apply_missing_comments(path: Path, lines: list[str], missing: list[MissingComment]) -> None:
    spec = LANG_SPECS[path.suffix]
    updated = list(lines)

    for item in sorted(missing, key=lambda x: x.insert_index, reverse=True):
        indent = re.match(r'^\s*', updated[item.insert_index]).group(0)
        comment = f"{indent}{spec.single_comment_prefix} {item.name} TODO: 补充方法注释。\n"
        updated.insert(item.insert_index, comment)

    path.write_text(''.join(updated), encoding='utf-8')


def execute_task(args: argparse.Namespace) -> int:
    repo_root = resolve_git_root()
    files = collect_candidate_files(repo_root, args)

    supported_files = [path for path in files if path.exists() and is_supported_file(path) and not should_skip_file(path)]
    if not supported_files:
        print('未找到需要检查的受支持文件。')
        return 0

    total_missing = 0
    touched_files = 0

    for path in supported_files:
        try:
            lines, missing = collect_missing_comments(path)
        except UnicodeDecodeError:
            print(f'SKIP {path}: 非 UTF-8 文本，跳过')
            continue

        if not missing:
            continue

        touched_files += 1
        total_missing += len(missing)
        for item in missing:
            print(f'MISSING {path}:{item.line_index + 1} 方法 `{item.name}` 缺少头部注释')

        if args.apply:
            apply_missing_comments(path, lines, missing)
            print(f'FIXED {path}: 已补齐 {len(missing)} 处注释')

    print(
        f'检查完成: 文件 {len(supported_files)} 个, 缺失注释 {total_missing} 处, 受影响文件 {touched_files} 个, apply={args.apply}'
    )

    if total_missing > 0 and not args.apply:
        return 2
    return 0


def main() -> int:
    args = parse_args()
    try:
        return execute_task(args)
    except RuntimeError as err:
        print(f'ERROR: {err}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
