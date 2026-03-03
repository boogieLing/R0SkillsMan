#!/usr/bin/env python3
"""Conservative auto-evolution for local r0-* skills.

Scope:
- Discover r0-* skills by folder name + SKILL.md.
- Auto-regenerate agents/openai.yaml when missing or stale.
- Validate each processed skill with quick_validate.py.

This script intentionally avoids high-risk content rewrites.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import yaml

GEN_OPENAI_YAML = Path(
    "/Users/r0/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py"
)
QUICK_VALIDATE = Path(
    "/Users/r0/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
)


@dataclass
class SkillResult:
    path: Path
    status: str
    reason: str


def expand_roots(roots: Iterable[str]) -> List[Path]:
    seen = set()
    out: List[Path] = []
    for root in roots:
        p = Path(root).expanduser().resolve()
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def discover_skills(roots: List[Path], prefix: str) -> List[Path]:
    found = set()
    for root in roots:
        if not root.exists():
            continue
        for skill_md in root.rglob("SKILL.md"):
            skill_dir = skill_md.parent.resolve()
            if skill_dir.name.startswith(prefix):
                found.add(skill_dir)
    return sorted(found)


def read_frontmatter(skill_md: Path) -> Dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md 缺少有效 frontmatter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("frontmatter 不是字典结构")
    return data


def generate_openai_yaml(skill_dir: Path, skill_name: str, dry_run: bool) -> Tuple[bool, str]:
    default_prompt = f"使用 ${skill_name} 执行当前任务，并按技能规范输出中文结构化结果。"
    cmd = [
        "python3",
        str(GEN_OPENAI_YAML),
        str(skill_dir),
        "--interface",
        f"default_prompt={default_prompt}",
    ]
    if dry_run:
        return True, "dry-run: 计划重建 agents/openai.yaml"

    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "未知错误"
        return False, f"重建 openai.yaml 失败: {stderr}"
    return True, "已重建 agents/openai.yaml"


def quick_validate(skill_dir: Path) -> Tuple[bool, str]:
    cmd = ["python3", str(QUICK_VALIDATE), str(skill_dir)]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    output = completed.stdout.strip() or completed.stderr.strip() or "无输出"
    return completed.returncode == 0, output


def process_skill(skill_dir: Path, dry_run: bool) -> SkillResult:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return SkillResult(skill_dir, "flagged", "缺少 SKILL.md")

    try:
        frontmatter = read_frontmatter(skill_md)
    except Exception as exc:
        return SkillResult(skill_dir, "flagged", f"frontmatter 解析失败: {exc}")

    fm_name = str(frontmatter.get("name", "")).strip()
    if not fm_name:
        return SkillResult(skill_dir, "flagged", "frontmatter 缺少 name")

    if fm_name != skill_dir.name:
        return SkillResult(
            skill_dir,
            "flagged",
            f"frontmatter.name 与目录名不一致: {fm_name} != {skill_dir.name}",
        )

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    need_regen = (not openai_yaml.exists()) or (
        skill_md.stat().st_mtime - openai_yaml.stat().st_mtime > 1.0
    )

    changed = False
    if need_regen:
        ok, msg = generate_openai_yaml(skill_dir, fm_name, dry_run=dry_run)
        if not ok:
            return SkillResult(skill_dir, "flagged", msg)
        changed = True

    valid, msg = quick_validate(skill_dir)
    if not valid:
        return SkillResult(skill_dir, "flagged", f"校验失败: {msg}")

    if changed:
        return SkillResult(skill_dir, "updated", "元数据已自动修复并通过校验")
    return SkillResult(skill_dir, "no_change", "No update required")


def main() -> int:
    parser = argparse.ArgumentParser(description="Conservative auto-evolution for r0-* skills.")
    parser.add_argument(
        "--roots",
        nargs="+",
        default=[
            "/Users/r0/.codex/skills",
            "/Users/r0/.agents/skills",
            "/Volumes/R0sORICO/r0_work/r0-skills",
        ],
        help="Skill roots to scan.",
    )
    parser.add_argument("--prefix", default="r0-", help="Skill folder prefix filter.")
    parser.add_argument("--dry-run", action="store_true", help="Plan only, do not modify files.")
    args = parser.parse_args()

    if not GEN_OPENAI_YAML.exists() or not QUICK_VALIDATE.exists():
        print("[ERROR] 依赖脚本缺失，无法执行自动进化。")
        return 1

    roots = expand_roots(args.roots)
    skills = discover_skills(roots, args.prefix)

    print("自动进化模式:", "dry-run" if args.dry_run else "apply")
    print("扫描根目录:", ", ".join(str(r) for r in roots))
    print("匹配技能数:", len(skills))

    updated: List[SkillResult] = []
    no_change: List[SkillResult] = []
    flagged: List[SkillResult] = []

    for skill_dir in skills:
        result = process_skill(skill_dir, dry_run=args.dry_run)
        if result.status == "updated":
            updated.append(result)
        elif result.status == "no_change":
            no_change.append(result)
        else:
            flagged.append(result)

    print("\nUpdated Skills:")
    if updated:
        for item in updated:
            print(f"- {item.path}: {item.reason}")
    else:
        print("- None")

    print("\nUnmodified Skills:")
    if no_change:
        for item in no_change:
            print(f"- {item.path}: {item.reason}")
    else:
        print("- None")

    print("\nFlagged Skills:")
    if flagged:
        for item in flagged:
            print(f"- {item.path}: {item.reason}")
    else:
        print("- None")

    print("\nSummary:")
    print(
        f"updated={len(updated)}, no_change={len(no_change)}, flagged={len(flagged)}"
    )
    return 0 if not flagged else 2


if __name__ == "__main__":
    raise SystemExit(main())
