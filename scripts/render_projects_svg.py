#!/usr/bin/env python3
"""
Vitrine de projetos como saída de `ls -la`, no mesmo tema dos outros cards.

Cada linha: status (calculado por inatividade), nome + descrição (manual),
linguagem dominante, último push, mini-gráfico de 12 semanas e commits em 30d.
Nada aqui é digitado à mão além do nome e da descrição em config.PROJECTS.
"""
import datetime as dt
import json
import os
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402

STATIC = os.environ.get("STATIC") == "1"
SRC = os.environ.get("PROJECTS_JSON", config.PROJECTS_JSON)
W, PAD, BAR = 860, 22, 30
HEAD_H, ROW, FOOT = 34, 46, 44
X_NAME, X_LANG, X_PUSH, X_SPARK, X_N = PAD + 18, 456, 606, 704, W - PAD
LANG_COLORS = {"Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "C#": "#178600",
               "HTML": "#e34c26", "CSS": "#563d7c", "SQL": "#e38c00", "PLSQL": "#dad8d8", "Shell": "#89e051"}


def ago(days):
    if days is None:
        return "—"
    if days < 1:
        return "hoje"
    if days < 14:
        return f"há {days}d"
    if days < 60:
        return f"há {days // 7} sem"
    if days < 365:
        return f"há {days // 30} meses"
    return f"há {days // 365} ano(s)"


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    projects = data["projects"]
    t = config.THEME
    # "unknown" = sem token p/ repo privado e sem dado anterior: cinza vazado, nunca "inativo"
    status_color = {"active": "#28c840", "paused": t["accent2"], "idle": t["muted"], "unknown": t["border"]}
    H = BAR + HEAD_H + ROW * len(projects) + FOOT + PAD // 2
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{config.FONT_MONO}" font-size="12">',
         "<style>"
         # Estado base = VISÍVEL; a animação só esconde durante o delay (fill backwards).
         # Se o renderizador ignorar a animação, o card continua legível.
         ".r{animation:in .5s ease-out backwards}"
         "@keyframes in{from{opacity:0;transform:translateX(-10px)}}"
         ".b{transform-box:fill-box;transform-origin:bottom;animation:g .5s cubic-bezier(.2,.8,.3,1.1) backwards}"
         "@keyframes g{from{transform:scaleY(0)}}"
         ".p{animation:pulse 2.4s ease-in-out infinite}@keyframes pulse{50%{opacity:.35}}"
         "@media (prefers-reduced-motion:reduce){.r,.b,.p{animation:none}}"
         + (".r,.b,.p{animation:none}" if STATIC else "")
         + "</style>",
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{t["panel"]}" stroke="{t["border"]}"/>',
         f'<path d="M.5 10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V{BAR}H.5z" fill="{t["titlebar"]}"/>',
         '<circle cx="18" cy="15" r="5" fill="#ff5f57"/><circle cx="34" cy="15" r="5" fill="#febc2e"/><circle cx="50" cy="15" r="5" fill="#28c840"/>',
         f'<text x="{W / 2}" y="19" text-anchor="middle" font-size="11" fill="{t["muted"]}">~/projetos — ls -la</text>']

    hy = BAR + 24
    for x, label, anchor in ((X_NAME, "PROJETO", "start"), (X_LANG, "LINGUAGEM", "start"), (X_PUSH, "ÚLTIMO PUSH", "start"),
                             (X_SPARK, "12 SEMANAS", "start"), (X_N, "30D", "end")):
        o.append(f'<text x="{x}" y="{hy}" fill="{t["accent2"]}" font-weight="700" font-size="11" text-anchor="{anchor}">{label}</text>')
    o.append(f'<line x1="{PAD}" x2="{W - PAD}" y1="{hy + 9}" y2="{hy + 9}" stroke="{t["border"]}"/>')

    y0 = BAR + HEAD_H
    for i, p in enumerate(projects):
        top = y0 + i * ROW
        st = p.get("status", "idle")
        d = f' style="animation-delay:{0.15 + i * 0.12:.2f}s"'
        pulse = ' class="p"' if st == "active" else ""
        name = escape(p["name"])
        tag = "privado" if p.get("private") else "público"
        tag_x = X_NAME + len(p["name"]) * 7.6 + 10
        w = p.get("weekly") or [0] * 12
        mx = max(max(w), 1)
        bars = []
        for k, v in enumerate(w):
            h = max(3, round(22 * v / mx)) if v else 3
            fill = t["accent"] if v else t["border"]
            bars.append(f'<rect class="b" x="{X_SPARK + k * 8}" y="{top + 30 - h}" width="6" height="{h}" rx="1.5" fill="{fill}" '
                        f'style="animation-delay:{0.4 + i * 0.12 + k * 0.03:.2f}s"/>')
        lang = p.get("language")
        lang_svg = (f'<circle cx="{X_LANG + 4}" cy="{top + 12}" r="4.5" fill="{LANG_COLORS.get(lang, t["muted"])}"/>'
                    f'<text x="{X_LANG + 15}" y="{top + 16}" fill="{t["fg"]}">{escape(lang)} <tspan fill="{t["muted"]}">{p["lang_pct"]}%</tspan></text>'
                    if lang else f'<text x="{X_LANG}" y="{top + 16}" fill="{t["muted"]}">—</text>')
        o.append(f'<g class="r"{d}>'
                 f'<circle{pulse} cx="{PAD + 5}" cy="{top + 12}" r="4.5" fill="{status_color.get(st, t["muted"])}" stroke="{t["muted"] if st == "unknown" else "none"}"/>'
                 f'<text x="{X_NAME}" y="{top + 16}" fill="{t["accent"]}" font-weight="700" font-size="13">{name}</text>'
                 f'<rect x="{tag_x:.1f}" y="{top + 5}" width="{len(tag) * 6.2 + 10:.1f}" height="15" rx="7.5" fill="none" stroke="{t["border"]}"/>'
                 f'<text x="{tag_x + 5:.1f}" y="{top + 16}" font-size="9.5" fill="{t["muted"]}">{tag}</text>'
                 f'<text x="{X_NAME}" y="{top + 34}" fill="{t["muted"]}" font-size="11">{escape(p["desc"])}</text>'
                 f'{lang_svg}'
                 f'<text x="{X_PUSH}" y="{top + 16}" fill="{t["fg"]}">{ago(p.get("days_since_push"))}</text>'
                 f'<text x="{X_N}" y="{top + 16}" fill="{t["accent2"] if p.get("commits_30d") else t["muted"]}" text-anchor="end" font-weight="700">{p.get("commits_30d", 0)}{"+" if p.get("commits_capped") else ""}</text>'
                 f'</g>' + "".join(bars) +
                 f'<line x1="{PAD}" x2="{W - PAD}" y1="{top + ROW - 3}" y2="{top + ROW - 3}" stroke="{t["border"]}" opacity=".5"/>')

    fy = y0 + ROW * len(projects) + 22
    lx = PAD
    for label, col in ((f"ativo · push < {config.STATUS_ACTIVE_DAYS}d", "#28c840"), (f"pausado · < {config.STATUS_PAUSED_DAYS}d", t["accent2"]), ("inativo", t["muted"])):
        o.append(f'<circle cx="{lx + 4}" cy="{fy - 4}" r="4" fill="{col}"/><text x="{lx + 14}" y="{fy}" font-size="11" fill="{t["muted"]}">{escape(label)}</text>')
        lx += 22 + len(label) * 6.6
    o.append(f'<text x="{W - PAD}" y="{fy}" text-anchor="end" font-size="11" fill="{t["muted"]}">atualizado em {data["generated_at"][:10]} · só metadados, nenhum código exposto</text>')
    o.append("</svg>")
    os.makedirs(os.path.dirname(config.PROJECTS_SVG), exist_ok=True)
    out = os.environ.get("OUT", config.PROJECTS_SVG)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"ok -> {out}")


if __name__ == "__main__":
    main()
