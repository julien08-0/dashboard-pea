import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from new_code import ETFS, build_portfolio

# ── Config page ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard PEA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Traductions ────────────────────────────────────────────────────────────────
# Un seul dictionnaire pilote les deux langues : ajouter une chaîne d'interface
# ne nécessite de la déclarer qu'ici, jamais en dur plus bas dans le fichier.
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin",
           "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MOIS_EN = ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]

TRANSLATIONS = {
    "fr": {
        "eyebrow": "Plan d'Épargne en Actions",
        "title": "Portefeuille",
        "updated_on": "Actualisé le {date}",
        "demo_note": "Démo — montants, dates et titres modifiés",
        "warning_non_suivis": (
            "⚠️ **{n} opération(s)** sur **{m} ETF non configuré(s)** dans `ETFS` (new_code.py) — "
            "**{montant:,.0f} €** non pris en compte dans les totaux ci-dessous.\n\n{liste}\n\n"
            "Ajoute ce(s) ticker(s) dans `ETFS` pour qu'ils soient suivis."
        ),
        "hero_label": "Valeur totale du portefeuille",
        "hero_sub": "dont {etf:,.0f} € investis en ETF · {cash:,.0f} € de cash disponible",
        "cagr_annualise": "CAGR annualisé",
        "ledger_valeur_etf": "Valeur ETF",
        "ledger_vol_globale": "Volatilité globale",
        "ledger_sharpe": "Ratio de Sharpe",
        "ledger_cash": "Cash disponible",
        "tabs": ["Portefeuille", "Cours & Achats", "Métriques", "Corrélations", "Frontière efficiente"],
        "tab1_metrics_header": "Métriques par ETF",
        "tab1_detail_header": "Détail par ETF",
        "card_cagr": "CAGR", "card_twr": "TWR", "card_vol_etf": "Vol ETF",
        "card_sharpe": "Sharpe", "card_sortino": "Sortino", "card_mdd": "Max DD",
        "tab2_header": "Évolution du cours avec points d'achat",
        "select_etf": "Choisir un ETF",
        "legend_cours": "Cours",
        "legend_achat": "Achat",
        "hover_achat": "<b>Achat</b><br>Date: %{{x}}<br>Cours: %{{y:.2f}}€<extra></extra>",
        "chart_cours_achats": "{nom} — Cours & Achats",
        "position_dans_le_temps": "Valeur de la position dans le temps",
        "legend_valeur_position": "Valeur position",
        "tab3_repartition": "Répartition du capital",
        "chart_poids_par_etf": "Poids par ETF",
        "chart_contribution_risque": "Contribution au risque (%)",
        "hover_contribution": "<b>%{{x}}</b><br>Contribution: %{{y:.1f}}%<extra></extra>",
        "evolution_valeur_totale": "Évolution de la valeur totale du portefeuille",
        "chart_valeur_empilee": "Valeur totale empilée par ETF",
        "poids_actuel_vs_optimal": "Poids actuel vs Optimal (max Sharpe)",
        "legend_actuel": "Actuel",
        "legend_optimal": "Optimal",
        "carte_portefeuille_actuel": "Portefeuille actuel",
        "carte_portefeuille_optimal": "Portefeuille optimal (max Sharpe)",
        "lbl_rendement": "Rendement", "lbl_volatilite": "Volatilité", "lbl_sharpe": "Sharpe",
        "tab4_header": "Matrice de corrélation",
        "hover_correlation": "<b>%{{x}} / %{{y}}</b><br>Corrélation: %{{z:.2f}}<extra></extra>",
        "lecture_rapide": "Lecture rapide",
        "corr_forte": "**> 0.7** — Forte corrélation, peu de diversification",
        "corr_moderee": "**0.3 – 0.7** — Corrélation modérée",
        "corr_faible": "**< 0.3** — Faible corrélation, bonne diversification",
        "tab5_header": "Frontière efficiente",
        "legend_simules": "Portefeuilles simulés",
        "hover_frontiere": "Vol: %{{x:.1f}}%<br>Rend: %{{y:.1f}}%<extra></extra>",
        "chart_espace_risque": "Espace risque/rendement — 1 000 portefeuilles simulés",
        "axis_volatilite": "Volatilité (%)",
        "axis_rendement": "Rendement (%)",
        "tab5_composition": "Composition du portefeuille optimal",
        "hover_poids": "<b>%{{x}}</b><br>%{{y:.1f}}%<extra></extra>",
    },
    "en": {
        "eyebrow": "Personal Equity Savings Plan (PEA)",
        "title": "Portfolio",
        "updated_on": "Updated on {date}",
        "demo_note": "Demo — amounts, dates and tickers altered",
        "warning_non_suivis": (
            "⚠️ **{n} transaction(s)** on **{m} unconfigured ETF(s)** in `ETFS` (new_code.py) — "
            "**€{montant:,.0f}** not included in the totals below.\n\n{liste}\n\n"
            "Add this/these ticker(s) to `ETFS` to track them."
        ),
        "hero_label": "Total portfolio value",
        "hero_sub": "including €{etf:,.0f} invested in ETFs · €{cash:,.0f} cash available",
        "cagr_annualise": "annualized CAGR",
        "ledger_valeur_etf": "ETF value",
        "ledger_vol_globale": "Overall volatility",
        "ledger_sharpe": "Sharpe ratio",
        "ledger_cash": "Cash available",
        "tabs": ["Portfolio", "Price & Purchases", "Metrics", "Correlations", "Efficient frontier"],
        "tab1_metrics_header": "Metrics by ETF",
        "tab1_detail_header": "Detail by ETF",
        "card_cagr": "CAGR", "card_twr": "TWR", "card_vol_etf": "Vol ETF",
        "card_sharpe": "Sharpe", "card_sortino": "Sortino", "card_mdd": "Max DD",
        "tab2_header": "Price evolution with purchase points",
        "select_etf": "Choose an ETF",
        "legend_cours": "Price",
        "legend_achat": "Purchase",
        "hover_achat": "<b>Purchase</b><br>Date: %{{x}}<br>Price: %{{y:.2f}}€<extra></extra>",
        "chart_cours_achats": "{nom} — Price & Purchases",
        "position_dans_le_temps": "Position value over time",
        "legend_valeur_position": "Position value",
        "tab3_repartition": "Capital allocation",
        "chart_poids_par_etf": "Weight by ETF",
        "chart_contribution_risque": "Risk contribution (%)",
        "hover_contribution": "<b>%{{x}}</b><br>Contribution: %{{y:.1f}}%<extra></extra>",
        "evolution_valeur_totale": "Total portfolio value over time",
        "chart_valeur_empilee": "Total value stacked by ETF",
        "poids_actuel_vs_optimal": "Current vs Optimal weight (max Sharpe)",
        "legend_actuel": "Current",
        "legend_optimal": "Optimal",
        "carte_portefeuille_actuel": "Current portfolio",
        "carte_portefeuille_optimal": "Optimal portfolio (max Sharpe)",
        "lbl_rendement": "Return", "lbl_volatilite": "Volatility", "lbl_sharpe": "Sharpe",
        "tab4_header": "Correlation matrix",
        "hover_correlation": "<b>%{{x}} / %{{y}}</b><br>Correlation: %{{z:.2f}}<extra></extra>",
        "lecture_rapide": "Quick read",
        "corr_forte": "**> 0.7** — High correlation, little diversification",
        "corr_moderee": "**0.3 – 0.7** — Moderate correlation",
        "corr_faible": "**< 0.3** — Low correlation, good diversification",
        "tab5_header": "Efficient frontier",
        "legend_simules": "Simulated portfolios",
        "hover_frontiere": "Vol: %{{x:.1f}}%<br>Return: %{{y:.1f}}%<extra></extra>",
        "chart_espace_risque": "Risk/return space — 1,000 simulated portfolios",
        "axis_volatilite": "Volatility (%)",
        "axis_rendement": "Return (%)",
        "tab5_composition": "Optimal portfolio composition",
        "hover_poids": "<b>%{{x}}</b><br>%{{y:.1f}}%<extra></extra>",
    },
}

if "lang" not in st.session_state:
    st.session_state.lang = "fr"

# ── CSS personnalisé ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,440;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root {
        --bg:          #0b0d11;
        --surface:     #14171e;
        --surface-2:   #191d25;
        --border:      #262b35;
        --border-soft: #1b1f27;
        --ink:         #edf0f4;
        --ink-2:       #9aa3b2;
        --ink-3:       #626b7a;
        --brass:       #c9a15f;
        --brass-soft:  rgba(201,161,95,0.12);
        --brass-line:  rgba(201,161,95,0.4);
        --positive:    #4fbf82;
        --negative:    #e0655c;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg) !important;
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stSidebar"] { background: var(--surface) !important; }
    [data-testid="stMainBlockContainer"] { padding-top: 2.4rem !important; max-width: 1280px; }

    /* Titres */
    h1 { font-family: 'Fraunces', serif !important; font-weight: 500 !important; color: var(--ink) !important; letter-spacing: -0.01em; }
    h2 { font-family: 'Fraunces', serif !important; font-weight: 500 !important; font-size: 1.5rem !important; color: var(--ink) !important; margin-top: 0.4rem !important; }
    h3 { font-family: 'Inter', sans-serif !important; font-size: 0.72rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-3) !important; }

    /* Tabs */
    [data-testid="stTabs"] { margin-top: 0.6rem; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 1.8rem; border-bottom: 1px solid var(--border); }
    [data-testid="stTabs"] button {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em;
        color: var(--ink-3) !important;
        padding: 0 0.1rem 0.8rem 0.1rem !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--ink) !important;
        border-bottom: 2px solid var(--brass) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--brass) !important; }
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 10px !important; font-family: 'IBM Plex Mono', monospace !important; }

    /* Alerts */
    [data-testid="stAlertContainer"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Divider */
    hr { border-color: var(--border) !important; }
    .rule {
        height: 1px;
        margin: 2.2rem 0 1.8rem 0;
        background: linear-gradient(90deg, var(--brass-line) 0%, var(--border) 35%, var(--border) 100%);
    }

    .tag {
        display: inline-block;
        background: var(--surface-2);
        border: 1px solid var(--border);
        color: var(--ink-3);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem;
        padding: 2px 9px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-right: 4px;
    }
    .highlight { color: var(--positive); }
    .negative  { color: var(--negative); }

    /* ── Masthead ── */
    .masthead-eyebrow {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--brass);
        margin-bottom: 0.3rem;
    }
    .masthead-row { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 0.6rem; }
    .masthead-title { font-family: 'Fraunces', serif; font-weight: 500; font-size: 2.6rem; color: var(--ink); letter-spacing: -0.01em; line-height: 1; }
    .masthead-meta { font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: var(--ink-3); display: flex; align-items: center; gap: 0.5rem; }
    .masthead-demo-note { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-style: italic; color: var(--ink-3); margin-top: 0.3rem; }
    .live-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--positive); display: inline-block; box-shadow: 0 0 0 3px rgba(79,191,130,0.15); }

    /* ── Sélecteur de langue ── */
    .lang-switch [data-testid="stSegmentedControl"] { display: flex; justify-content: flex-end; }

    /* ── Hero KPI ── */
    .hero {
        display: grid;
        grid-template-columns: 1.25fr 1fr;
        gap: 0;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 0.4rem;
    }
    .hero-main { padding: 1.9rem 2.2rem; }
    .hero-eyebrow { font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-3); margin-bottom: 0.7rem; }
    .hero-value { font-family: 'Fraunces', serif; font-weight: 500; font-size: 3rem; color: var(--ink); line-height: 1; letter-spacing: -0.01em; font-variant-numeric: tabular-nums; }
    .hero-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; color: var(--ink-3); margin-top: 0.6rem; }
    .hero-chip {
        display: inline-flex; align-items: center; gap: 0.4rem;
        margin-top: 1.1rem; padding: 0.32rem 0.8rem;
        border-radius: 20px; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
        border: 1px solid;
    }
    .hero-chip.positive { color: var(--positive); border-color: rgba(79,191,130,0.35); background: rgba(79,191,130,0.08); }
    .hero-chip.negative { color: var(--negative); border-color: rgba(224,101,92,0.35); background: rgba(224,101,92,0.08); }
    .ledger { display: flex; flex-direction: column; justify-content: center; padding: 1.4rem 2.2rem; background: var(--surface-2); border-left: 1px solid var(--border); }
    .ledger-row { display: flex; justify-content: space-between; align-items: baseline; padding: 0.6rem 0; border-bottom: 1px solid var(--border-soft); }
    .ledger-row:last-child { border-bottom: none; }
    .ledger-label { font-family: 'Inter', sans-serif; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-3); }
    .ledger-value { font-family: 'IBM Plex Mono', monospace; font-size: 1rem; color: var(--ink); font-variant-numeric: tabular-nums; }

    /* ── ETF cards ── */
    .etf-card { background: var(--surface); border: 1px solid var(--border); border-top: 3px solid var(--card-color, var(--brass)); border-radius: 10px; padding: 1.25rem 1.35rem 1.05rem; margin-bottom: 1.2rem; }
    .etf-card .ticker-tag { font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; letter-spacing: 0.08em; color: var(--ink-3); background: var(--surface-2); border: 1px solid var(--border); padding: 2px 9px; border-radius: 20px; display: inline-block; margin-bottom: 0.65rem; }
    .etf-card .name { font-family: 'Fraunces', serif; font-weight: 500; font-size: 1.2rem; color: var(--ink); margin-bottom: 0.1rem; }
    .etf-card .value { font-family: 'IBM Plex Mono', monospace; font-size: 1.35rem; color: var(--card-color, var(--ink)); margin-bottom: 0.85rem; font-variant-numeric: tabular-nums; }
    .etf-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; }
    .etf-grid > div { padding: 0.55rem 0.1rem 0.4rem 0; border-top: 1px solid var(--border-soft); }
    .etf-grid > div:nth-child(-n+3) { border-top: none; }
    .etf-grid .lbl { font-family: 'Inter', sans-serif; font-size: 0.63rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-3); }
    .etf-grid .val { font-family: 'IBM Plex Mono', monospace; font-size: 0.88rem; margin-top: 3px; font-variant-numeric: tabular-nums; }

    .legend-chip { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: var(--ink-2); }
</style>
""", unsafe_allow_html=True)

# ── Sélecteur de langue ───────────────────────────────────────────────────────
st.markdown('<div class="lang-switch">', unsafe_allow_html=True)
st.segmented_control(
    "Langue / Language",
    options=["FR", "EN"],
    default="FR" if st.session_state.lang == "fr" else "EN",
    label_visibility="collapsed",
    key="lang_switch",
    on_change=lambda: st.session_state.update(lang=st.session_state.lang_switch.lower()),
)
st.markdown('</div>', unsafe_allow_html=True)

lang = st.session_state.lang
t = TRANSLATIONS[lang]

# ── Chargement du portefeuille ────────────────────────────────────────────────
# Toute la donnée (transactions, cours, indicateurs) vient d'un seul endroit :
# new_code.build_portfolio(), piloté par la config ETFS. Ajouter un ETF suivi
# ne nécessite de toucher qu'à new_code.ETFS, ce fichier n'a rien à savoir de plus.
@st.cache_data(show_spinner="Chargement du portefeuille…", ttl=3600)
def get_portfolio():
    return build_portfolio()

portfolio = get_portfolio()

df = portfolio["df"]
data_prix_dict = portfolio["data_prix_dict"]
cash = portfolio["cash"]
indicateurs = portfolio["indicateurs"]
etfs_non_suivis = portfolio["etfs_non_suivis"]
correlation_matrix = portfolio["correlation_matrix"]
df_repartition = portfolio["df_repartition"]
valeur_totale = portfolio["valeur_totale"]
cagr_global = portfolio["cagr_global"]
vol_global = portfolio["vol_global"]
sharpe_global = portfolio["sharpe_global"]
df_contrib = portfolio["df_contrib"]
df_frontiere = portfolio["df_frontiere"]
df_poids_optimal = portfolio["df_poids_optimal"]
comparaison = portfolio["comparaison"]

LABELS = {tk: cfg["nom"] for tk, cfg in ETFS.items()}
COLORS = {tk: cfg["couleur"] for tk, cfg in ETFS.items()}
tickers = list(ETFS.keys())

# ── HEADER ────────────────────────────────────────────────────────────────────
today = pd.Timestamp.today()
mois = MOIS_FR if lang == "fr" else MOIS_EN
date_str = f"{today.day} {mois[today.month - 1]} {today.year}"

st.markdown(f"""
<div class="masthead-eyebrow">{t['eyebrow']}</div>
<div class="masthead-row">
    <div class="masthead-title">{t['title']}</div>
    <div class="masthead-meta"><span class="live-dot"></span>{t['updated_on'].format(date=date_str)}</div>
</div>
<div class="masthead-demo-note">{t['demo_note']}</div>
<div class="rule"></div>
""", unsafe_allow_html=True)

# ── Alerte ETF non configurés ─────────────────────────────────────────────────
# Une opération d'achat/vente dont le libellé ne matche aucune entrée de ETFS
# (new_code.py) est bien déduite du cash mais sa position n'est suivie nulle
# part : sans ce bandeau, les totaux ci-dessous seraient sous-évalués en silence.
if not etfs_non_suivis.empty:
    libelles = etfs_non_suivis["libellé"].unique()
    montant_total = etfs_non_suivis["montant_net"].abs().sum()
    liste = "\n".join(f"- **{libelle}**" for libelle in libelles)
    st.warning(t["warning_non_suivis"].format(
        n=len(etfs_non_suivis), m=len(libelles), montant=montant_total, liste=liste,
    ))

# ── KPIs globaux ──────────────────────────────────────────────────────────────
valeur_portefeuille = valeur_totale  # ETFs uniquement
valeur_cash = cash["cash_tot"].iloc[-1]
valeur_totale_avec_cash = valeur_totale + valeur_cash

cagr_sens = "positive" if cagr_global >= 0 else "negative"
cagr_signe = "+" if cagr_global >= 0 else ""
cagr_fleche = "↑" if cagr_global >= 0 else "↓"

st.markdown(f"""
<div class="hero">
    <div class="hero-main">
        <div class="hero-eyebrow">{t['hero_label']}</div>
        <div class="hero-value">{valeur_totale_avec_cash:,.0f} €</div>
        <div class="hero-sub">{t['hero_sub'].format(etf=valeur_portefeuille, cash=valeur_cash)}</div>
        <div class="hero-chip {cagr_sens}">{cagr_fleche} {cagr_signe}{cagr_global:.2f} % {t['cagr_annualise']}</div>
    </div>
    <div class="ledger">
        <div class="ledger-row"><span class="ledger-label">{t['ledger_valeur_etf']}</span><span class="ledger-value">{valeur_portefeuille:,.0f} €</span></div>
        <div class="ledger-row"><span class="ledger-label">{t['ledger_vol_globale']}</span><span class="ledger-value">{vol_global:.2f} %</span></div>
        <div class="ledger-row"><span class="ledger-label">{t['ledger_sharpe']}</span><span class="ledger-value">{sharpe_global:.2f}</span></div>
        <div class="ledger-row"><span class="ledger-label">{t['ledger_cash']}</span><span class="ledger-value">{valeur_cash:,.0f} €</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab3, tab2, tab1, tab4, tab5 = st.tabs(
    [t["tabs"][0], t["tabs"][1], t["tabs"][2], t["tabs"][3], t["tabs"][4]]
)

INK = "#edf0f4"
INK_MUTED = "#9aa3b2"
BORDER_SOFT = "#1f232c"
BRASS = "#c9a15f"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono, monospace", color=INK_MUTED, size=11),
    xaxis=dict(gridcolor=BORDER_SOFT, zeroline=False),
    yaxis=dict(gridcolor=BORDER_SOFT, zeroline=False),
    margin=dict(l=10, r=10, t=40, b=10),
)

# Titre en dict (jamais en simple chaîne) partout où on en met un : Plotly
# affiche littéralement "undefined" si un title_font global existe sans texte.
def titre(text):
    return dict(text=text, font=dict(family="Fraunces, serif", color=INK, size=15))

# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — Récapitulatif des indicateurs
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(f"## {t['tab1_metrics_header']}")

    df_table = pd.DataFrame({
        LABELS[tk]: {
            "TWR (%)": ind["twr"],
            "CAGR (%)": ind["cagr"],
            "MWR (%)": ind["mwr"],
            "Vol ETF (%)": ind["vol_etf"],
            "Vol Invest (%)": ind["vol_invest"],
            "Sharpe": ind["sharpe"],
            "Sortino": ind["sortino"],
            "Max DD (%)": ind["mdd"],
        }
        for tk, ind in indicateurs.items()
    }).T

    def color_val(val):
        if isinstance(val, float):
            if val > 0:
                return "color: #4fbf82"
            elif val < 0:
                return "color: #e0655c"
        return ""

    styled = df_table.style.map(color_val).format("{:.2f}")
    st.dataframe(styled, use_container_width=True, height=280)

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.markdown(f"## {t['tab1_detail_header']}")

    cols = st.columns(3)
    for idx, ticker in enumerate(tickers):
        col = cols[idx % 3]
        ind = indicateurs[ticker]
        color = COLORS[ticker]
        valeur_etf = data_prix_dict[ticker]["prix_tot"].iloc[-1]
        with col:
            st.markdown(f"""
            <div class="etf-card" style="--card-color:{color}">
                <div class="ticker-tag">{ticker}</div>
                <div class="name">{LABELS[ticker]}</div>
                <div class="value">{valeur_etf:,.0f} €</div>
                <div class="etf-grid">
                    <div><div class="lbl">{t['card_cagr']}</div><div class="val" style="color:{color}">{ind['cagr']:+.2f}%</div></div>
                    <div><div class="lbl">{t['card_twr']}</div><div class="val" style="color:{color}">{ind['twr']:+.2f}%</div></div>
                    <div><div class="lbl">{t['card_vol_etf']}</div><div class="val">{ind['vol_etf']:.1f}%</div></div>
                    <div><div class="lbl">{t['card_sharpe']}</div><div class="val">{ind['sharpe']:.2f}</div></div>
                    <div><div class="lbl">{t['card_sortino']}</div><div class="val">{ind['sortino']:.2f}</div></div>
                    <div><div class="lbl">{t['card_mdd']}</div><div class="val" style="color:#e0655c">{ind['mdd']:.2f}%</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — Cours & Achats dans le temps
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"## {t['tab2_header']}")

    ticker_choisi = st.selectbox(
        t["select_etf"],
        options=tickers,
        format_func=lambda tk: f"{LABELS[tk]} ({tk})"
    )

    data_etf = data_prix_dict[ticker_choisi].copy()
    color_etf = COLORS[ticker_choisi]

    # Données prix journaliers (sans doublons)
    prix_journalier = data_etf[data_etf["open_price"] > 0].copy()
    prix_journalier["Date"] = pd.to_datetime(prix_journalier["Date"]).dt.normalize()
    prix_journalier = prix_journalier.groupby("Date")["open_price"].last().reset_index()

    # Points d'achat depuis df
    achats = df[df["ticker"] == ticker_choisi].copy()
    achats = achats[achats["ordre"] == "achat_action"]

    fig = go.Figure()

    # Courbe de prix
    fig.add_trace(go.Scatter(
        x=prix_journalier["Date"],
        y=prix_journalier["open_price"],
        mode="lines",
        name=t["legend_cours"],
        line=dict(color=color_etf, width=2),
        fill="tozeroy",
        fillcolor=f"rgba{tuple(int(color_etf.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.08,)}",
    ))

    # Points d'achat
    if not achats.empty:
        fig.add_trace(go.Scatter(
            x=achats["date_opération"],
            y=achats["cours"],
            mode="markers",
            name=t["legend_achat"],
            marker=dict(
                color=BRASS,
                size=10,
                symbol="triangle-up",
                line=dict(color="#0b0d11", width=1.5)
            ),
            hovertemplate=t["hover_achat"]
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=titre(t["chart_cours_achats"].format(nom=LABELS[ticker_choisi])),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Évolution valeur investie
    st.markdown(f"### {t['position_dans_le_temps']}")

    prix_tot = data_etf.copy()
    prix_tot["Date"] = pd.to_datetime(prix_tot["Date"]).dt.normalize()
    prix_tot = prix_tot[prix_tot["prix_tot"] > 0]
    prix_tot = prix_tot.groupby("Date")["prix_tot"].last().reset_index()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=prix_tot["Date"],
        y=prix_tot["prix_tot"],
        mode="lines",
        name=t["legend_valeur_position"],
        line=dict(color=color_etf, width=2),
        fill="tozeroy",
        fillcolor=f"rgba{tuple(int(color_etf.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}",
    ))
    fig2.update_layout(**PLOTLY_LAYOUT, height=300)
    st.plotly_chart(fig2, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 3 — Portefeuille global
# ────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown(f"## {t['tab3_repartition']}")

    col_pie, col_risk = st.columns(2)

    with col_pie:
        labels_pie = [LABELS[tk] for tk in df_repartition.index]
        values_pie = df_repartition["valeur (€)"].values
        colors_pie = [COLORS[tk] for tk in df_repartition.index]

        fig_pie = go.Figure(go.Pie(
            labels=labels_pie,
            values=values_pie,
            hole=0.55,
            marker=dict(colors=colors_pie, line=dict(color="#0b0d11", width=2)),
            textfont=dict(family="IBM Plex Mono, monospace", size=11),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} €<br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(
            **PLOTLY_LAYOUT,
            title=titre(t["chart_poids_par_etf"]),
            annotations=[dict(
                text=f"<b>{valeur_totale:,.0f}€</b>",
                x=0.5, y=0.5, font_size=14,
                font_color=INK, showarrow=False
            )],
            showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            height=380,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_risk:
        contrib_labels = [LABELS[tk] for tk in df_contrib.index]
        contrib_values = df_contrib["contribution_risque (%)"].values
        contrib_colors = [COLORS[tk] for tk in df_contrib.index]

        fig_bar = go.Figure(go.Bar(
            x=contrib_labels,
            y=contrib_values,
            marker=dict(color=contrib_colors, line=dict(color="#0b0d11", width=1)),
            hovertemplate=t["hover_contribution"],
        ))
        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            title=titre(t["chart_contribution_risque"]),
            height=380,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Évolution valeur totale portefeuille
    st.markdown(f"### {t['evolution_valeur_totale']}")

    all_prix = {}
    for ticker, data in data_prix_dict.items():
        p = data[["Date", "prix_tot"]].copy()
        p["Date"] = pd.to_datetime(p["Date"]).dt.normalize()
        p = p.groupby("Date")["prix_tot"].last()
        all_prix[ticker] = p

    df_all = pd.DataFrame(all_prix).ffill().dropna()
    df_all["total"] = df_all.sum(axis=1)

    fig_tot = go.Figure()

    # Aires empilées par ETF
    for ticker in df_all.columns[:-1]:
        fig_tot.add_trace(go.Scatter(
            x=df_all.index,
            y=df_all[ticker],
            name=LABELS[ticker],
            stackgroup="one",
            line=dict(color=COLORS[ticker], width=0.5),
            fillcolor=COLORS[ticker],
            hovertemplate=f"<b>{LABELS[ticker]}</b><br>%{{y:,.0f}} €<extra></extra>",
        ))

    fig_tot.update_layout(
        **PLOTLY_LAYOUT,
        title=titre(t["chart_valeur_empilee"]),
        height=380,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    )
    st.plotly_chart(fig_tot, use_container_width=True)

    # Comparaison poids actuel vs optimal
    st.markdown(f"### {t['poids_actuel_vs_optimal']}")
    poids_actuel = df_repartition["poids (%)"]
    poids_opt    = df_poids_optimal["poids_optimal (%)"]

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        name=t["legend_actuel"],
        x=[LABELS[tk] for tk in poids_actuel.index],
        y=poids_actuel.values,
        marker_color=BRASS,
    ))
    fig_comp.add_trace(go.Bar(
        name=t["legend_optimal"],
        x=[LABELS[tk] for tk in poids_opt.index],
        y=poids_opt.values,
        marker_color="#3987e5",
    ))
    fig_comp.update_layout(
        **PLOTLY_LAYOUT,
        barmode="group",
        height=340,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Métriques actuel vs optimal
    ca, co = st.columns(2)
    for col, titre_carte, cle, couleur in (
        (ca, t["carte_portefeuille_actuel"], "actuel", BRASS),
        (co, t["carte_portefeuille_optimal"], "optimal", "#3987e5"),
    ):
        m = comparaison[cle]
        with col:
            st.markdown(f"""
            <div class="etf-card" style="--card-color:{couleur}">
                <div class="name">{titre_carte}</div>
                <div class="etf-grid" style="grid-template-columns:1fr 1fr 1fr;margin-top:0.6rem">
                    <div><div class="lbl">{t['lbl_rendement']}</div><div class="val" style="color:{couleur}">{m['rendement']:.2f}%</div></div>
                    <div><div class="lbl">{t['lbl_volatilite']}</div><div class="val">{m['vol']:.2f}%</div></div>
                    <div><div class="lbl">{t['lbl_sharpe']}</div><div class="val">{m['sharpe']:.2f}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 4 — Corrélations
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown(f"## {t['tab4_header']}")

    corr_labels = [LABELS[tk] for tk in correlation_matrix.index]
    corr_values = correlation_matrix.values

    fig_corr = go.Figure(go.Heatmap(
        z=corr_values,
        x=corr_labels,
        y=corr_labels,
        colorscale=[
            [0.0,  "#4fbf82"],
            [0.5,  "#c9a15f"],
            [1.0,  "#e0655c"],
        ],
        zmin=0, zmax=1,
        text=np.round(corr_values, 2),
        texttemplate="%{text}",
        textfont=dict(size=12, family="IBM Plex Mono, monospace"),
        hovertemplate=t["hover_correlation"],
    ))
    fig_corr.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono, monospace", color=INK_MUTED, size=11),
        margin=dict(l=10, r=10, t=40, b=10),
        height=480,
        xaxis=dict(side="bottom", gridcolor=BORDER_SOFT, zeroline=False),
        yaxis=dict(gridcolor=BORDER_SOFT, zeroline=False),
    )

    st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown(f"### {t['lecture_rapide']}")
    col_a, col_b, col_c = st.columns(3)
    col_a.error(t["corr_forte"])
    col_b.warning(t["corr_moderee"])
    col_c.success(t["corr_faible"])

# ────────────────────────────────────────────────────────────────────────────
# TAB 5 — Frontière efficiente
# ────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown(f"## {t['tab5_header']}")

    fig_front = go.Figure()

    # Nuage de portefeuilles simulés coloré par Sharpe — magnitude = une seule
    # teinte du clair au foncé (jamais un arc-en-ciel, qui n'a pas d'ordre perceptif).
    fig_front.add_trace(go.Scatter(
        x=df_frontiere["vol"],
        y=df_frontiere["rendement"],
        mode="markers",
        name=t["legend_simules"],
        marker=dict(
            color=df_frontiere["sharpe"],
            colorscale=[
                [0.0, "#1c2230"],
                [0.35, "#1c5cab"],
                [1.0, "#86b6ef"],
            ],
            size=5,
            opacity=0.75,
            colorbar=dict(
                title="Sharpe",
                tickfont=dict(family="IBM Plex Mono, monospace", size=10),
                bgcolor="rgba(0,0,0,0)",
                bordercolor=BORDER_SOFT,
            ),
        ),
        hovertemplate=t["hover_frontiere"],
    ))

    # Portefeuille actuel
    fig_front.add_trace(go.Scatter(
        x=[comparaison["actuel"]["vol"]],
        y=[comparaison["actuel"]["rendement"]],
        mode="markers+text",
        name=t["legend_actuel"],
        marker=dict(color=BRASS, size=14, symbol="star", line=dict(color="#0b0d11", width=1.5)),
        text=[t["legend_actuel"]],
        textposition="top center",
        textfont=dict(color=BRASS, size=11),
    ))

    # Portefeuille optimal
    fig_front.add_trace(go.Scatter(
        x=[comparaison["optimal"]["vol"]],
        y=[comparaison["optimal"]["rendement"]],
        mode="markers+text",
        name=t["legend_optimal"],
        marker=dict(color="#3987e5", size=14, symbol="star", line=dict(color="#0b0d11", width=1.5)),
        text=[t["legend_optimal"]],
        textposition="top center",
        textfont=dict(color="#3987e5", size=11),
    ))

    fig_front.update_layout(
        **PLOTLY_LAYOUT,
        title=titre(t["chart_espace_risque"]),
        xaxis_title=t["axis_volatilite"],
        yaxis_title=t["axis_rendement"],
        height=560,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_front, use_container_width=True)

    st.markdown(f"### {t['tab5_composition']}")
    opt_labels = [LABELS[tk] for tk in df_poids_optimal.index]
    opt_values = df_poids_optimal["poids_optimal (%)"].values
    opt_colors = [COLORS[tk] for tk in df_poids_optimal.index]

    # Barres fines et espacées (largeur fixe < 1 unité de catégorie) + libellés
    # au-dessus : évite l'effet "gros pavés" de barres larges avec peu de
    # catégories sur une hauteur de graphique standard.
    fig_opt = go.Figure(go.Bar(
        x=opt_labels,
        y=opt_values,
        width=0.4,
        marker=dict(color=opt_colors, line=dict(color="#0b0d11", width=1)),
        text=[f"{v:.1f}%" for v in opt_values],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=11, color=INK),
        hovertemplate=t["hover_poids"],
    ))
    layout_opt = {
        **PLOTLY_LAYOUT,
        "yaxis": dict(gridcolor=BORDER_SOFT, zeroline=False, range=[0, float(opt_values.max()) * 1.25]),
    }
    fig_opt.update_layout(**layout_opt, height=380)
    st.plotly_chart(fig_opt, use_container_width=True)
