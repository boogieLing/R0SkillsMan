#!/usr/bin/env python3
"""Write r0push scope-check output into a submit record markdown file."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_ROOT / "assets" / "submit_record_template.md"
CHECKER = SKILL_ROOT / "scripts" / "check_r0push_scope.py"
ANCHOR = "- 提交前 `check_r0push_scope.py` 结果："
START = "<!-- r0push-scope-check:start -->"
END = "<!-- r0push-scope-check:end -->"


def ensure_record_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, path)


def run_checker(repo_root: Path) -> tuple[int, str]:
    completed = subprocess.run(
        ["python3", str(CHECKER), "--repo-root", str(repo_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    body = completed.stdout.strip()
    if completed.stderr.strip():
        body = f"{body}\n\n[stderr]\n{completed.stderr.strip()}".strip()
    if not body:
        body = "<no output>"
    return completed.returncode, body


def render_block(exit_code: int, output: str) -> str:
    return (
        f"{ANCHOR}\n"
        f"{START}\n"
        "```text\n"
        f"exit_code={exit_code}\n"
        f"{output}\n"
        "```\n"
        f"{END}"
    )


def upsert_block(text: str, block: str) -> str:
    if START in text and END in text:
        marker_start = text.index(START)
        anchor_start = text.rfind(ANCHOR, 0, marker_start)
        if anchor_start != -1:
            start = anchor_start
        else:
            line_start = text.rfind("\n", 0, marker_start)
            start = 0 if line_start == -1 else line_start + 1
        end = text.index(END) + len(END)
        return text[:start].rstrip() + "\n" + block + text[end:]

    if ANCHOR in text:
        return text.replace(ANCHOR, block, 1)

    lines = text.rstrip("\n")
    if lines:
        return lines + "\n\n" + block + "\n"
    return block + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write check_r0push_scope output into a submit record.")
    parser.add_argument("--repo-root", default=".", help="Git repo root or any path inside it.")
    parser.add_argument("--record-file", required=True, help="Target markdown record file.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    record_file = Path(args.record_file).resolve()

    if not TEMPLATE.exists():
        print(f"[ERROR] template missing: {TEMPLATE}")
        return 1
    if not CHECKER.exists():
        print(f"[ERROR] checker missing: {CHECKER}")
        return 1

    ensure_record_file(record_file)
    exit_code, output = run_checker(repo_root)
    text = record_file.read_text(encoding="utf-8")
    record_file.write_text(upsert_block(text, render_block(exit_code, output)), encoding="utf-8")

    print(f"record_file={record_file}")
    print(f"checker_exit_code={exit_code}")
    print("[OK] scope check result written to submit record.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
