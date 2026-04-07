#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_SECTIONS = [
    "0. META RULES",
    "1. PROJECT CONFIG",
    "2. SYSTEM ARCHITECTURE",
    "3. EXECUTION MODEL",
    "4. GLOBAL STATE",
    "5. AGENT DEFINITIONS",
    "6. PHASE STRATEGY",
    "7. TASK DAG",
    "8. TASK TEMPLATE",
    "9. SKILL SYSTEM",
    "10. FAILURE HANDLING",
    "11. CONSTRAINT SYSTEM",
    "12. VALIDATION SYSTEM",
    "13. SUCCESS CRITERIA",
    "14. EXECUTION START",
]

ASSUMPTION_MARKERS = ("ASSUMPTION:", "TBD", "待确认")
PLACEHOLDER_RE = re.compile(r"<<[^>\n]+>>")
ALLOWED_PLACEHOLDERS = {
    "<<MULTI-AGENT CODING ORCHESTRATION TEMPLATE V3-FINAL>>",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a generated request DSL document."
    )
    parser.add_argument("path", help="Path to the generated markdown document.")
    parser.add_argument(
        "--max-placeholders",
        type=int,
        default=0,
        help="Maximum number of unresolved <<PLACEHOLDER>> entries allowed.",
    )
    return parser.parse_args()


def find_section_positions(text: str) -> tuple[list[str], list[tuple[str, int]]]:
    missing: list[str] = []
    positions: list[tuple[str, int]] = []
    for section in REQUIRED_SECTIONS:
        idx = text.find(section)
        if idx == -1:
            missing.append(section)
        else:
            positions.append((section, idx))
    return missing, positions


def validate_order(positions: list[tuple[str, int]]) -> list[str]:
    failures: list[str] = []
    offsets = [offset for _, offset in positions]
    if offsets != sorted(offsets):
        failures.append("章节顺序不符合 0 到 14 的模板顺序。")
    return failures


def main() -> int:
    args = parse_args()
    path = Path(args.path).resolve()
    if not path.exists():
        print("VALIDATION_STATUS=FAIL")
        print(f"FAIL: 文件不存在: {path}")
        return 1

    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    warnings: list[str] = []

    if "SYSTEM:" not in text:
        failures.append("缺少 `SYSTEM:` 起始标记。")
    if "END TEMPLATE" not in text:
        failures.append("缺少 `END TEMPLATE` 结束标记。")

    missing_sections, positions = find_section_positions(text)
    if missing_sections:
        failures.append("缺少章节: " + ", ".join(missing_sections))
    failures.extend(validate_order(positions))

    placeholders = [
        match for match in PLACEHOLDER_RE.findall(text) if match not in ALLOWED_PLACEHOLDERS
    ]
    if len(placeholders) > args.max_placeholders:
        failures.append(
            "存在未替换占位符: "
            + ", ".join(placeholders[:10])
            + (" ..." if len(placeholders) > 10 else "")
        )

    if not any(marker in text for marker in ASSUMPTION_MARKERS):
        warnings.append(
            "未发现 `ASSUMPTION:` / `TBD` / `待确认` 标记；若原始需求信息不完整，需确认没有隐性编造。"
        )

    status = "PASS" if not failures else "FAIL"
    print(f"VALIDATION_STATUS={status}")
    print(f"FILE={path}")
    print(f"FAILURE_COUNT={len(failures)}")
    print(f"WARNING_COUNT={len(warnings)}")

    for failure in failures:
        print(f"FAIL: {failure}")
    for warning in warnings:
        print(f"WARN: {warning}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
