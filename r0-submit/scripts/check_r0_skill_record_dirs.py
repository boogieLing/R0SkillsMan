#!/usr/bin/env python3
import re
import sys
from pathlib import Path

SKILLS_ROOT = Path('/Users/r0/.codex/skills')


def parse_name(text: str) -> str | None:
    m = re.search(r"^name:\s*(r0-[a-z0-9-]+)\s*$", text, flags=re.MULTILINE)
    return m.group(1) if m else None


def uniq(items: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def extract_refs(text: str) -> dict[str, list[str]]:
    local_dir_refs = uniq(re.findall(r"\./(r0-[a-z0-9-]+)(?:/|\b)", text))
    gitignore_refs = uniq(re.findall(r"\^(r0-[a-z0-9-]+)/\$", text))
    staged_refs = uniq(re.findall(r"git\s+restore\s+--staged\s+(r0-[a-z0-9-]+)/", text))
    return {
        'local': local_dir_refs,
        'gitignore': gitignore_refs,
        'staged': staged_refs,
    }


def main() -> int:
    skill_files = sorted(SKILLS_ROOT.glob('r0-*/SKILL.md'))
    if not skill_files:
        print('未找到 r0-* skill 文件')
        return 1

    issues: list[str] = []

    for skill_file in skill_files:
        text = skill_file.read_text(encoding='utf-8')
        name = parse_name(text)
        if not name:
            issues.append(f"{skill_file}: 缺少或无法解析 name")
            continue

        refs = extract_refs(text)
        has_hygiene_config = any(refs.values())

        for kind, items in refs.items():
            for item in items:
                if item != name:
                    issues.append(
                        f"{skill_file}: {kind} 引用为 {item}，但 skill name 是 {name}"
                    )

        if has_hygiene_config:
            if name not in refs['gitignore']:
                issues.append(f"{skill_file}: 检测到本地记录规则，但缺少 .gitignore 规则 ^{name}/$")
            if name not in refs['staged']:
                issues.append(f"{skill_file}: 检测到本地记录规则，但缺少 git restore --staged {name}/")
            if name not in refs['local']:
                issues.append(f"{skill_file}: 检测到本地记录规则，但未发现 ./{name} 路径引用")

    if issues:
        print('发现 r0 skill 本地记录规则不一致：')
        for issue in issues:
            print(f"- {issue}")
        return 2

    print('检查通过：所有含本地记录规则的 r0-* skill 目录名与 .gitignore/staged 规则一致。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
