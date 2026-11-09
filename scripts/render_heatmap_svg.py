#!/usr/bin/env python3
"""Render contrib-heatmap.svg from data/contributions.json.

53-week x 7-day grid of rounded boxes in the GitHub green ramp, revealed
once with a diagonal slide/fade (CSS keyframes, no looping), a Less->More
legend, and an honest stats footer taken from the real fetched data —
however sparse it is.

Usage: python scripts/render_heatmap_svg.py [in.json] [out.svg]
"""
import json
import sys
from datetime import date, timedelta

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# GitHub levels are 0..4 -> first five palette entries.
LEVEL_FILL = PALETTE[:5]

CELL = 12
STEP = 15.2
PAD_X = 16
TOP = 34          # room for title + month labels
GRID_H = 7 * STEP
W = int(PAD_X * 2 + 53 * STEP)
H = int(TOP + GRID_H + 46)
BG = "#0d1117"
BORDER = "#30363d"
DIM = "#8b949e"
FG = "#c9d1d9"


def daterange_grid(days):
    by_date = {d["date"]: d for d in days}
    first = date.fromisoformat(days[0]["date"])
    last = date.fromisoformat(days[-1]["date"])
    # Back up to the Sunday of the first week (Python: Mon=0 .. Sun=6).
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    weeks = []
    cur = start
    while cur <= last:
        col = []
        for r in range(7):
            d = cur + timedelta(days=r)
            rec = by_date.get(d.isoformat())
            if d < first or d > last or rec is None:
                col.append(None)
            else:
                col.append((d, rec))
        weeks.append(col)
        cur += timedelta(days=7)
    return weeks


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"
    with open(in_path, encoding="utf-8") as f:
        payload = json.load(f)
    days = payload["days"]
    der = payload["derived"]
    weeks = daterange_grid(days)

    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="GitHub contribution heatmap">'
    )
    parts.append(
        "<style>"
        ".cell{opacity:0;animation:rev .35s ease-out forwards}"
        "@keyframes rev{from{opacity:0;transform:translateY(-3px)}to{opacity:1;transform:translateY(0)}}"
        "text{font-family:ui-monospace,Menlo,Consolas,monospace}"
        "</style>"
    )
    parts.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="{BG}" stroke="{BORDER}"/>')
    parts.append(f'<text x="{PAD_X}" y="20" font-size="11.5" fill="{DIM}">contributions — last 53 weeks</text>')

    # Month labels: label a column when its Sunday starts a new month.
    prev_month = None
    for c, col in enumerate(weeks):
        sunday = next((cell for cell in col if cell), None)
        if sunday is None:
            continue
        m = sunday[0].month
        if m != prev_month:
            parts.append(
                f'<text x="{PAD_X + c * STEP:.0f}" y="31" font-size="8.5" fill="{DIM}">'
                f'{sunday[0].strftime("%b")}</text>'
            )
            prev_month = m

    for c, col in enumerate(weeks):
        for r, cell in enumerate(col):
            if cell is None:
                continue
            d, rec = cell
            x = PAD_X + c * STEP
            y = TOP + r * STEP
            fill = LEVEL_FILL[min(rec["level"], 4)]
            delay = (c + r) * 0.028
            parts.append(
                f'<rect class="cell" x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{fill}" style="animation-delay:{delay:.2f}s">'
                f'<title>{d.isoformat()}: {rec["count"]} contribution{"s" if rec["count"] != 1 else ""}</title></rect>'
            )

    fy = TOP + GRID_H + 26
    total = der["total_contributions"]
    footer = f'{total} contribution{"s" if total != 1 else ""} in the last year'
    if der["best_day"]["count"] > 0:
        footer += f' · longest streak {der["longest_streak"]}d · best day {der["best_day"]["count"]} ({der["best_day"]["date"]})'
    parts.append(f'<text x="{PAD_X}" y="{fy}" font-size="10.5" fill="{FG}">{footer}</text>')

    # Less -> More legend, right aligned.
    lx = W - PAD_X - 5 * STEP - 62
    parts.append(f'<text x="{lx:.0f}" y="{fy}" font-size="9.5" fill="{DIM}">Less</text>')
    for i, fill in enumerate(LEVEL_FILL):
        parts.append(
            f'<rect x="{lx + 30 + i * STEP:.1f}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{fill}"/>'
        )
    parts.append(f'<text x="{lx + 34 + 5 * STEP:.0f}" y="{fy}" font-size="9.5" fill="{DIM}">More</text>')

    parts.append("</svg>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")
    print(f"heatmap: {len(weeks)} weeks x 7, {W}x{H}, total={total} -> {out_path}")


if __name__ == "__main__":
    main()
