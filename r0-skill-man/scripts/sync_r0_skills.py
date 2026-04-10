#!/usr/bin/env python3
"""Bidirectional sync for local r0-* skills and shared support directories across configured roots.

Policy:
- Discover skills by directory name prefix + SKILL.md presence.
- For each skill, pick the newest copy (latest file mtime in tree) as source of truth.
- Sync source -> all other roots.
- Optional prune removes files only when --prune is set.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

IGNORE_NAMES = {".DS_Store", "Thumbs.db"}
AUXILIARY_DIRS = ("shared",)


@dataclass
class SyncStats:
    created_files: int = 0
    updated_files: int = 0
    created_dirs: int = 0
    deleted_files: int = 0
    deleted_dirs: int = 0

    def merge(self, other: "SyncStats") -> None:
        self.created_files += other.created_files
        self.updated_files += other.updated_files
        self.created_dirs += other.created_dirs
        self.deleted_files += other.deleted_files
        self.deleted_dirs += other.deleted_dirs


def expand_roots(roots: Iterable[str]) -> List[Path]:
    seen: Set[Path] = set()
    out: List[Path] = []
    for root in roots:
        p = Path(root).expanduser().resolve()
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def is_skill_dir(path: Path) -> bool:
    return (path / "SKILL.md").is_file()


def discover_skills(roots: List[Path], prefix: str) -> Dict[str, List[Path]]:
    skills: Dict[str, List[Path]] = {}
    for root in roots:
        if not root.exists():
            continue
        for skill_md in root.rglob("SKILL.md"):
            skill_dir = skill_md.parent.resolve()
            skill_name = skill_dir.name
            if not skill_name.startswith(prefix):
                continue
            skills.setdefault(skill_name, []).append(skill_dir)
    # Deduplicate same real paths per skill.
    for name, paths in list(skills.items()):
        uniq = sorted({p for p in paths})
        skills[name] = uniq
    return skills


def latest_tree_mtime(path: Path) -> float:
    latest = path.stat().st_mtime
    for item in path.rglob("*"):
        if item.name in IGNORE_NAMES:
            continue
        try:
            latest = max(latest, item.stat().st_mtime)
        except FileNotFoundError:
            continue
    return latest


def should_copy(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return True
    if not dst.is_file():
        return True
    src_stat = src.stat()
    dst_stat = dst.stat()
    if src_stat.st_size != dst_stat.st_size:
        return True
    # Worktrees frequently refresh mtimes without changing content.
    return not filecmp.cmp(src, dst, shallow=False)


def sync_one_skill(source: Path, target: Path, dry_run: bool, prune: bool) -> SyncStats:
    stats = SyncStats()

    if not target.exists():
        stats.created_dirs += 1
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)

    source_items: Set[Path] = set()

    for src_path in source.rglob("*"):
        if src_path.name in IGNORE_NAMES:
            continue
        rel = src_path.relative_to(source)
        source_items.add(rel)
        dst_path = target / rel

        if src_path.is_dir():
            if not dst_path.exists():
                stats.created_dirs += 1
                if not dry_run:
                    dst_path.mkdir(parents=True, exist_ok=True)
            continue

        if src_path.is_file() and should_copy(src_path, dst_path):
            if dst_path.exists():
                stats.updated_files += 1
            else:
                stats.created_files += 1
            if not dry_run:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)

    if prune and target.exists():
        # Remove files/dirs not present in source.
        target_items = sorted(
            (p.relative_to(target) for p in target.rglob("*") if p.name not in IGNORE_NAMES),
            key=lambda p: len(p.parts),
            reverse=True,
        )
        for rel in target_items:
            if rel in source_items:
                continue
            dst_path = target / rel
            if dst_path.is_file() or dst_path.is_symlink():
                stats.deleted_files += 1
                if not dry_run:
                    dst_path.unlink(missing_ok=True)
            elif dst_path.is_dir():
                stats.deleted_dirs += 1
                if not dry_run:
                    shutil.rmtree(dst_path, ignore_errors=True)

    return stats


def format_stats(stats: SyncStats) -> str:
    return (
        f"created_dirs={stats.created_dirs}, created_files={stats.created_files}, "
        f"updated_files={stats.updated_files}, deleted_files={stats.deleted_files}, "
        f"deleted_dirs={stats.deleted_dirs}"
    )


def sync_auxiliary_dir(dir_name: str, roots: List[Path], dry_run: bool, prune: bool) -> SyncStats:
    existing = [root / dir_name for root in roots if (root / dir_name).exists()]
    stats = SyncStats()
    if not existing:
        return stats

    source = max(existing, key=latest_tree_mtime)
    print(f"\n[{dir_name}] source={source}")
    seen_targets: Set[Path] = set()
    for root in roots:
        target = (root / dir_name).resolve()
        if target == source or target in seen_targets:
            continue
        seen_targets.add(target)
        delta = sync_one_skill(source, target, dry_run=dry_run, prune=prune)
        stats.merge(delta)
        if any(
            [
                delta.created_dirs,
                delta.created_files,
                delta.updated_files,
                delta.deleted_files,
                delta.deleted_dirs,
            ]
        ):
            print(f"  -> {target}: {format_stats(delta)}")
    if not any(
        [stats.created_dirs, stats.created_files, stats.updated_files, stats.deleted_files, stats.deleted_dirs]
    ):
        print("  -> no changes")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync local r0-* skills across roots.")
    parser.add_argument(
        "--roots",
        nargs="+",
        default=[
            "/Users/r0/.codex/skills",
            "/Volumes/R0sORICO/r0_work/r0-skills",
        ],
        help="Root directories that contain skills.",
    )
    parser.add_argument(
        "--prefix",
        default="r0-",
        help="Skill directory prefix to include (default: r0-).",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete target-side files that do not exist in the selected source copy.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan changes without writing files.",
    )
    args = parser.parse_args()

    roots = expand_roots(args.roots)
    for root in roots:
        if not args.dry_run:
            root.mkdir(parents=True, exist_ok=True)

    skills = discover_skills(roots, args.prefix)
    if not skills:
        print("No matching skills found.")
        return 0

    overall = SyncStats()
    print(f"Mode: {'dry-run' if args.dry_run else 'apply'}")
    print(f"Roots: {', '.join(str(r) for r in roots)}")
    print(f"Skills matched: {len(skills)}")

    for skill_name in sorted(skills):
        copies = skills[skill_name]
        source = max(copies, key=latest_tree_mtime)
        print(f"\n[{skill_name}] source={source}")

        per_skill = SyncStats()
        seen_targets: Set[Path] = set()
        for root in roots:
            target = (root / skill_name).resolve()
            if target == source or target in seen_targets:
                continue
            seen_targets.add(target)
            stats = sync_one_skill(source, target, dry_run=args.dry_run, prune=args.prune)
            per_skill.merge(stats)
            if any(
                [
                    stats.created_dirs,
                    stats.created_files,
                    stats.updated_files,
                    stats.deleted_files,
                    stats.deleted_dirs,
                ]
            ):
                print(f"  -> {target}: {format_stats(stats)}")

        if not any(
            [
                per_skill.created_dirs,
                per_skill.created_files,
                per_skill.updated_files,
                per_skill.deleted_files,
                per_skill.deleted_dirs,
            ]
        ):
            print("  -> no changes")

        overall.merge(per_skill)

    for aux_dir in AUXILIARY_DIRS:
        overall.merge(sync_auxiliary_dir(aux_dir, roots, dry_run=args.dry_run, prune=args.prune))

    print("\nSummary:")
    print(format_stats(overall))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
