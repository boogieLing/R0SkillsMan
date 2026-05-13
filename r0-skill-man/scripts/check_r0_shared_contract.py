#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from shared_contract_checks import detect_repo_root, discover_skills, validate_repo_contract, validate_skill_contract


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="校验 r0-* skills 的 shared contract、token-efficient prompting、本地记录路径、摘要卡片与 repo hygiene 约束。"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=detect_repo_root(),
        help="技能仓库根目录；默认自动探测包含 shared/r0-core-contract.md 的目录。",
    )
    parser.add_argument(
        "--prefix",
        default="r0-",
        help="技能目录前缀，默认 r0-。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    repo_issues = validate_repo_contract(repo_root, prefix=args.prefix)
    skill_dirs = discover_skills(repo_root, prefix=args.prefix)

    if not skill_dirs:
        print(f"[FAIL] 未找到 {args.prefix}* / SKILL.md: repo_root={repo_root}")
        return 1

    print(f"repo_root={repo_root}")
    print(f"skill_count={len(skill_dirs)}")

    if repo_issues:
        print("\n[repo]")
        for issue in repo_issues:
            print(f"- {issue}")
    else:
        print("\n[repo]")
        print("- OK")

    skill_failures = 0
    print("\n[skills]")
    for skill_dir in skill_dirs:
        issues = validate_skill_contract(skill_dir)
        if issues:
            skill_failures += 1
            print(f"- {skill_dir.name}: FAIL")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"- {skill_dir.name}: OK")

    print("\n[summary]")
    print(f"repo_issues={len(repo_issues)}")
    print(f"skill_failures={skill_failures}")
    print(f"skills_checked={len(skill_dirs)}")

    if repo_issues or skill_failures:
        return 2

    print("检查通过：shared contract、token-efficient prompting、本地记录路径、摘要卡片与 repo hygiene 约束一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
