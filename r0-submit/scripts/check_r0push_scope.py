#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOWED_PREFIXES = ("r0/",)
ALLOWED_EXACT = {".gitignore"}
ALLOWED_LEGACY_PREFIX = "r0-"


@dataclass
class Item:
    staged: str
    unstaged: str
    path: str


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo_root), *args], check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "git failed")
    return completed.stdout


def is_allowed(path: str) -> bool:
    if path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES):
        return True
    return path.split("/", 1)[0].startswith(ALLOWED_LEGACY_PREFIX)


def parse_status(repo_root: Path) -> list[Item]:
    items: list[Item] = []
    for raw in run_git(repo_root, "status", "--porcelain=v1").splitlines():
      if not raw:
        continue
      body = raw[3:]
      path = body.split(" -> ", 1)[1] if " -> " in body else body
      items.append(Item(staged=raw[0], unstaged=raw[1], path=path))
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    top = Path(run_git(repo_root, "rev-parse", "--show-toplevel").strip())
    items = parse_status(top)

    staged = sorted({item.path for item in items if item.staged not in {" ", "?"}})
    dirty = sorted({item.path for item in items if item.unstaged != " " or item.staged == "?"})
    blocked = sorted({path for path in dirty if not is_allowed(path)})

    print(f"repo_root={top}")
    print(f"staged_count={len(staged)}")
    print(f"dirty_count={len(dirty)}")
    print("staged_paths:")
    for path in staged or ["<none>"]:
        print(f"- {path}")
    print("dirty_paths:")
    for path in dirty or ["<none>"]:
        print(f"- {path}")

    if not staged:
        print("[BLOCK] 当前没有 staged 改动，不能安全调用 r0push。")
        return 2
    if blocked:
        print("[BLOCK] 检测到超出允许范围的未提交工作区改动，不能假设 r0push 只提交 staged 内容。")
        print("blocked_paths:")
        for path in blocked:
            print(f"- {path}")
        return 3
    print("[OK] 未发现超出允许范围的工作区脏改动；若继续调用 r0push，仍应先复核 git diff --cached。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
