#!/usr/bin/env python3
"""
Etapa 5b do guia — heatmap animado + painel de números.

Grid 53 semanas x 7 dias, 6 níveis de cor (tema em config.THEME["heat"]).
Entrada: slide diagonal único (delay = semana + dia), depois congela.
Rodapé com métricas que dizem algo de verdade sobre o ritmo de trabalho:
total no ano, sequência atual, recorde, melhor dia e dia da semana mais
produtivo.

Nível de cor: usa o data-level que o próprio GitHub calcula (quartis
relativos ao seu histórico) — assim o mapa bate com o do perfil oficial.
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402

STATIC = os.environ.get("STATIC") == "1"
CELL, GAP = 13, 3
STEP = CELL + GAP
PAD, BAR = 22, 30
LEFT = 34
WEEKDAYS_PT = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def level(d, maxc):
    if d.get("level") is not None and d["count"]:
        return min(int(d["level"]) + (1 if d["level"] >= 4 and d["count"] >= maxc * 0.9 else 0), 5)
    if not d["count"]:
        return 0
    return min(5, 1 + int(4 * d["count"] / max(maxc, 1)))


def fmt_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day:02d} {config.MONTHS_PT[d.month - 1]}"


def main():
    with open(config.CONTRIB_JSON, encoding="utf-8") as f:
        data = json.load(f)
    days = data["days"]
    t = config.THEME
    maxc = max((d["count"] for d in days), default=1)

    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)   # domingo da 1ª semana
    weeks = (dt.date.fromisoformat(days[-1]["date"]) - start).days // 7 + 1
    grid_w = weeks * STEP
    W = LEFT + grid_w + PAD * 2 - GAP
    grid_top = BAR + PAD + 20
    grid_h = 7 * STEP
    stats_top = grid_top + grid_h + 34
    H = stats_top + 74 + PAD

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{config.FONT_MONO}">',
         "<style>"
         f".l{{fill:{t['muted']};font-size:11px}}"
         ".c{animation:in .5s cubic-bezier(.2,.7,.3,1.2) backwards}"   # base visível; anima só no delay
         "@keyframes in{from{opacity:0;transform:translate(-10px,-10px)}}"
         "@media (prefers-reduced-motion:reduce){.c{animation:none}}"
         + (".c{animation:none}" if STATIC else "")
         + "</style>",
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{t["panel"]}" stroke="{t["border"]}"/>',
         f'<path d="M.5 10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10V{BAR}H.5z" fill="{t["titlebar"]}"/>',
         '<circle cx="18" cy="15" r="5" fill="#ff5f57"/><circle cx="34" cy="15" r="5" fill="#febc2e"/>'
         '<circle cx="50" cy="15" r="5" fill="#28c840"/>',
         f'<text x="{W / 2}" y="19" text-anchor="middle" font-size="11" fill="{t["muted"]}">'
         f'~/contribuicoes — últimos 12 meses</text>']

    x0 = PAD + LEFT
    # rótulos de mês (quando a semana contém o dia 1)
    last_m = None
    for w in range(weeks):
        d0 = start + dt.timedelta(weeks=w)
        for k in range(7):
            dd = d0 + dt.timedelta(days=k)
            if dd.day == 1 and dd.month != last_m and w < weeks - 1:
                o.append(f'<text class="l" x="{x0 + w * STEP}" y="{grid_top - 8}">{config.MONTHS_PT[dd.month - 1]}</text>')
                last_m = dd.month
    for k, name in ((1, "Seg"), (3, "Qua"), (5, "Sex")):
        o.append(f'<text class="l" x="{PAD}" y="{grid_top + k * STEP + 10}">{name}</text>')

    by_date = {d["date"]: d for d in days}
    for w in range(weeks):
        for k in range(7):
            dd = start + dt.timedelta(weeks=w, days=k)
            d = by_date.get(dd.isoformat())
            if not d:
                continue
            lv = level(d, maxc)
            delay = (w + k) * 0.018
            tip = f'{d["count"]} contribuição(ões) em {fmt_date(d["date"])}'
            o.append(f'<rect class="c" x="{x0 + w * STEP}" y="{grid_top + k * STEP}" width="{CELL}" height="{CELL}" rx="3" '
                     f'fill="{t["heat"][lv]}" style="animation-delay:{delay:.3f}s"><title>{tip}</title></rect>')

    # legenda
    lx = W - PAD - 6 * STEP - 70
    ly = grid_top + grid_h + 8
    o.append(f'<text class="l" x="{lx}" y="{ly + 10}">menos</text>')
    for i, c in enumerate(t["heat"]):
        o.append(f'<rect x="{lx + 42 + i * STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>')
    o.append(f'<text class="l" x="{lx + 46 + 6 * STEP}" y="{ly + 10}">mais</text>')
    o.append(f'<text class="l" x="{x0}" y="{ly + 10}">atualizado em {data["generated_at"][:10]} via GitHub Actions</text>')

    # painel de métricas
    wd = data.get("weekday_totals") or [0] * 7
    best_wd = WEEKDAYS_PT[wd.index(max(wd))] if any(wd) else "—"
    tiles = [
        (str(data["total_contributions"]), "contribuições no ano"),
        (f'{data["current_streak"]["length"]}d', "sequência atual"),
        (f'{data["longest_streak"]["length"]}d', "maior sequência"),
        (f'{data["best_day"]["count"]}', f'melhor dia · {fmt_date(data["best_day"]["date"])}'),
        (best_wd, "dia mais produtivo"),
    ]
    tw = (W - PAD * 2 - 4 * 10) / len(tiles)
    for i, (big, small) in enumerate(tiles):
        tx = PAD + i * (tw + 10)
        delay = 1.4 + i * 0.12
        anim = "" if STATIC else (f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur=".5s" fill="freeze"/>')
        o.append(f'<g opacity="{1 if STATIC else 0}">{anim}'
                 f'<rect x="{tx:.1f}" y="{stats_top}" width="{tw:.1f}" height="64" rx="8" fill="{t["bg"]}" stroke="{t["border"]}"/>'
                 f'<rect x="{tx:.1f}" y="{stats_top + 14}" width="3" height="36" rx="1.5" fill="{t["accent2"] if i == 1 else t["accent"]}"/>'
                 f'<text x="{tx + 16:.1f}" y="{stats_top + 31}" font-size="20" font-weight="700" fill="{t["fg"]}">{big}</text>'
                 f'<text x="{tx + 16:.1f}" y="{stats_top + 50}" font-size="11" fill="{t["muted"]}">{small}</text></g>')

    o.append("</svg>")
    os.makedirs(config.ASSETS, exist_ok=True)
    with open(config.HEATMAP_SVG, "w", encoding="utf-8") as f:
        f.write("\n".join(o))
    print(f"ok -> {config.HEATMAP_SVG} ({weeks} semanas)")


if __name__ == "__main__":
    main()
