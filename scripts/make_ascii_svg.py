#!/usr/bin/env python3
"""Turn a photo into a self-typing monochrome ASCII-art SVG.

Pipeline (light deps: Pillow + numpy only):
  photo -> crop to head/shoulders -> grayscale
        -> autocontrast + contrast enhancement (CLAHE substitute)
        -> downsample to a ~100-col character grid
        -> darkness -> glyph density
        -> SVG: one <text> per row, revealed left-to-right by a SMIL
           clip wipe, staggered top-to-bottom, with a small block cursor
           riding the wipe edge. Plays once and freezes (fill="freeze").

Conventional orientation, exactly as in the Avi Vashishta article:
- The source photo is a professional headshot on a WHITE background
  (Ayush's face card: front-on face, navy blazer, light blue shirt).
- The white background composites to the blank end of the ramp (spaces),
  and DARKER areas of the subject map to DENSER glyphs.
- INVERT_DENSITY = False is the current, correct setting for this photo
  (False = density keyed to darkness, i.e. key = 1.0 - brightness).
  Only flip it to True for a lit subject photographed on a dark ground.
- Framing: CROP below keeps the head and shoulders (hair to upper chest,
  including the blazer's dark mass at the bottom) and trims the empty
  white margins at the sides.

Usage: python scripts/make_ascii_svg.py [photo] [out.svg]
The package build used:
  python scripts/make_ascii_svg.py ~/workspace/profile-images/user-headshot.jpg ayush-ascii.svg
"""
import sys
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

RAMP = " .`:-=+*cs#%@"  # sparse -> dense; leading space = blank
# INVERT_DENSITY = False (CURRENT SETTING): conventional article
# orientation for the white-background headshot — white background maps
# to spaces/blank, darker subject areas map to dense glyphs.
# Set to True only for a lit subject on a dark ground.
INVERT_DENSITY = False
# Crop (relative) framing head + shoulders of the headshot: hair at top,
# upper chest / blazer at the bottom, side white margins trimmed.
CROP = (0.05, 0.02, 0.95, 0.78)

COLS = 100
FONT_SIZE = 10
CHAR_W = 6.0        # monospace advance at FONT_SIZE 10 (~0.602em, rounded)
CHAR_H = 9.6        # row pitch
FG = "#c9d1d9"      # one monochrome light-gray fill
BG = "#0d1117"      # terminal background
CURSOR = "#58a6ff"


def build_grid(photo_path):
    img = Image.open(photo_path).convert("L")
    w0, h0 = img.size
    img = img.crop((int(CROP[0] * w0), int(CROP[1] * h0), int(CROP[2] * w0), int(CROP[3] * h0)))
    # Contrast: autocontrast + a contrast lift stands in for OpenCV CLAHE
    # (cv2/rembg are intentionally not required; background removal is
    # skipped too). NOTE: histogram equalisation is deliberately NOT used
    # for this photo — equalising would spread the near-white background's
    # JPEG noise across the whole ramp and print the blank background as
    # glyph static. Autocontrast keeps white at white while spreading the
    # subject's tones, so the face reads in mid-tones.
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    w, h = img.size
    rows = max(1, int(round(COLS * (h / w) * (CHAR_W / CHAR_H))))
    small = img.resize((COLS, rows), Image.LANCZOS)
    arr = np.asarray(small).astype(np.float64) / 255.0  # 1.0 = white
    # Density key (conventional, INVERT_DENSITY=False): darkness — white
    # background -> blank spaces, hair/beard/blazer -> densest glyphs.
    # (INVERT_DENSITY=True would key to brightness instead.)
    key = arr if INVERT_DENSITY else (1.0 - arr)
    idx = np.clip((key * len(RAMP)).astype(int), 0, len(RAMP) - 1)
    lines = ["".join(RAMP[i] for i in row) for row in idx]
    return lines


def render_svg(lines):
    rows = len(lines)
    width = int(COLS * CHAR_W) + 16
    height = int(rows * CHAR_H) + 16
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="ASCII portrait of Ayush Shukla">'
    )
    out.append("<defs>")
    for i in range(rows):
        out.append(
            f'<clipPath id="row{i}"><rect x="8" y="{8 + i * CHAR_H - 8}" '
            f'width="0" height="{CHAR_H + 2}">'
            f'<animate attributeName="width" from="0" to="{COLS * CHAR_W}" '
            f'dur="0.38s" begin="{i * 0.045:.3f}s" fill="freeze"/></rect></clipPath>'
        )
    out.append("</defs>")
    out.append(f'<rect x="0" y="0" width="{width}" height="{height}" rx="6" fill="{BG}"/>')
    for i, line in enumerate(lines):
        y = 8 + (i + 1) * CHAR_H - 2.4
        out.append(
            f'<g clip-path="url(#row{i})"><text x="8" y="{y:.1f}" '
            f'font-family="ui-monospace, Menlo, Consolas, monospace" '
            f'font-size="{FONT_SIZE}" fill="{FG}" xml:space="preserve">{escape(line)}</text></g>'
        )
        # Block cursor riding the wipe edge, fading out as the row finishes.
        out.append(
            f'<rect x="8" y="{8 + i * CHAR_H - 1}" width="{CHAR_W}" height="{CHAR_H}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="8" to="{8 + COLS * CHAR_W}" dur="0.38s" '
            f'begin="{i * 0.045:.3f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0.9;0.9;0" keyTimes="0;0.85;1" '
            f'dur="0.38s" begin="{i * 0.045:.3f}s" fill="freeze"/></rect>'
        )
    out.append("</svg>")
    return "\n".join(out) + "\n", width, height


def main():
    photo = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "ayush-ascii.svg"
    lines = build_grid(photo)
    svg, width, height = render_svg(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"grid: {COLS} cols x {len(lines)} rows | svg: {width}x{height} -> {out_path}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
