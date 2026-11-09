#!/usr/bin/env python3
"""Hand-authored neofetch-style info card SVG for Ayush Shukla's profile.

Static content (regenerate only when details change). Each line fades and
slides in with a short CSS stagger so the panel looks like it is printing
next to the ASCII portrait. CSS animations inside an SVG run when GitHub
embeds the file via <img>; there is no JavaScript.

Usage: python scripts/make_info_card.py [out.svg]
"""
import sys
from xml.sax.saxutils import escape

W = 490
BG = "#0d1117"
BORDER = "#30363d"
TITLEBAR = "#161b22"
KEY = "#58a6ff"      # blue keys, like neofetch
VAL = "#c9d1d9"      # light gray values
DIM = "#8b949e"
GREEN = "#3fb950"

# (key, value) rows — content kept accurate to Ayush's profile README draft.
ROWS = [
    ("Role", "Researcher • Engineer • Builder"),
    ("Now", "Research & Prototyping @ Stealth Startup"),
    ("Also", "Security Researcher @ Bugcrowd"),
    ("Focus", "AI Agents • Quantitative Finance"),
    ("", "Security Research"),
    ("Building", "finance-ai-agents (launching soon)"),
    ("Base", "San Francisco / India — Remote"),
    ("Contact", "ayushshukla.business@gmail.com"),
]

LINE_H = 23
TOP = 74  # first row baseline


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    height = TOP + LINE_H * len(ROWS) + 14
    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" aria-label="Info card for Ayush Shukla">'
    )
    parts.append(
        "<style>"
        ".row{opacity:0;animation:print .45s ease-out forwards}"
        "@keyframes print{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:translateX(0)}}"
        "text{font-family:ui-monospace,Menlo,Consolas,monospace}"
        "</style>"
    )
    parts.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="6" fill="{BG}" stroke="{BORDER}"/>')
    # Fake terminal title bar
    parts.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="30" rx="6" fill="{TITLEBAR}"/>')
    parts.append(f'<rect x="0.5" y="16" width="{W - 1}" height="15" fill="{TITLEBAR}"/>')
    for cx, color in ((16, "#f85149"), (36, "#d29922"), (56, "#3fb950")):
        parts.append(f'<circle cx="{cx}" cy="16" r="5.5" fill="{color}"/>')
    parts.append(f'<text x="76" y="20" font-size="11.5" fill="{DIM}">ayush@github: ~/whoami</text>')
    # Header: user + rule, neofetch style
    parts.append(
        f'<g class="row"><text x="18" y="56" font-size="14" font-weight="bold" fill="{GREEN}">ayush@github</text></g>'
    )
    # rows
    for i, (key, val) in enumerate(ROWS):
        y = TOP + i * LINE_H
        delay = 0.35 + i * 0.16
        if key:
            parts.append(
                f'<g class="row" style="animation-delay:{delay:.2f}s">'
                f'<text x="18" y="{y}" font-size="11.5" font-weight="bold" fill="{KEY}">{escape(key)}</text>'
                f'<text x="104" y="{y}" font-size="11.5" fill="{VAL}">{escape(val)}</text></g>'
            )
        else:
            parts.append(
                f'<g class="row" style="animation-delay:{delay:.2f}s">'
                f'<text x="104" y="{y}" font-size="11.5" fill="{VAL}">{escape(val)}</text></g>'
            )
    parts.append("</svg>")
    svg = "\n".join(parts) + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"info card: {W}x{height}, {len(ROWS)} rows -> {out_path}")


if __name__ == "__main__":
    main()
