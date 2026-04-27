#!/usr/bin/env python3
"""Wrap a generated SVG technical diagram in a self-contained HTML page."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_CARDS = [
    {
        "title": "Architecture",
        "color": "cyan",
        "items": ["Layered component view", "Boundaries and dependencies", "Primary request path"],
    },
    {
        "title": "Data Flow",
        "color": "emerald",
        "items": ["Read/write paths", "Async or event flows", "External integrations"],
    },
    {
        "title": "Operations",
        "color": "violet",
        "items": ["Runtime ownership", "Observability points", "Risk and scaling notes"],
    },
]


def theme_css(theme: str) -> str:
    if theme == "dark":
        return """
    body {
      font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
      background: #020617;
      min-height: 100vh;
      padding: 2rem;
      color: #ffffff;
    }

    .container { max-width: 1240px; margin: 0 auto; }
    .header { margin-bottom: 2rem; }
    .header-row { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
    .pulse-dot { width: 12px; height: 12px; background: #22d3ee; border-radius: 50%; animation: pulse 2s infinite; }
    h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: 0; }
    .subtitle { color: #94a3b8; font-size: 0.875rem; margin-left: 1.75rem; line-height: 1.7; }

    .diagram-container {
      background: rgba(15, 23, 42, 0.72);
      border-radius: 0.75rem;
      border: 1px solid #1e293b;
      padding: 1.5rem;
      overflow-x: auto;
    }

    .card {
      background: rgba(15, 23, 42, 0.58);
      border-radius: 0.5rem;
      border: 1px solid #1e293b;
      padding: 1.25rem;
    }

    .card h3 { color: #ffffff; }
    .card ul { color: #94a3b8; }
    .card li::before { color: #475569; }
    .footer { color: #475569; }
"""
    return """
    body {
      font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
      background: #f7fafc;
      min-height: 100vh;
      padding: 2rem;
      color: #2d3436;
    }

    .container { max-width: 1240px; margin: 0 auto; }
    .header { margin-bottom: 2rem; }
    .header-row { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
    .pulse-dot {
      width: 12px;
      height: 12px;
      background: #00cec9;
      border-radius: 50%;
      box-shadow: 0 0 0 6px rgba(0, 206, 201, 0.12);
      animation: pulse 2s infinite;
    }
    h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: 0; color: #2d3436; }
    .subtitle { color: #636e72; font-size: 0.875rem; margin-left: 1.75rem; line-height: 1.7; }

    .diagram-container {
      background: #ffffff;
      border-radius: 0.75rem;
      border: 1px solid #dfe6e9;
      padding: 1.5rem;
      overflow-x: auto;
      box-shadow: 0 20px 45px rgba(45, 52, 54, 0.08);
    }

    .card {
      background: #ffffff;
      border-radius: 0.5rem;
      border: 1px solid #dfe6e9;
      padding: 1.25rem;
      box-shadow: 0 12px 30px rgba(45, 52, 54, 0.06);
    }

    .card h3 { color: #2d3436; }
    .card ul { color: #636e72; }
    .card li::before { color: #b2bec3; }
    .footer { color: #636e72; }
"""


def load_svg(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"^\s*<\?xml[^>]*>\s*", "", content)
    content = re.sub(r"^\s*<!DOCTYPE[^>]*>\s*", "", content, flags=re.I)
    start = content.find("<svg")
    if start == -1:
        raise ValueError(f"SVG root not found in {path}")
    return content[start:].strip()


def normalize_cards(value: str | None) -> list[dict[str, Any]]:
    if not value:
        return DEFAULT_CARDS
    raw = json.loads(value)
    if not isinstance(raw, list):
        raise ValueError("--cards must be a JSON array")
    cards: list[dict[str, Any]] = []
    for item in raw[:6]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "Summary"))
        color = str(item.get("color", "cyan"))
        items = item.get("items", [])
        if not isinstance(items, list):
            items = [str(items)]
        cards.append({"title": title, "color": color, "items": [str(x) for x in items[:6]]})
    return cards or DEFAULT_CARDS


def render_cards(cards: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for card in cards:
        title = html.escape(str(card["title"]))
        color = html.escape(str(card.get("color", "cyan")))
        items = "\n".join(
            f"          <li>{html.escape(str(item))}</li>" for item in card.get("items", [])
        )
        chunks.append(
            f"""      <section class="card">
        <div class="card-header">
          <div class="card-dot {color}"></div>
          <h3>{title}</h3>
        </div>
        <ul>
{items}
        </ul>
      </section>"""
        )
    return "\n".join(chunks)


def build_html(
    title: str,
    subtitle: str,
    svg: str,
    cards: list[dict[str, Any]],
    footer: str,
    theme: str,
) -> str:
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_footer = html.escape(footer)
    cards_html = render_cards(cards)
    themed_css = theme_css(theme)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title}</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap" rel="stylesheet">
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

{themed_css}

    @keyframes pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.5; }}
    }}

    .diagram-container svg {{
      width: 100%;
      min-width: 900px;
      display: block;
      border-radius: 0.5rem;
    }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1rem;
      margin-top: 2rem;
    }}

    .card-header {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
    }}

    .card-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex: 0 0 auto;
    }}

    .card-dot.cyan {{ background: #00cec9; }}
    .card-dot.emerald {{ background: #00b894; }}
    .card-dot.violet {{ background: #6c5ce7; }}
    .card-dot.amber {{ background: #fdcb6e; }}
    .card-dot.rose {{ background: #d63031; }}
    .card-dot.pink {{ background: #e84393; }}
    .card-dot.orange {{ background: #e17055; }}

    .card h3 {{
      font-size: 0.875rem;
      font-weight: 600;
    }}

    .card ul {{
      list-style: none;
      font-size: 0.75rem;
      line-height: 1.65;
    }}

    .card li {{
      margin-bottom: 0.375rem;
    }}

    .card li::before {{
      content: "\\2022";
      margin-right: 0.5rem;
    }}

    .footer {{
      text-align: center;
      margin-top: 1.5rem;
      font-size: 0.75rem;
    }}
  </style>
</head>
<body>
  <main class="container">
    <header class="header">
      <div class="header-row">
        <div class="pulse-dot"></div>
        <h1>{safe_title}</h1>
      </div>
      <p class="subtitle">{safe_subtitle}</p>
    </header>

    <section class="diagram-container">
{svg}
    </section>

    <section class="cards">
{cards_html}
    </section>

    <footer class="footer">{safe_footer}</footer>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="Input SVG path")
    parser.add_argument("html", type=Path, help="Output HTML path")
    parser.add_argument("--title", default="Technical Architecture", help="HTML title and page heading")
    parser.add_argument("--subtitle", default="Generated architecture diagram", help="Page subtitle")
    parser.add_argument("--cards", help="JSON array of summary cards")
    parser.add_argument("--footer", default="Generated by r0-tech-graph", help="Footer text")
    parser.add_argument("--theme", choices=("light", "dark"), default="light", help="HTML shell theme")
    args = parser.parse_args()

    svg = load_svg(args.svg)
    cards = normalize_cards(args.cards)
    output = build_html(args.title, args.subtitle, svg, cards, args.footer, args.theme)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(output, encoding="utf-8")
    print(f"HTML generated: {args.html}")


if __name__ == "__main__":
    main()
