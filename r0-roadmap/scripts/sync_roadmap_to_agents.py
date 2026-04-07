#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

START_MARKER = "<!-- r0-roadmap:start -->"
END_MARKER = "<!-- r0-roadmap:end -->"


def find_agents(start_dir: Path) -> Path | None:
    current = start_dir.resolve()
    while True:
        candidate = current / "AGENTS.md"
        if candidate.exists():
            return candidate
        if current.parent == current:
            return None
        current = current.parent


def extract_title_and_summary(roadmap_text: str, roadmap_path: Path, project_root: Path) -> str:
    lines = [line.rstrip() for line in roadmap_text.splitlines()]
    heading = next((line for line in lines if line.startswith("#")), "# Roadmap")

    summary_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        summary_lines.append(stripped)
        if len(summary_lines) >= 6:
            break

    try:
        rel_roadmap = roadmap_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        rel_roadmap = roadmap_path.resolve()
    body = "\n".join(f"- {line}" for line in summary_lines) if summary_lines else "- 详见 roadmap 文档。"
    return (
        f"{START_MARKER}\n"
        f"## R0 Roadmap\n\n"
        f"- Source: `{rel_roadmap}`\n"
        f"- Title: `{heading.lstrip('#').strip()}`\n"
        f"- Managed by: `r0-roadmap`\n\n"
        f"{body}\n"
        f"{END_MARKER}\n"
    )


def upsert_agents(agents_path: Path, managed_block: str) -> None:
    text = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    if START_MARKER in text and END_MARKER in text:
        start = text.index(START_MARKER)
        end = text.index(END_MARKER) + len(END_MARKER)
        new_text = text[:start] + managed_block.rstrip() + text[end:]
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        if text and not text.endswith("\n\n"):
            text += "\n"
        new_text = text + managed_block
    agents_path.write_text(new_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync roadmap summary into the nearest global AGENTS.md.")
    parser.add_argument("--target-dir", required=True, help="Target project directory.")
    parser.add_argument("--roadmap-file", required=True, help="Generated roadmap markdown file.")
    args = parser.parse_args()

    target_dir = Path(args.target_dir).expanduser().resolve()
    roadmap_file = Path(args.roadmap_file).expanduser().resolve()

    if not target_dir.is_dir():
        raise SystemExit(f"[ERROR] target-dir 不存在或不是目录: {target_dir}")
    if not roadmap_file.is_file():
        raise SystemExit(f"[ERROR] roadmap-file 不存在: {roadmap_file}")

    agents_path = find_agents(target_dir)
    if agents_path is None:
        print("[INFO] 未发现全局 AGENTS.md")
        return 0

    managed_block = extract_title_and_summary(
        roadmap_file.read_text(encoding="utf-8"),
        roadmap_file,
        agents_path.parent,
    )
    upsert_agents(agents_path, managed_block)
    print(f"[OK] 已更新 AGENTS.md: {agents_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
