#!/usr/bin/env python3
"""
Coleta metadados dos projetos listados em config.PROJECTS via REST API.

Segurança:
  * Token só por variável de ambiente (GH_TOKEN), nunca impresso nem salvo.
  * Para repos privados use um fine-grained token SOMENTE LEITURA, limitado
    aos repos da lista (permissões: Metadata + Contents = Read).
  * Só metadados derivados vão para o JSON público (datas, % de linguagem,
    contagem de commits). Nenhuma mensagem de commit, nenhum nome de arquivo.

Resiliência: se um repo falhar (sem acesso, rate limit), reaproveita o
último dado bom de data/projects.json em vez de quebrar o perfil.
"""
import datetime as dt
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402

API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
WEEKS = 12

# O Linguist classifica SQL como linguagem "data" e o exclui de /languages, então
# um repo de queries aparece como "Python". Somamos esses arquivos pela árvore
# (só nome e tamanho, nunca conteúdo) e juntamos ao resultado do GitHub.
EXTRA_LANGS = {
    ".sql": "SQL",
    ".hdbprocedure": "SQL", ".hdbview": "SQL", ".hdbtable": "SQL",
    ".hdbfunction": "SQL", ".hdbcalculationview": "SQL",
}
SKIP_DIRS = ("node_modules/", "vendor/", "dist/", "build/", ".venv/")


def extra_language_bytes(s, repo, branch):
    r = s.get(f"{API}/repos/{repo}/git/trees/{branch}", params={"recursive": 1}, timeout=30)
    if r.status_code != 200:
        return {}
    out = {}
    for item in r.json().get("tree", []):
        path = item.get("path", "")
        if item.get("type") != "blob" or any(d in path for d in SKIP_DIRS):
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext in EXTRA_LANGS:
            out[EXTRA_LANGS[ext]] = out.get(EXTRA_LANGS[ext], 0) + item.get("size", 0)
    return out


def session():
    s = requests.Session()
    s.headers.update({"Accept": "application/vnd.github+json",
                      "X-GitHub-Api-Version": "2022-11-28",
                      "User-Agent": "profile-readme-bot/1.0"})
    if TOKEN:
        s.headers["Authorization"] = f"Bearer {TOKEN}"
    return s


def parse(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def status_for(days):
    if days < config.STATUS_ACTIVE_DAYS:
        return "active"
    return "paused" if days < config.STATUS_PAUSED_DAYS else "idle"


def collect(s, repo, now):
    r = s.get(f"{API}/repos/{repo}", timeout=30)
    r.raise_for_status()
    meta = r.json()

    langs = s.get(f"{API}/repos/{repo}/languages", timeout=30).json()
    for lang, size in extra_language_bytes(s, repo, meta["default_branch"]).items():
        langs[lang] = max(langs.get(lang, 0), size)   # max: se o GitHub já contou, não soma 2x
    total = sum(langs.values()) or 1
    top = max(langs, key=langs.get) if langs else None

    since = (now - dt.timedelta(weeks=WEEKS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    weekly = [0] * WEEKS
    n30 = 0
    capped = False
    for page in (1, 2, 3):
        c = s.get(f"{API}/repos/{repo}/commits", params={"since": since, "per_page": 100, "page": page}, timeout=30)
        if c.status_code == 409:          # repo vazio
            break
        c.raise_for_status()
        items = c.json()
        for it in items:
            age = (now - parse(it["commit"]["committer"]["date"])).days
            weekly[WEEKS - 1 - min(age // 7, WEEKS - 1)] += 1
            n30 += age < 30
        if len(items) < 100:
            break
    else:
        capped = True          # 3 páginas cheias: há mais commits que o limite lido

    pushed = parse(meta["pushed_at"])
    days = (now - pushed).days
    return {"repo": repo, "private": meta["private"], "archived": meta["archived"],
            "pushed_at": meta["pushed_at"], "days_since_push": days,
            "language": top, "lang_pct": round(100 * langs[top] / total) if top else 0,
            "commits_30d": n30, "commits_capped": capped, "weekly": weekly,
            "status": "idle" if meta["archived"] else status_for(days), "ok": True}


def main():
    now = dt.datetime.now(dt.timezone.utc)
    try:
        with open(config.PROJECTS_JSON, encoding="utf-8") as f:
            old = {p["repo"]: p for p in json.load(f)["projects"]}
    except (OSError, ValueError, KeyError):
        old = {}
    s = session()
    # Diagnóstico de credencial (nunca imprime nada do token): um PAT responde
    # /user com o login; o GITHUB_TOKEN do Actions recebe 403.
    if TOKEN:
        u = s.get(f"{API}/user", timeout=30)
        kind = {200: "PAT", 403: "GITHUB_TOKEN (fallback)"}.get(u.status_code, f"HTTP {u.status_code}")
        who = u.json().get("login", "—") if u.status_code == 200 else "—"
        print(f"credencial: {kind} · login {who} · expira {u.headers.get('github-authentication-token-expiration', '—')}")
    else:
        print("credencial: nenhuma (só repos públicos)")
    out, failed = [], 0
    for p in config.PROJECTS:
        try:
            d = collect(s, p["repo"], now)
        except requests.RequestException as e:
            failed += 1
            code = getattr(e.response, "status_code", "erro")
            print(f"! {p['repo']}: {code} — mantendo último dado" if p["repo"] in old
                  else f"! {p['repo']}: {code} — sem dados", file=sys.stderr)
            if code == 404 and TOKEN:
                print(f"  dica: o token não enxerga {p['repo']} — inclua o repo em 'Repository access' "
                      "do fine-grained token (Metadata + Contents: Read)", file=sys.stderr)
            prev = old.get(p["repo"], {"repo": p["repo"], "private": True, "weekly": [0] * WEEKS, "commits_30d": 0})
            # sem dado novo: só mantém o status antigo se ele veio de uma leitura bem-sucedida
            d = {**prev, "ok": False, "status": prev.get("status") if prev.get("ok") else "unknown"}
        out.append({**d, "desc": p["desc"], "name": p["repo"].split("/")[1]})
    os.makedirs(config.DATA, exist_ok=True)
    with open(config.PROJECTS_JSON, "w", encoding="utf-8") as f:
        json.dump({"generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "projects": out}, f, indent=1)
    print(f"ok: {len(out) - failed}/{len(out)} projetos atualizados")


if __name__ == "__main__":
    main()
