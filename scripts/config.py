"""
Fonte única de verdade do profile README.

Tudo que é pessoal (usuário, textos, cores) mora aqui. Os scripts de render
só leem deste módulo, então trocar o tema ou um texto do card é uma edição
de uma linha — sem caçar valores espalhados.
"""
import os

# ── Identidade ──────────────────────────────────────────────────────────────
USERNAME = os.environ.get("GH_PROFILE_USER", "Wyterlin")
PROMPT_USER = "christian"
PROMPT_HOST = "wyterlin"

# ── Caminhos (relativos à raiz do repo) ─────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "data")
PHOTO_SRC = os.path.join(ASSETS, "source-photo.png")      # opcional: foto sua em alta
PHOTO_PREPPED = os.path.join(ASSETS, "source-prepped.png")
PORTRAIT_SVG = os.path.join(ASSETS, "portrait.svg")
INFO_SVG = os.path.join(ASSETS, "info-card.svg")
HEATMAP_SVG = os.path.join(ASSETS, "contrib-heatmap.svg")
CONTRIB_JSON = os.path.join(DATA, "contributions.json")

# ── Tema "HANA console" ─────────────────────────────────────────────────────
# Fundo próprio nos cards => legível tanto no tema claro quanto no escuro do GitHub.
THEME = {
    "bg": "#0b0f14",
    "panel": "#0f1620",
    "border": "#1f2a37",
    "titlebar": "#121b26",
    "fg": "#d6e2ee",
    "muted": "#6b7b8c",
    "accent": "#2dd4bf",     # teal — chaves, prompt
    "accent2": "#f5b942",    # âmbar — destaques
    "ascii": "#9fb3c8",
    # 6 níveis do heatmap (0 = vazio). Teal em vez do verde padrão p/ casar com o tema.
    "heat": ["#151e29", "#0f3d3a", "#11615a", "#14897d", "#1fb5a3", "#5eead4"],
}

# Proporção altura/largura do card do retrato. O README mostra retrato (370px)
# e card hdbsql (490px) lado a lado; 1.34 iguala as alturas das duas colunas.
# Se mudar a qtde de linhas do INFO_ROWS, ajuste aqui (≈ altura_info*490/520/370).
PORTRAIT_ASPECT = 1.34

FONT_MONO = "'JetBrains Mono','Cascadia Code',Consolas,'SFMono-Regular',Menlo,'Courier New',monospace"

# ── Card neofetch ───────────────────────────────────────────────────────────
# (chave, valor). Valor pode ser lista => vira linhas extras alinhadas.
INFO_ROWS = [
    ("Cargo", "Analista de TI"),
    ("Cert", "Consultor SAP Business One · Ramo"),
    ("Core", "SAP B1 on HANA"),
    ("Faço", ["TransactionNotification · PostTransaction",
              "Procedures · Views · Crystal Reports",
              "DTW · layouts de UI · queries"]),
    ("Stack", ["HANA SQL · C#/.NET · Python",
               "JavaScript · HTML · CSS"]),
    ("SDK", "DI API · UI API · Service Layer"),
    ("Estudo", "Ciência da Computação · Estácio"),
    ("Curso", "DEV SAP Business One · Dev Academy"),
    ("Agora", ["AEGIS — IA pessoal estilo JARVIS",
               "Obscura — cofre de senhas",
               "Refactor do repo de queries SAP B1"]),
    ("Local", "Rio de Janeiro · UTC-3"),
]

# ── Vitrine de projetos ─────────────────────────────────────────────────────
# MANUAL de propósito: só entra aqui o que você decidir mostrar. Um repo
# privado novo nunca aparece no perfil público por acidente.
# Dados (último push, linguagem, commits) vêm da API; descrição é sua.
# Descrições: máx. ~60 caracteres (coluna do SVG).
PROJECTS = [
    {"repo": "Wyterlin/aegis", "desc": "IA pessoal estilo JARVIS: memória e tools modulares"},
    {"repo": "Wyterlin/sapb1-sql-scripts", "desc": "Queries, TransactionNotification e procedures p/ SAP B1"},
    {"repo": "Wyterlin/obscura", "desc": "Cofre de senhas com foco em segurança"},
    {"repo": "Wyterlin/performance-dashboard", "desc": "Dashboard de performance"},
    {"repo": "Wyterlin/my-website", "desc": "Portfólio pessoal"},
]
# Status por inatividade (dias desde o último push)
STATUS_ACTIVE_DAYS = 14
STATUS_PAUSED_DAYS = 90
PROJECTS_JSON = os.path.join(DATA, "projects.json")
PROJECTS_SVG = os.path.join(ASSETS, "projects.svg")

# Meses em pt-BR para o heatmap
MONTHS_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
             "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
