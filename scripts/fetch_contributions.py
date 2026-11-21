#!/usr/bin/env python3
"""
Etapa 5a do guia — coleta as contribuições reais, sem token.

Usa o fragmento HTML público que a própria página de perfil carrega
(github.com/users/<user>/contributions). Por que não a API GraphQL?
Ela exige token; com scraping do endpoint público o workflow não depende
de secret nenhum e não tem rate limit de serviço de terceiros.

Trade-off honesto: se o GitHub mudar o markup, o script falha (exit 1) e
o workflow fica vermelho — o README continua mostrando o último SVG bom,
nada quebra para quem visita.
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402


def fetch_days():
    import requests
    from bs4 import BeautifulSoup
    url = f"https://github.com/users/{config.USERNAME}/contributions"
    r = requests.get(url, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        sys.exit("nenhuma célula encontrada — o markup do GitHub pode ter mudado")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        text = tips.get(td.get("id"), "")
        m = re.match(r"([\d,.]+)", text)
        count = 0 if (not m or re.search(r"no contributions", text, re.I)) else int(re.sub(r"\D", "", m.group(1)))
        days.append({"date": date, "count": count, "level": int(td.get("data-level") or 0)})
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    # atual: hoje ainda não acabou, então dia zerado HOJE não quebra a sequência
    i = len(days) - 1
    if i >= 0 and days[i]["count"] == 0:
        i -= 1
    cur = 0
    while i >= 0 and days[i]["count"] > 0:
        cur += 1
        i -= 1
    best = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        best = max(best, run)
    return cur, best


def build(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    top = max(days, key=lambda d: d["count"])
    cur, best = streaks(days)
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    wd = [0] * 7
    for d in days:
        wd[dt.date.fromisoformat(d["date"]).weekday()] += d["count"]
    return {
        "username": config.USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_contributions": total,
        "active_days": active,
        "current_streak": {"length": cur},
        "longest_streak": {"length": best},
        "best_day": {"date": top["date"], "count": top["count"]},
        "weekday_totals": wd,               # seg..dom
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    data = build(fetch_days())
    os.makedirs(config.DATA, exist_ok=True)
    with open(config.CONTRIB_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"ok: {data['total_contributions']} contribuições, streak {data['current_streak']['length']}, "
          f"recorde {data['longest_streak']['length']}")
