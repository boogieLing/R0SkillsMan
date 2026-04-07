#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

IMG_REF_RE = re.compile(r'!\[[^\]]*\]\((assets/diagrams/diagram-[^)]+)\)')


@dataclass
class Issue:
    code: str
    severity: str
    ref: str
    message: str

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "ref": self.ref,
            "message": self.message,
        }


def run(cmd: List[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)


def parse_sips_size(path: Path) -> Optional[Tuple[int, int]]:
    proc = run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)])
    if proc.returncode != 0:
        return None
    m_w = re.search(r"pixelWidth:\s*(\d+)", proc.stdout)
    m_h = re.search(r"pixelHeight:\s*(\d+)", proc.stdout)
    if not m_w or not m_h:
        return None
    return int(m_w.group(1)), int(m_h.group(1))


def write_svg_wrapper(svg_path: Path, png_name: str, width: int, height: int) -> None:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{svg_path.stem}">\n'
        '  <rect width="100%" height="100%" fill="#ffffff" />\n'
        f'  <image href="{png_name}" x="0" y="0" width="{width}" height="{height}" '
        'preserveAspectRatio="xMidYMid meet" />\n'
        '</svg>\n'
    )
    svg_path.write_text(svg, encoding="utf-8")


def load_profiles(skill_root: Path) -> Dict[str, Dict[str, int]]:
    fp = skill_root / "references" / "diagram_profiles.json"
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, Dict[str, int]] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            w = int(v.get("width", 1600))
            h = int(v.get("height", 1200))
            out[str(k)] = {"width": w, "height": h}
    return out


def discover_md_files(article_dir: Path) -> List[Path]:
    return sorted(p for p in article_dir.glob("*.md") if p.is_file())


def collect_refs(md_files: List[Path]) -> Tuple[Set[str], Dict[str, List[Tuple[Path, int]]]]:
    refs: Set[str] = set()
    where: Dict[str, List[Tuple[Path, int]]] = {}
    for md in md_files:
        lines = md.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            for m in IMG_REF_RE.finditer(line):
                ref = m.group(1)
                refs.add(ref)
                where.setdefault(ref, []).append((md, i))
    return refs, where


def check_ref(
    article_dir: Path,
    ref: str,
    min_width: int,
    min_height: int,
) -> List[Issue]:
    issues: List[Issue] = []
    path = article_dir / ref
    if not path.exists():
        issues.append(Issue("missing_file", "error", ref, f"缺少文件: {ref}"))
        return issues

    if path.suffix.lower() == ".png":
        size = parse_sips_size(path)
        if not size:
            issues.append(Issue("bad_png", "error", ref, f"无法读取 PNG 尺寸: {ref}"))
            return issues
        w, h = size
        if (w == 45 and h == 13) or (w <= 60 and h <= 20):
            issues.append(Issue("placeholder_png", "error", ref, f"疑似占位图尺寸: {w}x{h}"))
        elif w < min_width or h < min_height:
            issues.append(Issue("tiny_png", "error", ref, f"尺寸过小: {w}x{h} (< {min_width}x{min_height})"))

    if path.suffix.lower() == ".svg":
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "<foreignObject" in text or "<foreignobject" in text:
            issues.append(Issue("foreignobject_svg", "error", ref, "SVG 含 foreignObject，存在黑块渲染风险"))
    return issues


def regenerate_from_mmd(
    *,
    stem: str,
    diagram_dir: Path,
    profiles: Dict[str, Dict[str, int]],
    edge_path: str,
    actions: List[str],
) -> Optional[str]:
    mmd = diagram_dir / f"{stem}.mmd"
    if not mmd.exists():
        return f"缺少 mmd 源文件: {mmd.name}"

    png = diagram_dir / f"{stem}.png"
    svg = diagram_dir / f"{stem}.svg"

    profile = profiles.get(stem, {"width": 1600, "height": 1200})
    width = int(profile.get("width", 1600))
    height = int(profile.get("height", 1200))

    pptr = diagram_dir / ".diagram_guard_pptr.json"
    pptr.write_text(
        json.dumps(
            {
                "executablePath": edge_path,
                "args": ["--no-sandbox", "--disable-setuid-sandbox"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    cmd = [
        "npx",
        "--yes",
        "@mermaid-js/mermaid-cli@11.9.0",
        "-i",
        str(mmd),
        "-o",
        str(png),
        "-p",
        str(pptr),
        "-w",
        str(width),
        "-H",
        str(height),
        "-s",
        "2",
        "-b",
        "white",
        "-q",
    ]
    proc = run(cmd)
    if proc.returncode != 0:
        return f"mmdc 失败({stem}): {proc.stderr.strip() or proc.stdout.strip()}"

    size = parse_sips_size(png)
    if not size:
        return f"mmdc 输出异常，无法读取 PNG 尺寸: {png.name}"

    w, h = size
    write_svg_wrapper(svg, png.name, w, h)
    actions.append(f"regenerate:{stem} -> {w}x{h}")
    return None


def wrap_svg_if_needed(ref: str, article_dir: Path, actions: List[str]) -> Optional[str]:
    svg_path = article_dir / ref
    if not svg_path.exists() or svg_path.suffix.lower() != ".svg":
        return None
    text = svg_path.read_text(encoding="utf-8", errors="ignore")
    if "<foreignObject" not in text and "<foreignobject" not in text:
        return None

    png_path = svg_path.with_suffix(".png")
    if not png_path.exists():
        return f"{ref} 含 foreignObject，且缺少同名 PNG 无法包装"

    size = parse_sips_size(png_path)
    if not size:
        return f"无法读取同名 PNG 尺寸: {png_path.name}"

    w, h = size
    write_svg_wrapper(svg_path, png_path.name, w, h)
    actions.append(f"wrap-svg:{svg_path.name} -> png-wrapper")
    return None


def drop_broken_refs(md_files: List[Path], refs_to_drop: Set[str], actions: List[str]) -> None:
    if not refs_to_drop:
        return
    for md in md_files:
        lines = md.read_text(encoding="utf-8").splitlines()
        out_lines: List[str] = []
        removed = 0
        for line in lines:
            hit = False
            for ref in refs_to_drop:
                if f"]({ref})" in line and "![" in line:
                    hit = True
                    removed += 1
                    break
            if not hit:
                out_lines.append(line)
        if removed:
            md.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
            actions.append(f"drop-ref:{md.name} removed={removed}")


def evaluate(article_dir: Path, refs: Set[str], min_width: int, min_height: int) -> List[Issue]:
    issues: List[Issue] = []
    for ref in sorted(refs):
        issues.extend(check_ref(article_dir, ref, min_width, min_height))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagram gate + auto-fix for article assets/diagrams")
    parser.add_argument("--article-dir", required=True, help="Article directory path")
    parser.add_argument("--mode", choices=["check", "fix", "gate-fix"], default="gate-fix")
    parser.add_argument("--min-width", type=int, default=120)
    parser.add_argument("--min-height", type=int, default=40)
    parser.add_argument("--drop-unfixable-refs", action="store_true", help="Auto-remove broken diagram refs from markdown when cannot fix")
    parser.add_argument("--report", default="", help="Report json path (default: <article>/assets/diagrams/diagram_guard_report.json)")
    parser.add_argument(
        "--edge-path",
        default="/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        help="Edge/Chromium executable for mermaid rendering",
    )
    args = parser.parse_args()

    article_dir = Path(args.article_dir).resolve()
    if not article_dir.is_dir():
        print(f"[diagram-guard][ERROR] 文章目录不存在: {article_dir}", file=sys.stderr)
        return 2

    diagram_dir = article_dir / "assets" / "diagrams"
    diagram_dir.mkdir(parents=True, exist_ok=True)

    md_files = discover_md_files(article_dir)
    refs, _ = collect_refs(md_files)

    before = evaluate(article_dir, refs, args.min_width, args.min_height)
    actions: List[str] = []

    if args.mode in {"fix", "gate-fix"}:
        skill_root = Path(__file__).resolve().parents[1]
        profiles = load_profiles(skill_root)

        # 1) Wrap risky SVG first
        for ref in sorted(refs):
            err = wrap_svg_if_needed(ref, article_dir, actions)
            if err:
                actions.append(f"warn:{err}")

        # 2) Regenerate broken PNG from .mmd when possible
        for issue in before:
            if issue.code not in {"placeholder_png", "tiny_png", "missing_file", "foreignobject_svg"}:
                continue
            ref_path = issue.ref
            stem = Path(ref_path).stem
            # only handle diagram-* references under assets/diagrams
            if not stem.startswith("diagram-"):
                continue
            err = regenerate_from_mmd(
                stem=stem,
                diagram_dir=diagram_dir,
                profiles=profiles,
                edge_path=args.edge_path,
                actions=actions,
            )
            if err:
                actions.append(f"warn:{err}")

        # 3) Drop unresolved refs if explicitly enabled
        if args.drop_unfixable_refs:
            refs_after_fix, _ = collect_refs(md_files)
            unresolved = evaluate(article_dir, refs_after_fix, args.min_width, args.min_height)
            drop_set = {i.ref for i in unresolved if i.code in {"missing_file", "placeholder_png", "tiny_png", "bad_png"}}
            if drop_set:
                drop_broken_refs(md_files, drop_set, actions)
                refs, _ = collect_refs(md_files)
            else:
                refs = refs_after_fix

    refs_final, _ = collect_refs(md_files)
    after = evaluate(article_dir, refs_final, args.min_width, args.min_height)

    passed = len(after) == 0
    report_path = Path(args.report) if args.report else (diagram_dir / "diagram_guard_report.json")
    report = {
        "article_dir": str(article_dir),
        "mode": args.mode,
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "referenced_diagrams": sorted(refs_final),
        "before_issues": [i.as_dict() for i in before],
        "actions": actions,
        "after_issues": [i.as_dict() for i in after],
        "passed": passed,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[diagram-guard] article={article_dir}")
    print(f"[diagram-guard] mode={args.mode}")
    print(f"[diagram-guard] before={len(before)} issue(s), after={len(after)} issue(s)")
    print(f"[diagram-guard] report={report_path}")
    if actions:
        for action in actions:
            print(f"[diagram-guard] action: {action}")

    if not passed:
        for item in after:
            print(f"[diagram-guard][{item.severity}] {item.code} {item.ref} :: {item.message}", file=sys.stderr)

    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
