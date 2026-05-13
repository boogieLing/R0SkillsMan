#!/usr/bin/env python3
"""Validate shared contract requirements for local r0-* skills.

Checks per skill:
- shared contract reference exists
- local record path uses ./r0/<skill-key>/
- staged cleanup rule covers both r0/ and r0-*
- shared result contract / summary-card constraints are present
- auto-evolution section is mentioned

Checks at repo root:
- .gitignore contains r0/ and uses r0-*/ only for normal target projects
- .gitignore does not keep per-skill unignore exceptions
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


RESULT_CONTRACT_TOKENS = (
    "共享结果契约",
    "shared result contract",
    "shared summary-card/result contract",
    "summary-card/result contract",
)
CARD_TOKENS = ("首屏摘要卡片", "摘要卡片", "summary-card", "summary card")
AUTO_EVOLUTION_TOKENS = ("自动进化", "auto evolution")


@dataclass
class SkillIssue:
    skill_name: str
    path: Path
    issues: list[str]


def discover_skills(repo_root: Path) -> list[Path]:
    skills: list[Path] = []
    for path in sorted(repo_root.iterdir()):
        if not path.is_dir():
            continue
        if not path.name.startswith("r0-"):
            continue
        if (path / "SKILL.md").is_file():
            skills.append(path)
    return skills


def has_shared_contract_reference(text: str) -> bool:
    return "shared/r0-core-contract.md" in text or "../shared/r0-core-contract.md" in text


def has_restore_rules(text: str) -> tuple[bool, bool]:
    normalized = text.replace("`", "")
    has_r0_restore = (
        "git restore --staged r0/" in normalized
        or "git restore --staged -- r0/" in normalized
    )
    has_legacy_restore = "'r0-*'" in normalized or '"r0-*"' in normalized or " r0-*" in normalized
    return has_r0_restore, has_legacy_restore


def validate_skill(skill_dir: Path) -> SkillIssue | None:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    skill_key = skill_dir.name.removeprefix("r0-")
    expected_record = f"./r0/{skill_key}/"
    issues: list[str] = []

    if not has_shared_contract_reference(text):
        issues.append("缺少 shared/r0-core-contract.md 引用")
    if expected_record not in text:
        issues.append(f"缺少本地记录路径 {expected_record}")

    has_r0_restore, has_legacy_restore = has_restore_rules(text)
    if not has_r0_restore:
        issues.append("未声明 git restore --staged -- r0/ 规则")
    if not has_legacy_restore:
        issues.append("未覆盖历史目录 r0-* 的误暂存清理规则")
    if not any(token in text for token in RESULT_CONTRACT_TOKENS):
        issues.append("缺少共享结果契约提示")
    if not any(token in text for token in CARD_TOKENS):
        issues.append("缺少首屏摘要卡片约束")
    if not any(token in text for token in AUTO_EVOLUTION_TOKENS):
        issues.append("缺少自动进化约束")
    if re.search(r"(?<!\.)\./r0-[a-z0-9-]+/", text):
        issues.append("仍包含旧的 ./r0-xxx/ 本地记录路径")

    if not issues:
        return None
    return SkillIssue(skill_name=skill_dir.name, path=skill_dir, issues=issues)


def validate_gitignore(repo_root: Path) -> list[str]:
    path = repo_root / ".gitignore"
    issues: list[str] = []
    if not path.exists():
        return [f"缺少 {path.name}"]

    lines = path.read_text(encoding="utf-8").splitlines()
    normalized = {line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")}
    if "r0/" not in normalized:
        issues.append(".gitignore 缺少 r0/ 主规则")
    is_source_repo = any(
        path.is_dir() and (path / "SKILL.md").is_file()
        for path in repo_root.iterdir()
        if path.name.startswith("r0-")
    )
    if is_source_repo:
        if "r0-*/" in normalized:
            issues.append("source repo 不应在根 .gitignore 使用裸 r0-*/")
    elif "r0-*/" not in normalized:
        issues.append(".gitignore 缺少 r0-*/ 兼容规则")
    if any(line.strip().startswith("!/r0-") for line in lines):
        issues.append(".gitignore 仍包含按 skill 放行的例外规则")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check shared contract coverage for local r0-* skills.")
    parser.add_argument("--repo-root", default=".", help="Repository root or any path inside the repository.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if (repo_root / ".git").is_file() or (repo_root / ".git").is_dir():
        pass
    else:
        for candidate in [repo_root, *repo_root.parents]:
            if (candidate / ".git").exists():
                repo_root = candidate
                break

    skills = discover_skills(repo_root)
    print(f"repo_root={repo_root}")
    print(f"skill_count={len(skills)}")

    if not skills:
        print("[FAIL] 未找到任何 r0-* skill 文件。")
        return 1

    repo_issues = validate_gitignore(repo_root)
    issues = [result for skill_dir in skills if (result := validate_skill(skill_dir)) is not None]

    if not issues and not repo_issues:
        print("[OK] 所有 r0-* skills 均通过 shared contract / local record / summary-card 校验。")
        return 0

    failed_count = len(issues) + (1 if repo_issues else 0)
    print(f"failed_count={failed_count}")

    if repo_issues:
        print("\n[repo-root]")
        print(f"path={repo_root / '.gitignore'}")
        for issue in repo_issues:
            print(f"- {issue}")

    for item in issues:
        print(f"\n[{item.skill_name}]")
        print(f"path={item.path}")
        for issue in item.issues:
            print(f"- {issue}")

    print("[FAIL] 检测到 shared contract 覆盖缺口。")
    return 2


if __name__ == "__main__":
    sys.exit(main())
