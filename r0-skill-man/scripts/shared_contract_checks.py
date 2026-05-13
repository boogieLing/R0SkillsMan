#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from typing import List

SHARED_RESULT_TOKENS = (
    "共享结果契约",
    "shared result contract",
    "shared summary-card/result contract",
    "summary-card/result contract",
)
CARD_TOKENS = ("首屏摘要卡片", "摘要卡片", "summary-card", "summary card")
LOCAL_RECORD_RE = re.compile(r"\./r0/([a-z0-9-]+)(?:/|\b)")
LEGACY_LOCAL_RECORD_RE = re.compile(r"(?<!\.)\./r0-[a-z0-9-]+/")
LEGACY_GITIGNORE_RE = re.compile(r"\^r0-[a-z0-9-]+/\$")
SKILL_NAME_RE = re.compile(r"^name:\s*(r0-[a-z0-9-]+)\s*$", re.MULTILINE)


def detect_repo_root(start: Path | None = None) -> Path:
    probe = (start or Path(__file__)).resolve()
    if probe.is_file():
        probe = probe.parent
    for parent in (probe, *probe.parents):
        if (parent / "shared" / "r0-core-contract.md").exists():
            return parent
    raise FileNotFoundError("未找到 shared/r0-core-contract.md，无法探测 repo root")


def discover_skills(repo_root: Path, prefix: str = "r0-") -> List[Path]:
    return sorted(
        skill_md.parent.resolve()
        for skill_md in repo_root.glob(f"{prefix}*/SKILL.md")
        if skill_md.parent.name.startswith(prefix)
    )


def parse_skill_name(text: str) -> str | None:
    match = SKILL_NAME_RE.search(text)
    return match.group(1) if match else None


def expected_record_key(skill_name: str) -> str:
    return skill_name.removeprefix("r0-")


def has_shared_contract_ref(text: str) -> bool:
    return "../shared/r0-core-contract.md" in text or "shared/r0-core-contract.md" in text


def has_result_card_contract(text: str) -> bool:
    return any(token in text for token in SHARED_RESULT_TOKENS) and any(
        token in text for token in CARD_TOKENS
    )


def extract_local_record_keys(text: str) -> List[str]:
    seen = set()
    items: List[str] = []
    for key in LOCAL_RECORD_RE.findall(text):
        if key in seen:
            continue
        seen.add(key)
        items.append(key)
    return items


def has_restore_rules(text: str) -> tuple[bool, bool]:
    normalized = text.replace("`", "")
    has_r0_restore = (
        "git restore --staged r0/" in normalized
        or "git restore --staged -- r0/" in normalized
    )
    has_legacy_restore = "'r0-*'" in normalized or '"r0-*"' in normalized or " r0-*" in normalized
    return has_r0_restore, has_legacy_restore


def validate_repo_contract(repo_root: Path, prefix: str = "r0-") -> List[str]:
    issues: List[str] = []
    contract_file = repo_root / "shared" / "r0-core-contract.md"
    if not contract_file.exists():
        issues.append("缺少 shared/r0-core-contract.md")

    gitignore = repo_root / ".gitignore"
    if not gitignore.exists():
        issues.append("缺少 .gitignore")
        return issues

    lines = {line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()}
    if "r0/" not in lines:
        issues.append(".gitignore 缺少主规则 r0/")
    is_source_repo = any(repo_root.glob(f"{prefix}*/SKILL.md"))
    if is_source_repo:
        if "r0-*/" in lines:
            issues.append("source repo 不应在根 .gitignore 使用裸 r0-*/；这会忽略新加入的 skill 源码文件")
    elif "r0-*/" not in lines:
        issues.append(".gitignore 缺少兼容规则 r0-*/")
    return issues


def validate_skill_contract(skill_dir: Path) -> List[str]:
    issues: List[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["缺少 SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    skill_name = parse_skill_name(text)
    if not skill_name:
        return ["缺少或无法解析 frontmatter.name"]
    if skill_name != skill_dir.name:
        issues.append(f"frontmatter.name 与目录名不一致: {skill_name} != {skill_dir.name}")

    expected_key = expected_record_key(skill_name)
    local_record_keys = extract_local_record_keys(text)

    if not has_shared_contract_ref(text):
        issues.append("缺少 shared/r0-core-contract.md 引用")
    if not has_result_card_contract(text):
        issues.append("缺少共享结果契约 + 摘要卡片约束提示")
    if LEGACY_LOCAL_RECORD_RE.search(text):
        issues.append("仍包含旧的 ./r0-xxx/ 本地记录路径")
    if LEGACY_GITIGNORE_RE.search(text):
        issues.append("仍包含旧的按 skill 分散维护的 .gitignore 规则")
    if expected_key not in local_record_keys:
        issues.append(f"未声明本技能本地记录目录 ./r0/{expected_key}/")
    for key in local_record_keys:
        if key != expected_key:
            issues.append(f"引用了其他本地记录目录 ./r0/{key}/")

    has_r0_restore, has_legacy_restore = has_restore_rules(text)
    if not has_r0_restore:
        issues.append("未声明统一的 git restore --staged r0/ 规则")
    if not has_legacy_restore:
        issues.append("未覆盖历史目录 r0-* 的误暂存清理规则")

    return issues
