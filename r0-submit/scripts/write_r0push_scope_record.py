#!/usr/bin/env python3
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
    completed = subprocess.run(["python3", str(CHECKER), "--repo-root", str(repo_root)], check=False, capture_output=True, text=True)
    body = completed.stdout.strip()
    if completed.stderr.strip():
        body = f"{body}\n\n[stderr]\n{completed.stderr.strip()}".strip()
    return completed.returncode, body or "<no output>"


def render(exit_code: int, body: str) -> str:
    return "\n".join([ANCHOR, START, "```text", f"exit_code={exit_code}", body, "```", END])


def upsert(text: str, block: str) -> str:
    if START in text and END in text:
        marker_start = text.index(START)
        anchor_start = text.rfind(ANCHOR, 0, marker_start)
        start = anchor_start if anchor_start != -1 else (text.rfind("\n", 0, marker_start) + 1)
        end = text.index(END) + len(END)
        return text[:start].rstrip() + "\n" + block + text[end:]
    if ANCHOR in text:
        return text.replace(ANCHOR, block, 1)
    return text.rstrip() + "\n\n" + block + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--record-file", required=True)
    args = parser.parse_args()

    record_file = Path(args.record_file).resolve()
    ensure_record_file(record_file)
    exit_code, body = run_checker(Path(args.repo_root).resolve())
    text = record_file.read_text(encoding="utf-8")
    record_file.write_text(upsert(text, render(exit_code, body)), encoding="utf-8")
    print(f"record_file={record_file}")
    print(f"checker_exit_code={exit_code}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
