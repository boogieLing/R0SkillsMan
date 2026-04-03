#!/usr/bin/env python3
"""Prepare a local r0-submit record with git baseline and scope-audit output."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_ROOT / "assets" / "submit_record_template.md"
MIGRATOR = SKILL_ROOT / "scripts" / "migrate_r0_record_dirs.py"
SCOPE_WRITER = SKILL_ROOT / "scripts" / "write_r0push_scope_record.py"
ALLOWED_RECORD_KEYS = {
    "- 项目路径：": "",
    "- 工作开始时间：": "",
    "- 记录文件路径：": "",
    "- dry-run manifest 路径：": "",
    "- `.gitignore` 是否包含 `r0/`：": "",
    "- `.gitignore` 是否包含 `r0-*/`：": "",
    "- 提交前 `git status --short --branch` 摘要：": "",
}
START = "<!-- git-baseline:start -->"
END = "<!-- git-baseline:end -->"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)


def git(repo_root: Path, *args: str) -> str:
    completed = run(["git", *args], repo_root)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise RuntimeError(f"{' '.join(args)}: {stderr}")
    return completed.stdout.strip()


def rel_to_repo(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def ensure_record_file(record_file: Path) -> None:
    if record_file.exists():
        return
    record_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, record_file)


def replace_line(text: str, prefix: str, value: str) -> str:
    lines = text.splitlines()
    replaced = False
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{prefix} {value}".rstrip()
            replaced = True
            break
    if not replaced:
        lines.append(f"{prefix} {value}".rstrip())
    return "\n".join(lines) + "\n"


def render_git_baseline(repo_root: Path) -> str:
    status = git(repo_root, "status", "--short", "--branch")
    diff = git(repo_root, "diff", "--name-only")
    cached = git(repo_root, "diff", "--cached", "--name-only")
    stat = git(repo_root, "diff", "--stat")
    cached_stat = git(repo_root, "diff", "--cached", "--stat")
    parts = [
        "## Git Baseline Snapshot",
        START,
        "```text",
        "[git status --short --branch]",
        status or "<empty>",
        "",
        "[git diff --name-only]",
        diff or "<empty>",
        "",
        "[git diff --cached --name-only]",
        cached or "<empty>",
        "",
        "[git diff --stat]",
        stat or "<empty>",
        "",
        "[git diff --cached --stat]",
        cached_stat or "<empty>",
        "```",
        END,
    ]
    return "\n".join(parts)


def upsert_git_baseline(text: str, block: str) -> str:
    if START in text and END in text:
        start = text.index(START)
        line_start = text.rfind("\n", 0, start)
        start = 0 if line_start == -1 else line_start + 1
        end = text.index(END) + len(END)
        return text[:start].rstrip() + "\n" + block + text[end:]
    return text.rstrip() + "\n\n" + block + "\n"


def ensure_gitignore(repo_root: Path) -> tuple[bool, bool]:
    path = repo_root / ".gitignore"
    if not path.exists():
        path.write_text("", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    changed = False
    for rule in ("r0/", "r0-*/"):
        if rule not in lines:
            lines.append(rule)
            changed = True
    if changed:
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    final = path.read_text(encoding="utf-8").splitlines()
    return ("r0/" in final, "r0-*/" in final)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare r0-submit local record and baseline.")
    parser.add_argument("--repo-root", default=".", help="Git repo root or any path inside it.")
    parser.add_argument("--record-file", help="Target record file. Defaults to ./r0/submit/提交记录_YYYYMMDD_HHMMSS.md")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    try:
        repo_root = Path(git(repo_root, "rev-parse", "--show-toplevel"))
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    if not TEMPLATE.exists() or not MIGRATOR.exists() or not SCOPE_WRITER.exists():
        print("[ERROR] required helper scripts or template missing.")
        return 1

    run(["python3", str(MIGRATOR), "--repo-root", str(repo_root)], repo_root)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    record_file = Path(args.record_file).resolve() if args.record_file else repo_root / "r0" / "submit" / f"提交记录_{ts}.md"
    ensure_record_file(record_file)

    run(["python3", str(SCOPE_WRITER), "--repo-root", str(repo_root), "--record-file", str(record_file)], repo_root)

    r0_ok, legacy_ok = ensure_gitignore(repo_root)

    text = record_file.read_text(encoding="utf-8")
    text = replace_line(text, "- 项目路径：", str(repo_root))
    text = replace_line(text, "- 工作开始时间：", datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z").strip())
    text = replace_line(text, "- 记录文件路径：", rel_to_repo(record_file, repo_root))
    text = replace_line(text, "- dry-run manifest 路径：", "")
    text = replace_line(text, "- `.gitignore` 是否包含 `r0/`：", "yes" if r0_ok else "no")
    text = replace_line(text, "- `.gitignore` 是否包含 `r0-*/`：", "yes" if legacy_ok else "no")
    text = replace_line(text, "- 提交前 `git status --short --branch` 摘要：", "见下方 `Git Baseline Snapshot`")
    text = upsert_git_baseline(text, render_git_baseline(repo_root))
    record_file.write_text(text, encoding="utf-8")

    print(f"repo_root={repo_root}")
    print(f"record_file={record_file}")
    print("[OK] submit record prepared with git baseline and scope check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
