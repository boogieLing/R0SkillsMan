#!/usr/bin/env python3
"""Validate git scope before invoking r0push.

Purpose:
- Do not assume r0push only commits staged content.
- Block when the worktree still contains unrelated unstaged/untracked changes.
- Allow local record files (`r0/`, `r0-*/`) and `.gitignore` to remain outside the staged set.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ALLOWED_PREFIXES = ("r0/",)
ALLOWED_LEGACY_PREFIX = "r0-"
ALLOWED_EXACT = {".gitignore"}


@dataclass
class Item:
    staged: str
    unstaged: str
    path: str


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise RuntimeError(f"{' '.join(args)}: {stderr}")
    return completed.stdout


def is_allowed_local(path: str) -> bool:
    normalized = path.strip()
    if normalized in ALLOWED_EXACT:
        return True
    if normalized.startswith(ALLOWED_PREFIXES):
        return True
    first = normalized.split("/", 1)[0]
    return first.startswith(ALLOWED_LEGACY_PREFIX)


def parse_status(repo_root: Path) -> list[Item]:
    output = run_git(repo_root, "status", "--porcelain=v1")
    items: list[Item] = []
    for raw in output.splitlines():
        if not raw:
            continue
        staged = raw[0]
        unstaged = raw[1]
        body = raw[3:]
        if " -> " in body:
            path = body.split(" -> ", 1)[1]
        else:
            path = body
        items.append(Item(staged=staged, unstaged=unstaged, path=path))
    return items


def summarize(items: list[Item]) -> tuple[list[str], list[str], list[str]]:
    staged_paths: list[str] = []
    dirty_paths: list[str] = []
    blocked_paths: list[str] = []
    for item in items:
        if item.staged not in {" ", "?"}:
            staged_paths.append(item.path)
        if item.unstaged != " " or item.staged == "?":
            dirty_paths.append(item.path)
            if not is_allowed_local(item.path):
                blocked_paths.append(item.path)
    return sorted(set(staged_paths)), sorted(set(dirty_paths)), sorted(set(blocked_paths))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check submit scope before invoking r0push.")
    parser.add_argument("--repo-root", default=".", help="Git repository root or any path inside it.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    try:
        top = run_git(repo_root, "rev-parse", "--show-toplevel").strip()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1
    repo_root = Path(top)

    try:
        items = parse_status(repo_root)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    staged_paths, dirty_paths, blocked_paths = summarize(items)

    print(f"repo_root={repo_root}")
    print(f"staged_count={len(staged_paths)}")
    print(f"dirty_count={len(dirty_paths)}")

    if staged_paths:
        print("staged_paths:")
        for path in staged_paths:
            print(f"- {path}")
    else:
        print("staged_paths:\n- <none>")

    if dirty_paths:
        print("dirty_paths:")
        for path in dirty_paths:
            print(f"- {path}")
    else:
        print("dirty_paths:\n- <none>")

    if not staged_paths:
        print("[BLOCK] 当前没有 staged 改动，不能安全调用 r0push。")
        return 2

    if blocked_paths:
        print("[BLOCK] 检测到超出允许范围的未提交工作区改动，不能假设 r0push 只提交 staged 内容。")
        print("blocked_paths:")
        for path in blocked_paths:
            print(f"- {path}")
        return 3

    print("[OK] 未发现超出允许范围的工作区脏改动；若继续调用 r0push，仍应先复核 git diff --cached。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
