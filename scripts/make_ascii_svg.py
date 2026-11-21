#!/usr/bin/env python3
"""
Etapa 3b do guia — foto preparada => SVG ASCII que "se digita".

Decisões:
  * ~100 colunas: abaixo disso o rosto some; acima, o SVG pesa e a fonte
    fica ilegível no card de 370px.
  * Glifo de terminal tem ~2:1 (altura:largura), por isso as linhas são
    amostradas com metade da densidade das colunas.
  * Cada linha é um <text> com textLength fixo: a largura fica idêntica
    em qualquer fonte monoespaçada que o navegador escolher.
  * Animação: clipPath por linha cuja largura cresce (SMIL), com um cursor
    que acompanha — escalonado de cima p/ baixo, roda uma vez e congela.
    Tudo dentro do SVG, porque o GitHub remove <script> e CSS do README.
"""
import os
import sys
from xml.sax.saxutils import escape

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402

COLS = int(os.environ.get("ASCII_COLS", 100))
# Rampa curta = degraus de tom distintos. Rampas de 70 glifos parecem mais
# "ricas", mas viram ruído em fotos pequenas: vizinhos de tom quase igual
# recebem glifos de formas muito diferentes.
RAMP = os.environ.get("ASCII_RAMP", " .:-=+*#%@")
CHAR_W, CHAR_H = 7.2, 13.0
PAD, BAR = 16, 30
ROW_DUR, ROW_STAGGER = 0.22, 0.045
STATIC = os.environ.get("STATIC") == "1"


def to_ascii(path: str):
    img = Image.open(path).convert("L")
    w, h = img.size
    rows = max(1, int(COLS * (h / w) * (CHAR_W / CHAR_H)))
    small = np.asarray(img.resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    # Foto escura sobre card escuro: sem levantar sombras o cabelo (e o contorno
    # da cabeça) simplesmente some. Gamma < 1 clareia os tons baixos; o unsharp
    # realça olhos, sobrancelhas e boca, que é o que faz o rosto ser reconhecível.
    gamma = float(os.environ.get("ASCII_GAMMA", 0.85))
    blur = cv2.GaussianBlur(small, (0, 0), 1.1)
    small = np.clip(small + float(os.environ.get("ASCII_SHARP", 0.0)) * (small - blur), 0, 1)
    lo, hi = np.percentile(small, (3, 97))     # stretch: usa a rampa inteira
    small = np.clip((small - lo) / max(hi - lo, 1e-6), 0, 1) ** gamma
    idx = (small * (len(RAMP) - 1)).round().astype(int)
    lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]
    # remove linhas vazias nas pontas (sem sujeito)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def render(lines):
    t = config.THEME
    inner_w = COLS * CHAR_W
    W = int(inner_w + PAD * 2)
    art_h = len(lines) * CHAR_H
    H = int(max(BAR + PAD + art_h + PAD, W * config.PORTRAIT_ASPECT))
    top = BAR + (H - BAR - art_h) / 2          # centraliza a arte na vertical
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        "<defs>",
    ]
    if not STATIC:
        for i, line in enumerate(lines):
            lw = len(line) * CHAR_W
            begin = i * ROW_STAGGER
            out.append(
                f'<clipPath id="r{i}"><rect x="{PAD}" y="{top + i * CHAR_H - 1}" width="0" height="{CHAR_H + 2}">'
                f'<animate attributeName="width" from="0" to="{lw + 2:.1f}" begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze"/>'
                "</rect></clipPath>"
            )
    out += [
        "</defs>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{t["panel"]}" stroke="{t["border"]}"/>',
        f'<path d="M.5 10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V{BAR}H.5z" fill="{t["titlebar"]}"/>',
        f'<circle cx="18" cy="15" r="5" fill="#ff5f57"/><circle cx="34" cy="15" r="5" fill="#febc2e"/><circle cx="50" cy="15" r="5" fill="#28c840"/>',
        f'<text x="{W / 2}" y="19" text-anchor="middle" font-family="{config.FONT_MONO}" font-size="11" fill="{t["muted"]}">~/portrait.txt</text>',
        f'<g font-family="{config.FONT_MONO}" font-size="11.5" fill="{t["ascii"]}" xml:space="preserve">',
    ]
    last_end = 0.0
    for i, line in enumerate(lines):
        if not line:
            continue
        y = top + (i + 1) * CHAR_H - 3
        lw = len(line) * CHAR_W
        clip = "" if STATIC else f' clip-path="url(#r{i})"'
        out.append(
            f'<text x="{PAD}" y="{y:.1f}" textLength="{lw:.1f}" lengthAdjust="spacingAndGlyphs"{clip}>{escape(line)}</text>'
        )
        if not STATIC:
            begin = i * ROW_STAGGER
            last_end = begin + ROW_DUR
            # cursor: aparece no início da linha, corre junto do wipe e some
            out.append(
                f'<rect x="{PAD}" y="{top + i * CHAR_H}" width="7" height="{CHAR_H - 1}" fill="{t["accent"]}" opacity="0">'
                f'<set attributeName="opacity" to="1" begin="{begin:.3f}s"/>'
                f'<animate attributeName="x" from="{PAD}" to="{PAD + lw:.1f}" begin="{begin:.3f}s" dur="{ROW_DUR}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.3f}s"/>'
                "</rect>"
            )
    out.append("</g>")
    if not STATIC:
        # cursor final piscando depois que o desenho termina
        y = top + art_h - CHAR_H
        out.append(
            f'<rect x="{PAD}" y="{y}" width="7" height="{CHAR_H - 1}" fill="{t["accent"]}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.01;0.5;0.51" dur="1.1s" begin="{last_end:.2f}s" repeatCount="indefinite"/>'
            "</rect>"
        )
    out.append("</svg>")
    return "\n".join(out)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else config.PHOTO_PREPPED
    dst = sys.argv[2] if len(sys.argv) > 2 else config.PORTRAIT_SVG
    lines = to_ascii(src)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(render(lines))
    print(f"ok -> {dst} ({COLS}x{len(lines)})")


if __name__ == "__main__":
    main()
