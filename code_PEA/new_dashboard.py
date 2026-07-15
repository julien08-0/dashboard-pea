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
    .live-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--positive); display: inline-block; box-shadow: 0 0 0 3px rgba(79,191,130,0.15); }

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

LABELS = {t: cfg["nom"] for t, cfg in ETFS.items()}
COLORS = {t: cfg["couleur"] for t, cfg in ETFS.items()}
tickers = list(ETFS.keys())

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="masthead-eyebrow">Plan d'Épargne en Actions</div>
<div class="masthead-row">
    <div class="masthead-title">Portefeuille</div>
    <div class="masthead-meta"><span class="live-dot"></span>Actualisé le {pd.Timestamp.today().strftime('%d %B %Y')}</div>
</div>
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
    st.warning(
        f"⚠️ **{len(etfs_non_suivis)} opération(s)** sur **{len(libelles)} ETF non configuré(s)** "
        f"dans `ETFS` (new_code.py) — **{montant_total:,.0f} €** non pris en compte dans les totaux "
        f"ci-dessous.\n\n{liste}\n\nAjoute ce(s) ticker(s) dans `ETFS` pour qu'ils soient suivis."
    )

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
        <div class="hero-eyebrow">Valeur totale du portefeuille</div>
        <div class="hero-value">{valeur_totale_avec_cash:,.0f} €</div>
        <div class="hero-sub">dont {valeur_portefeuille:,.0f} € investis en ETF · {valeur_cash:,.0f} € de cash disponible</div>
        <div class="hero-chip {cagr_sens}">{cagr_fleche} {cagr_signe}{cagr_global:.2f} % CAGR annualisé</div>
    </div>
    <div class="ledger">
        <div class="ledger-row"><span class="ledger-label">Valeur ETF</span><span class="ledger-value">{valeur_portefeuille:,.0f} €</span></div>
        <div class="ledger-row"><span class="ledger-label">Volatilité globale</span><span class="ledger-value">{vol_global:.2f} %</span></div>
        <div class="ledger-row"><span class="ledger-label">Ratio de Sharpe</span><span class="ledger-value">{sharpe_global:.2f}</span></div>
        <div class="ledger-row"><span class="ledger-label">Cash disponible</span><span class="ledger-value">{valeur_cash:,.0f} €</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab3, tab2, tab1, tab4, tab5 = st.tabs([
    "Portefeuille",
    "Cours & Achats",
    "Métriques",
    "Corrélations",
    "Frontière efficiente",
])

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
    st.markdown("## Métriques par ETF")

    df_table = pd.DataFrame({
        LABELS[t]: {
            "TWR (%)": ind["twr"],
            "CAGR (%)": ind["cagr"],
            "MWR (%)": ind["mwr"],
            "Vol ETF (%)": ind["vol_etf"],
            "Vol Invest (%)": ind["vol_invest"],
            "Sharpe": ind["sharpe"],
            "Sortino": ind["sortino"],
            "Max DD (%)": ind["mdd"],
        }
        for t, ind in indicateurs.items()
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
    st.markdown("## Détail par ETF")

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
                    <div><div class="lbl">CAGR</div><div class="val" style="color:{color}">{ind['cagr']:+.2f}%</div></div>
                    <div><div class="lbl">TWR</div><div class="val" style="color:{color}">{ind['twr']:+.2f}%</div></div>
                    <div><div class="lbl">Vol ETF</div><div class="val">{ind['vol_etf']:.1f}%</div></div>
                    <div><div class="lbl">Sharpe</div><div class="val">{ind['sharpe']:.2f}</div></div>
                    <div><div class="lbl">Sortino</div><div class="val">{ind['sortino']:.2f}</div></div>
                    <div><div class="lbl">Max DD</div><div class="val" style="color:#e0655c">{ind['mdd']:.2f}%</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — Cours & Achats dans le temps
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("## Évolution du cours avec points d'achat")

    ticker_choisi = st.selectbox(
        "Choisir un ETF",
        options=tickers,
        format_func=lambda t: f"{LABELS[t]} ({t})"
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
        name="Cours",
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
            name="Achat",
            marker=dict(
                color=BRASS,
                size=10,
                symbol="triangle-up",
                line=dict(color="#0b0d11", width=1.5)
            ),
            hovertemplate="<b>Achat</b><br>Date: %{x}<br>Cours: %{y:.2f}€<extra></extra>"
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=titre(f"{LABELS[ticker_choisi]} — Cours & Achats"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Évolution valeur investie
    st.markdown("### Valeur de la position dans le temps")

    prix_tot = data_etf.copy()
    prix_tot["Date"] = pd.to_datetime(prix_tot["Date"]).dt.normalize()
    prix_tot = prix_tot[prix_tot["prix_tot"] > 0]
    prix_tot = prix_tot.groupby("Date")["prix_tot"].last().reset_index()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=prix_tot["Date"],
        y=prix_tot["prix_tot"],
        mode="lines",
        name="Valeur position",
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
    st.markdown("## Répartition du capital")

    col_pie, col_risk = st.columns(2)

    with col_pie:
        labels_pie = [LABELS[t] for t in df_repartition.index]
        values_pie = df_repartition["valeur (€)"].values
        colors_pie = [COLORS[t] for t in df_repartition.index]

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
            title=titre("Poids par ETF"),
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
        contrib_labels = [LABELS[t] for t in df_contrib.index]
        contrib_values = df_contrib["contribution_risque (%)"].values
        contrib_colors = [COLORS[t] for t in df_contrib.index]

        fig_bar = go.Figure(go.Bar(
            x=contrib_labels,
            y=contrib_values,
            marker=dict(color=contrib_colors, line=dict(color="#0b0d11", width=1)),
            hovertemplate="<b>%{x}</b><br>Contribution: %{y:.1f}%<extra></extra>",
        ))
        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            title=titre("Contribution au risque (%)"),
            height=380,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Évolution valeur totale portefeuille
    st.markdown("### Évolution de la valeur totale du portefeuille")

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
        title=titre("Valeur totale empilée par ETF"),
        height=380,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    )
    st.plotly_chart(fig_tot, use_container_width=True)

    # Comparaison poids actuel vs optimal
    st.markdown("### Poids actuel vs Optimal (max Sharpe)")
    poids_actuel = df_repartition["poids (%)"]
    poids_opt    = df_poids_optimal["poids_optimal (%)"]

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        name="Actuel",
        x=[LABELS[t] for t in poids_actuel.index],
        y=poids_actuel.values,
        marker_color=BRASS,
    ))
    fig_comp.add_trace(go.Bar(
        name="Optimal",
        x=[LABELS[t] for t in poids_opt.index],
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
        (ca, "Portefeuille actuel", "actuel", BRASS),
        (co, "Portefeuille optimal (max Sharpe)", "optimal", "#3987e5"),
    ):
        m = comparaison[cle]
        with col:
            st.markdown(f"""
            <div class="etf-card" style="--card-color:{couleur}">
                <div class="name">{titre_carte}</div>
                <div class="etf-grid" style="grid-template-columns:1fr 1fr 1fr;margin-top:0.6rem">
                    <div><div class="lbl">Rendement</div><div class="val" style="color:{couleur}">{m['rendement']:.2f}%</div></div>
                    <div><div class="lbl">Volatilité</div><div class="val">{m['vol']:.2f}%</div></div>
                    <div><div class="lbl">Sharpe</div><div class="val">{m['sharpe']:.2f}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 4 — Corrélations
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("## Matrice de corrélation")

    corr_labels = [LABELS[t] for t in correlation_matrix.index]
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
        hovertemplate="<b>%{x} / %{y}</b><br>Corrélation: %{z:.2f}<extra></extra>",
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

    st.markdown("### Lecture rapide")
    col_a, col_b, col_c = st.columns(3)
    col_a.error("**> 0.7** — Forte corrélation, peu de diversification")
    col_b.warning("**0.3 – 0.7** — Corrélation modérée")
    col_c.success("**< 0.3** — Faible corrélation, bonne diversification")

# ────────────────────────────────────────────────────────────────────────────
# TAB 5 — Frontière efficiente
# ────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("## Frontière efficiente")

    fig_front = go.Figure()

    # Nuage de portefeuilles simulés coloré par Sharpe — magnitude = une seule
    # teinte du clair au foncé (jamais un arc-en-ciel, qui n'a pas d'ordre perceptif).
    fig_front.add_trace(go.Scatter(
        x=df_frontiere["vol"],
        y=df_frontiere["rendement"],
        mode="markers",
        name="Portefeuilles simulés",
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
        hovertemplate="Vol: %{x:.1f}%<br>Rend: %{y:.1f}%<extra></extra>",
    ))

    # Portefeuille actuel
    fig_front.add_trace(go.Scatter(
        x=[comparaison["actuel"]["vol"]],
        y=[comparaison["actuel"]["rendement"]],
        mode="markers+text",
        name="Actuel",
        marker=dict(color=BRASS, size=14, symbol="star", line=dict(color="#0b0d11", width=1.5)),
        text=["Actuel"],
        textposition="top center",
        textfont=dict(color=BRASS, size=11),
    ))

    # Portefeuille optimal
    fig_front.add_trace(go.Scatter(
        x=[comparaison["optimal"]["vol"]],
        y=[comparaison["optimal"]["rendement"]],
        mode="markers+text",
        name="Optimal",
        marker=dict(color="#3987e5", size=14, symbol="star", line=dict(color="#0b0d11", width=1.5)),
        text=["Optimal"],
        textposition="top center",
        textfont=dict(color="#3987e5", size=11),
    ))

    fig_front.update_layout(
        **PLOTLY_LAYOUT,
        title=titre("Espace risque/rendement — 1 000 portefeuilles simulés"),
        xaxis_title="Volatilité (%)",
        yaxis_title="Rendement (%)",
        height=560,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_front, use_container_width=True)

    st.markdown("### Composition du portefeuille optimal")
    opt_labels = [LABELS[t] for t in df_poids_optimal.index]
    opt_values = df_poids_optimal["poids_optimal (%)"].values
    opt_colors = [COLORS[t] for t in df_poids_optimal.index]

    fig_opt = go.Figure(go.Bar(
        x=opt_labels,
        y=opt_values,
        marker=dict(color=opt_colors, line=dict(color="#0b0d11", width=1)),
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    ))
    fig_opt.update_layout(**PLOTLY_LAYOUT, height=300)
    st.plotly_chart(fig_opt, use_container_width=True)
