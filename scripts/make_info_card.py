#!/usr/bin/env python3
"""
Etapa 4 do guia — o card de informações, com um twist de identidade:
em vez de um neofetch genérico, é uma sessão `hdbsql` (cliente de linha de
comando do SAP HANA) rodando uma query que devolve o seu perfil como
result set. Quem é do ecossistema SAP reconhece na hora; quem não é,
entende pelo formato de tabela.

Se data/contributions.json existir, a última linha da query mostra
números reais de atividade — o card deixa de ser só "bio" e vira dado vivo.

STATIC=1 gera um frame congelado (útil para preview/PNG).
"""
import json
import os
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402

STATIC = os.environ.get("STATIC") == "1"
W = 520
PAD, BAR, LH = 18, 30, 19
KEY_W = 82            # largura da coluna CAMPO
FS = 12.5
STAGGER, FADE = 0.09, 0.45


def live_rows():
    try:
        with open(config.CONTRIB_JSON, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return []
    return [("Commits", f'{d["total_contributions"]} no último ano · '
                        f'streak {d["current_streak"]["length"]}d · recorde {d["longest_streak"]["length"]}d')]


def flatten(rows):
    for key, val in rows:
        vals = val if isinstance(val, list) else [val]
        for j, v in enumerate(vals):
            yield (key if j == 0 else ""), v


def anim(i, extra=0.0):
    if STATIC:
        return ""
    b = 0.6 + i * STAGGER + extra
    return (f'<animate attributeName="opacity" from="0" to="1" begin="{b:.2f}s" dur="{FADE}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="-8 0" to="0 0" '
            f'begin="{b:.2f}s" dur="{FADE}s" fill="freeze"/>')


def main():
    t = config.THEME
    rows = list(flatten(config.INFO_ROWS + live_rows()))
    n = len(rows)
    # layout: prompt(1) + query(2) + blank + header + sep + rows + sep + status
    top = BAR + PAD + 6
    H = top + LH * (n + 8) + PAD
    op0 = "1" if STATIC else "0"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{config.FONT_MONO}" font-size="{FS}">',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{t["panel"]}" stroke="{t["border"]}"/>',
         f'<path d="M.5 10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V{BAR}H.5z" fill="{t["titlebar"]}"/>',
         '<circle cx="18" cy="15" r="5" fill="#ff5f57"/><circle cx="34" cy="15" r="5" fill="#febc2e"/>'
         '<circle cx="50" cy="15" r="5" fill="#28c840"/>',
         f'<text x="{W / 2}" y="19" text-anchor="middle" font-size="11" fill="{t["muted"]}">'
         f'hdbsql — {config.PROMPT_USER}@{config.PROMPT_HOST}:30015</text>']

    y = top
    # linha 1: prompt + query digitada (wipe via clipPath)
    q1 = 'SELECT CAMPO, VALOR FROM "CHRISTIAN"."PERFIL"'
    q2 = "  WHERE ATIVO = 'Y' ORDER BY PRIORIDADE;"
    for k, q in enumerate((q1, q2)):
        prefix = "hdbsql=> " if k == 0 else "      -> "
        full = prefix + q
        tw = len(full) * FS * 0.6
        if not STATIC:
            o.append(f'<clipPath id="q{k}"><rect x="{PAD}" y="{y - LH + 4}" width="0" height="{LH}">'
                     f'<animate attributeName="width" to="{tw + 4:.0f}" begin="{k * 0.3:.1f}s" dur="0.3s" fill="freeze"/>'
                     '</rect></clipPath>')
        clip = "" if STATIC else f' clip-path="url(#q{k})"'
        o.append(f'<text x="{PAD}" y="{y}"{clip} xml:space="preserve">'
                 f'<tspan fill="{t["accent"]}">{escape(prefix)}</tspan>'
                 f'<tspan fill="{t["fg"]}">{escape(q)}</tspan></text>')
        y += LH
    y += LH * 0.5

    # header + separadores
    sep_w = W - PAD * 2
    o.append(f'<g opacity="{op0}">{anim(0)}'
             f'<text x="{PAD}" y="{y}" fill="{t["accent2"]}" font-weight="700">CAMPO</text>'
             f'<text x="{PAD + KEY_W + 14}" y="{y}" fill="{t["accent2"]}" font-weight="700">VALOR</text>'
             f'<line x1="{PAD}" x2="{PAD + sep_w}" y1="{y + 7}" y2="{y + 7}" stroke="{t["border"]}"/>'
             f'<line x1="{PAD + KEY_W + 6}" x2="{PAD + KEY_W + 6}" y1="{y - 13}" y2="{y + 7 + LH * n + 4}" stroke="{t["border"]}"/>'
             '</g>')
    y += LH + 6

    for i, (key, val) in enumerate(rows, start=1):
        hl = key == "Commits"
        o.append(f'<g opacity="{op0}">{anim(i)}'
                 f'<text x="{PAD}" y="{y}" fill="{t["accent"]}">{escape(key)}</text>'
                 f'<text x="{PAD + KEY_W + 14}" y="{y}" fill="{t["accent2"] if hl else t["fg"]}">{escape(val)}</text>'
                 '</g>')
        y += LH

    o.append(f'<line x1="{PAD}" x2="{PAD + sep_w}" y1="{y - 11}" y2="{y - 11}" stroke="{t["border"]}" opacity="{op0}">'
             + ("" if STATIC else f'<set attributeName="opacity" to="1" begin="{0.6 + n * STAGGER:.2f}s"/>') + '</line>')
    y += LH * 0.4
    distinct = len({k for k, _ in rows if k})
    o.append(f'<g opacity="{op0}">{anim(n + 1, 0.15)}'
             f'<text x="{PAD}" y="{y}" fill="{t["muted"]}">{distinct} rows selected (overall time 0.42 ms)</text></g>')
    y += LH
    # prompt final com cursor piscando
    cur_begin = 0.6 + (n + 2) * STAGGER + 0.3
    o.append(f'<g opacity="{op0}">' + ("" if STATIC else f'<set attributeName="opacity" to="1" begin="{cur_begin:.2f}s"/>')
             + f'<text x="{PAD}" y="{y}" fill="{t["accent"]}">hdbsql=&gt;</text>'
             f'<rect x="{PAD + 9 * FS * 0.6 + 4:.1f}" y="{y - 11}" width="7.5" height="14" fill="{t["accent"]}">'
             + ("" if STATIC else '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/>')
             + '</rect></g>')
    o.append("</svg>")

    os.makedirs(config.ASSETS, exist_ok=True)
    with open(config.INFO_SVG, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"ok -> {config.INFO_SVG} ({n} linhas)")


if __name__ == "__main__":
    main()
