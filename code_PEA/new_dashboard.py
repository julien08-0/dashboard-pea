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
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap');

    :root {
        --bg:        #0d0f14;
        --surface:   #151820;
        --border:    #1e2330;
        --accent:    #4fffb0;
        --accent2:   #7c6fff;
        --accent3:   #ff6b6b;
        --text:      #e8ecf4;
        --muted:     #6b7280;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'DM Mono', monospace;
    }

    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stSidebar"] { background: var(--surface) !important; }

    /* Titres */
    h1 { font-family: 'DM Serif Display', serif !important; font-size: 2.8rem !important; color: var(--text) !important; letter-spacing: -0.02em; }
    h2 { font-family: 'DM Serif Display', serif !important; color: var(--text) !important; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }
    h3 { font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted) !important; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
    }
    [data-testid="stMetricValue"] { font-family: 'DM Mono', monospace !important; font-size: 1.6rem !important; color: var(--accent) !important; }
    [data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 0.1em; }
    [data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

    /* Tabs */
    [data-testid="stTabs"] button {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted) !important;
        border-radius: 6px 6px 0 0 !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom: 2px solid var(--accent) !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 10px !important; }

    /* Divider */
    hr { border-color: var(--border) !important; }

    .tag {
        display: inline-block;
        background: var(--border);
        color: var(--muted);
        font-size: 0.65rem;
        padding: 2px 8px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-right: 4px;
    }
    .highlight { color: var(--accent); }
    .negative  { color: var(--accent3); }
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
st.markdown("# Dashboard PEA")
st.markdown(f"<span class='tag'>Mise à jour</span> <span style='color:#6b7280;font-size:0.8rem'>{pd.Timestamp.today().strftime('%d %b %Y')}</span>", unsafe_allow_html=True)
st.markdown("")

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
valeur_totale_avec_cash = valeur_totale + cash["cash_tot"].iloc[-1]

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("📊 Valeur en Portefeuille", f"{valeur_portefeuille:,.0f} €")
k2.metric("💰 Valeur Totale", f"{valeur_totale_avec_cash:,.0f} €")
k3.metric("📈 CAGR Global", f"{cagr_global} %")
k4.metric("〰 Vol Globale", f"{vol_global} %")
k5.metric("⚡ Sharpe Global", f"{sharpe_global}")
k6.metric("💵 Cash", f"{cash['cash_tot'].iloc[-1]:,.0f} €")

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab3, tab2, tab1, tab4, tab5 = st.tabs([
    "🌍  Portefeuille",
    "📉  Cours & Achats",
    "📐  Métriques",
    "🔗  Corrélations",
    "🎯  Frontière Efficiente",
])

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono, monospace", color="#e8ecf4", size=11),
    xaxis=dict(gridcolor="#1e2330", zeroline=False),
    yaxis=dict(gridcolor="#1e2330", zeroline=False),
    margin=dict(l=10, r=10, t=40, b=10),
)

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
                return "color: #4fffb0"
            elif val < 0:
                return "color: #ff6b6b"
        return ""

    styled = df_table.style.map(color_val).format("{:.2f}")
    st.dataframe(styled, use_container_width=True, height=280)

    st.markdown("---")
    st.markdown("## Détail par ETF")

    cols = st.columns(3)
    for idx, ticker in enumerate(tickers):
        col = cols[idx % 3]
        ind = indicateurs[ticker]
        color = COLORS[ticker]
        valeur_etf = data_prix_dict[ticker]["prix_tot"].iloc[-1]
        with col:
            st.markdown(f"""
            <div style="background:#151820;border:1px solid #1e2330;border-left:3px solid {color};
                        border-radius:10px;padding:1rem 1.2rem;margin-bottom:1rem">
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;color:#6b7280;margin-bottom:0.5rem">
                    {ticker}
                </div>
                <div style="font-size:1.1rem;font-family:'DM Serif Display',serif;color:#e8ecf4;margin-bottom:0.3rem">
                    {LABELS[ticker]}
                </div>
                <div style="font-size:1.3rem;font-family:'DM Mono',monospace;color:{color};margin-bottom:0.8rem;font-weight:500">
                    {valeur_etf:,.0f} €
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;font-size:0.78rem">
                    <div><span style="color:#6b7280">CAGR</span><br><span style="color:{color}">{ind['cagr']:+.2f}%</span></div>
                    <div><span style="color:#6b7280">TWR</span><br><span style="color:{color}">{ind['twr']:+.2f}%</span></div>
                    <div><span style="color:#6b7280">Sharpe</span><br><span style="color:#e8ecf4">{ind['sharpe']:.2f}</span></div>
                    <div><span style="color:#6b7280">Sortino</span><br><span style="color:#e8ecf4">{ind['sortino']:.2f}</span></div>
                    <div><span style="color:#6b7280">Vol ETF</span><br><span style="color:#e8ecf4">{ind['vol_etf']:.1f}%</span></div>
                    <div><span style="color:#6b7280">Max DD</span><br><span style="color:#ff6b6b">{ind['mdd']:.2f}%</span></div>
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
                color="#ffd166",
                size=10,
                symbol="triangle-up",
                line=dict(color="#0d0f14", width=1.5)
            ),
            hovertemplate="<b>Achat</b><br>Date: %{x}<br>Cours: %{y:.2f}€<extra></extra>"
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=f"{LABELS[ticker_choisi]} — Cours & Achats",
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
            marker=dict(colors=colors_pie, line=dict(color="#0d0f14", width=2)),
            textfont=dict(family="DM Mono, monospace", size=11),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} €<br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(
            **PLOTLY_LAYOUT,
            title="Poids par ETF",
            annotations=[dict(
                text=f"<b>{valeur_totale:,.0f}€</b>",
                x=0.5, y=0.5, font_size=14,
                font_color="#e8ecf4", showarrow=False
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
            marker=dict(color=contrib_colors, line=dict(color="#0d0f14", width=1)),
            hovertemplate="<b>%{x}</b><br>Contribution: %{y:.1f}%<extra></extra>",
        ))
        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            title="Contribution au risque (%)",
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
        title="Valeur totale empilée par ETF",
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
        marker_color="#7c6fff",
    ))
    fig_comp.add_trace(go.Bar(
        name="Optimal",
        x=[LABELS[t] for t in poids_opt.index],
        y=poids_opt.values,
        marker_color="#4fffb0",
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
    with ca:
        st.markdown("**Portefeuille actuel**")
        st.metric("Rendement", f"{comparaison['actuel']['rendement']:.2f} %")
        st.metric("Volatilité", f"{comparaison['actuel']['vol']:.2f} %")
        st.metric("Sharpe", f"{comparaison['actuel']['sharpe']:.2f}")
    with co:
        st.markdown("**Portefeuille optimal**")
        st.metric("Rendement", f"{comparaison['optimal']['rendement']:.2f} %")
        st.metric("Volatilité", f"{comparaison['optimal']['vol']:.2f} %")
        st.metric("Sharpe", f"{comparaison['optimal']['sharpe']:.2f}")

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
            [0.0,  "#ff6b6b"],
            [0.5,  "#151820"],
            [1.0,  "#4fffb0"],
        ],
        zmin=-1, zmax=1,
        text=np.round(corr_values, 2),
        texttemplate="%{text}",
        textfont=dict(size=12, family="DM Mono, monospace"),
        hovertemplate="<b>%{x} / %{y}</b><br>Corrélation: %{z:.2f}<extra></extra>",
    ))
    fig_corr.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Mono, monospace", color="#e8ecf4", size=11),
        margin=dict(l=10, r=10, t=40, b=10),
        height=480,
        xaxis=dict(side="bottom", gridcolor="#1e2330", zeroline=False),
        yaxis=dict(gridcolor="#1e2330", zeroline=False),
    )

    st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("### Lecture rapide")
    col_a, col_b, col_c = st.columns(3)
    col_a.info("**> 0.7** — Forte corrélation, peu de diversification")
    col_b.warning("**0.3 – 0.7** — Corrélation modérée")
    col_c.success("**< 0.3** — Faible corrélation, bonne diversification")

# ────────────────────────────────────────────────────────────────────────────
# TAB 5 — Frontière efficiente
# ────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("## Frontière efficiente")

    fig_front = go.Figure()

    # Nuage de portefeuilles simulés coloré par Sharpe
    fig_front.add_trace(go.Scatter(
        x=df_frontiere["vol"],
        y=df_frontiere["rendement"],
        mode="markers",
        name="Portefeuilles simulés",
        marker=dict(
            color=df_frontiere["sharpe"],
            colorscale=[
                [0.0, "#ff6b6b"],
                [0.5, "#7c6fff"],
                [1.0, "#4fffb0"],
            ],
            size=5,
            opacity=0.7,
            colorbar=dict(
                title="Sharpe",
                tickfont=dict(family="DM Mono, monospace", size=10),
                bgcolor="rgba(0,0,0,0)",
                bordercolor="#1e2330",
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
        marker=dict(color="#ffd166", size=14, symbol="star", line=dict(color="#0d0f14", width=1.5)),
        text=["Actuel"],
        textposition="top center",
        textfont=dict(color="#ffd166", size=11),
    ))

    # Portefeuille optimal
    fig_front.add_trace(go.Scatter(
        x=[comparaison["optimal"]["vol"]],
        y=[comparaison["optimal"]["rendement"]],
        mode="markers+text",
        name="Optimal",
        marker=dict(color="#4fffb0", size=14, symbol="star", line=dict(color="#0d0f14", width=1.5)),
        text=["Optimal"],
        textposition="top center",
        textfont=dict(color="#4fffb0", size=11),
    ))

    fig_front.update_layout(
        **PLOTLY_LAYOUT,
        title="Espace risque/rendement — 1 000 portefeuilles simulés",
        xaxis_title="Volatilité (%)",
        yaxis_title="Rendement (%)",
        height=520,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_front, use_container_width=True)

    st.markdown("### Composition du portefeuille optimal")
    opt_labels = [LABELS[t] for t in df_poids_optimal.index]
    opt_values = df_poids_optimal["poids_optimal (%)"].values
    opt_colors = [COLORS[t] for t in df_poids_optimal.index]

    fig_opt = go.Figure(go.Bar(
        x=opt_labels,
        y=opt_values,
        marker=dict(color=opt_colors, line=dict(color="#0d0f14", width=1)),
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    ))
    fig_opt.update_layout(**PLOTLY_LAYOUT, height=300)
    st.plotly_chart(fig_opt, use_container_width=True)
