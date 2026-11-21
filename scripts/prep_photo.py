#!/usr/bin/env python3
"""
Etapa 3a do guia — prepara a foto para virar ASCII.

Pipeline:
  1. Fonte: assets/source-photo.png (se existir) ou o avatar do GitHub.
  2. Remove o fundo com rembg (se instalado). Sem isso, o fundo vira ruído
     de caracteres e o rosto se perde.
  3. CLAHE (OpenCV): contraste LOCAL. Contraste global estoura a pele e
     apaga a sombra; CLAHE equaliza por blocos, preservando detalhes
     do rosto — é o que dá "volume" ao ASCII.
  4. Compõe sobre PRETO e salva em escala de cinza.
     Por quê preto? O card é escuro e os glifos são claros: pixel claro =>
     glifo denso. Assim o retrato sai positivo, não um negativo.
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402


def load_source() -> Image.Image:
    if os.path.exists(config.PHOTO_SRC):
        print(f"fonte: {config.PHOTO_SRC}")
        return Image.open(config.PHOTO_SRC)
    import requests
    url = f"https://github.com/{config.USERNAME}.png?size=600"
    print(f"fonte: avatar do GitHub ({url})")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))


def remove_background(img: Image.Image) -> Image.Image:
    try:
        from rembg import remove
    except ImportError:
        print("rembg indisponível — seguindo sem remover o fundo", file=sys.stderr)
        return img.convert("RGBA")
    return remove(img.convert("RGBA"))


def local_contrast(gray: np.ndarray) -> np.ndarray:
    try:
        import cv2
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        return clahe.apply(gray)
    except ImportError:
        return np.asarray(ImageOps.autocontrast(Image.fromarray(gray), cutoff=1))


def main():
    img = ImageOps.exif_transpose(load_source())
    rgba = remove_background(img)
    alpha = np.asarray(rgba.split()[-1], dtype=np.float32) / 255.0
    gray = np.asarray(rgba.convert("L"))
    gray = local_contrast(gray).astype(np.float32)
    out = gray * alpha                       # fundo => preto (0)
    # Enquadra a partir da CABEÇA. O bbox do sujeito inteiro estica até os
    # ombros e a cabeça vira ~28% da largura. Mede a cabeça nas linhas do topo
    # e monta o recorte em volta dela (busto ou só rosto, ver config).
    solid = (alpha > 0.5).astype(np.uint8)
    # só o maior objeto: o rembg às vezes deixa manchas soltas (reflexo, objeto
    # no fundo) e elas inflariam a medida da largura da cabeça.
    try:
        import cv2
        n, lab, st, _ = cv2.connectedComponentsWithStats(solid)
        if n > 2:
            solid = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    except ImportError:
        pass
    solid = solid.astype(bool)
    ys, xs = np.where(solid)
    if len(xs):
        top, bottom = ys.min(), ys.max()
        # Largura da cabeça = percentil 90 das larguras nas 40% de cima do sujeito.
        # Em busto (cabeça ~40% da altura) pega só cabeça+orelhas; em rosto
        # fechado (cabeça ~85%) pega a testa/cabelo. Medir mais fundo que isso
        # incluiria os ombros e encolheria o rosto de novo.
        rows = solid[top: top + max(int((bottom - top) * 0.40), 8)]
        widths = rows.sum(axis=1)
        head_w = int(np.percentile(widths[widths > 0], 90) * 1.08)
        cx = int(np.median([np.where(r)[0].mean() for r in rows if r.any()]))
        bx = np.array([cx - head_w // 2, cx + head_w // 2])
        # A proporção do recorte segue a área útil do cartão (~1.31 alt/larg),
        # assim a arte enche o cartão sem distorcer nem sobrar faixa vazia.
        pad = int(0.07 * head_w)
        y0 = max(top - pad, 0)
        if config.PORTRAIT_FRAME == "bust":
            crop_w = int(head_w * config.PORTRAIT_BUST_HEADS)
        else:
            crop_w = head_w + 2 * pad
        crop_h = int(crop_w * 1.31)
        x0 = max(cx - crop_w // 2, 0)
        x1 = min(x0 + crop_w, out.shape[1])
        y1 = min(y0 + crop_h, out.shape[0])
        out = out[y0:y1, x0:x1]
    os.makedirs(config.ASSETS, exist_ok=True)
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(config.PHOTO_PREPPED)
    print(f"ok -> {config.PHOTO_PREPPED}")


if __name__ == "__main__":
    main()
