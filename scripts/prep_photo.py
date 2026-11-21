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
    # recorta a caixa útil (onde há sujeito) com folga de 4%
    ys, xs = np.where(alpha > 0.1)
    if len(xs):
        pad = int(0.04 * max(out.shape))
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, out.shape[0])
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, out.shape[1])
        out = out[y0:y1, x0:x1]
    os.makedirs(config.ASSETS, exist_ok=True)
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(config.PHOTO_PREPPED)
    print(f"ok -> {config.PHOTO_PREPPED}")


if __name__ == "__main__":
    main()
