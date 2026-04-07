#!/usr/bin/env python3
"""Migrate legacy r0-* local record directories into the unified r0/<skill-key>/ layout."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Stats:
    moved: int = 0
    deduped: int = 0
    conflicts: int = 0
    skipped: int = 0


def skill_key_from_legacy(name: str) -> str | None:
    if not name.startswith("r0-"):
        return None
    suffix = name[3:]
    return suffix or None


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def same_file(src: Path, dst: Path) -> bool:
    if src.is_file() and dst.is_file():
        return filecmp.cmp(src, dst, shallow=False)
    return False


def migrate_file(src: Path, dst: Path, stats: Stats, conflicts: list[str]) -> None:
    ensure_parent(dst)

    if not dst.exists():
        shutil.move(str(src), str(dst))
        stats.moved += 1
        return

    if same_file(src, dst):
        src.unlink()
        stats.deduped += 1
        return

    stats.conflicts += 1
    conflicts.append(f"{src} -> {dst}")


def prune_empty_dirs(path: Path, stop: Path) -> None:
    current = path
    while current != stop and current.exists():
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def migrate_legacy_dir(repo_root: Path, legacy_dir: Path, stats: Stats, conflicts: list[str]) -> None:
    key = skill_key_from_legacy(legacy_dir.name)
    if not key:
        stats.skipped += 1
        return
    if (legacy_dir / "SKILL.md").exists():
        stats.skipped += 1
        return

    target_root = repo_root / "r0" / key
    target_root.mkdir(parents=True, exist_ok=True)

    for src in sorted(legacy_dir.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(legacy_dir)
        migrate_file(src, target_root / rel, stats, conflicts)

    for child in sorted(legacy_dir.rglob("*"), reverse=True):
        if child.is_dir():
            prune_empty_dirs(child, legacy_dir)
    prune_empty_dirs(legacy_dir, repo_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy r0-* record dirs into r0/<skill-key>/.")
    parser.add_argument("--repo-root", default=".", help="Repository root or any path inside the repository.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    stats = Stats()
    conflicts: list[str] = []

    legacy_dirs = [
        path
        for path in sorted(repo_root.iterdir())
        if path.is_dir() and path.name.startswith("r0-") and path.name != "r0-skills"
    ]

    for legacy_dir in legacy_dirs:
        migrate_legacy_dir(repo_root, legacy_dir, stats, conflicts)

    print(f"repo_root={repo_root}")
    print(f"legacy_dir_count={len(legacy_dirs)}")
    print(f"moved={stats.moved}")
    print(f"deduped={stats.deduped}")
    print(f"conflicts={stats.conflicts}")
    print(f"skipped={stats.skipped}")

    if conflicts:
        print("conflict_paths:")
        for item in conflicts:
            print(f"- {item}")
        print("[WARN] legacy r0-* migration finished with conflicts; no conflicting file was overwritten.")
        return 2

    print("[OK] legacy r0-* migration finished without conflicts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
