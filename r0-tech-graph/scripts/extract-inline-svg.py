#!/usr/bin/env python3
"""Extract the first inline SVG from a self-contained HTML diagram."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SVG_RE = re.compile(r"<svg\b[\s\S]*?</svg>", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="Input HTML file")
    parser.add_argument("svg", type=Path, help="Output SVG file")
    args = parser.parse_args()

    html = args.html.read_text(encoding="utf-8")
    match = SVG_RE.search(html)
    if not match:
        print(f"error: no inline SVG found in {args.html}")
        return 1

    svg = match.group(0).strip()
    if "xmlns=" not in svg.partition(">")[0]:
        svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)

    args.svg.parent.mkdir(parents=True, exist_ok=True)
    args.svg.write_text(svg + "\n", encoding="utf-8")
    print(f"SVG extracted: {args.svg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
