#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_TEMPLATE_VERSION = "MULTI-AGENT CODING ORCHESTRATION TEMPLATE V3-FINAL"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "untitled"


def build_output_path(repo_root: Path, title: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = repo_root / "r0" / "request"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"request-{stamp}-{slugify(title)}.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save rendered prompt DSL content into ./r0/request/ under the unified r0/ local record tree."
    )
    parser.add_argument(
        "--title",
        default="untitled",
        help="Human-readable title used to build the output filename.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing the unified ./r0/ tree.",
    )
    parser.add_argument(
        "--source-request",
        default="",
        help="Original natural language request for traceability.",
    )
    parser.add_argument(
        "--template-version",
        default=DEFAULT_TEMPLATE_VERSION,
        help="Template version identifier written into the document metadata.",
    )
    return parser.parse_args()


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_frontmatter(
    *,
    title: str,
    created_at: str,
    source_request: str,
    template_version: str,
) -> str:
    lines = [
        "---",
        f"title: {yaml_quote(title)}",
        f"created_at: {yaml_quote(created_at)}",
        f"template_version: {yaml_quote(template_version)}",
    ]
    if source_request.strip():
        lines.append("source_request: |-")
        for line in source_request.splitlines():
            lines.append(f"  {line}")
    else:
        lines.append('source_request: ""')
    lines.append("---")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    content = sys.stdin.read()
    if not content.strip():
        print("error: stdin is empty", file=sys.stderr)
        return 1

    repo_root = Path(args.repo_root).resolve()
    output_path = build_output_path(repo_root, args.title)
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    frontmatter = build_frontmatter(
        title=args.title,
        created_at=created_at,
        source_request=args.source_request,
        template_version=args.template_version,
    )
    rendered = f"{frontmatter}\n\n{content.lstrip()}"
    output_path.write_text(rendered, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
