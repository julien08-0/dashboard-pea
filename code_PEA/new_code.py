"""
Calcul des indicateurs de performance d'un portefeuille PEA à partir
d'un export de transactions et des cours historiques (yfinance).

Toute la logique est pilotée par le dictionnaire ETFS ci-dessous : ajouter,
retirer ou renommer un ETF suivi ne nécessite de modifier que cette
configuration, rien d'autre dans le reste du fichier ni dans le dashboard.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import brentq, minimize

# ── Configuration ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# Par défaut : le fichier de démo livré avec le repo (données anonymisées, voir
# data/extraction_demo.xlsx) — c'est ce que Streamlit Cloud utilisera puisque
# c'est le seul fichier committé. En local, positionner la variable
# d'environnement PEA_EXCEL_PATH vers son propre export PEA réel (jamais
# committé) pour l'utiliser à la place, sans toucher au code.
EXCEL_PATH = Path(os.environ.get("PEA_EXCEL_PATH", BASE_DIR / "data" / "extraction_demo.xlsx"))
START_DATE = "2024-01-01"
TAUX_SANS_RISQUE = 3.0  # % — utilisé pour Sharpe / Sortino

# Un seul endroit à modifier pour ajouter, retirer ou renommer un ETF suivi.
# "libelle" doit correspondre exactement au libellé de l'opération dans l'export PEA.
ETFS = {
    "PASI.PA": {
        "libelle": "AM.PEA CHINE (MS.C.)SCR.UC.ETF AM.PEA CHN SCREEN.",
        "nom": "MSCI China A",
        "couleur": "#3987e5",
    },
    "PINR.PA": {
        "libelle": "AMUN.PEA INDE UC.ETF ACC FCP AM.PEA INDE ACC",
        "nom": "MSCI India",
        "couleur": "#c98500",
    },
    "ETSZ.DE": {
        "libelle": "BNP PAR.EASY STOX.EU.600 U.ETF BNPETF STOXX 600",
        "nom": "Europe 600",
        "couleur": "#199e70",
    },
    "ESE.PA": {
        "libelle": "BNPP EASY S&P 500 UC.EUR ETF BNPP S&P500EUR ETF",
        "nom": "S&P 500",
        "couleur": "#9085e9",
    },
    "ESEH.PA": {
        "libelle": "BNPP E.S P 500 UCIT.ETF.E.HDG BNPP E.S P 500 U.",
        "nom": "S&P 500 Hedgé",
        "couleur": "#d55181",
    },
    "0P0001DKPN.F": {
        "libelle": "IND.ET EXP.EUROPE SM.IC EUR 4D IE EUROPE SM.IC 4D",
        "nom": "Indép. Europe Small",
        "couleur": "#d95926",
    },
}


# ── Chargement et préparation des transactions ───────────────────────────────
def load_transactions(excel_path, etfs_config):
    """Charge l'export PEA et enrichit chaque ligne (ordre, ticker, horaire, qté cumulée)."""

    df = pd.read_excel(excel_path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    df["date_opération"] = pd.to_datetime(df["date_opération"], errors="coerce")
    df["date_affectation"] = pd.to_datetime(df["date_affectation"], errors="coerce")
    df["montant_net"] = pd.to_numeric(df["montant_net"], errors="coerce")
    df["qté"] = pd.to_numeric(df["qté"], errors="coerce")

    libelle_valide = df["libellé"].notna()
    df["ordre"] = np.select(
        [
            (df["montant_net"] < 0) & libelle_valide,
            (df["montant_net"] > 0) & libelle_valide,
        ],
        ["achat_action", "vente_action"],
        default="ajout_de_capital",
    )

    name_to_ticker = {v["libelle"]: k for k, v in etfs_config.items()}
    df["ticker"] = df["libellé"].map(name_to_ticker)

    df = df.sort_values(by=["date_opération"]).reset_index(drop=True)
    df = _assign_horaire(df)
    df = _assign_qte_totale(df)

    return df


def _assign_horaire(df):
    """Retrouve, pour chaque achat/vente, l'heure de la journée où le cours a été atteint."""

    df["horaire"] = 0

    for i, row in df.iterrows():
        ticker = row["ticker"]
        if pd.isna(ticker):
            continue

        cours = row["cours"]
        date = row["date_opération"]
        date_apres = date + pd.Timedelta(days=1)

        data = yf.download(tickers=ticker, start=date, end=date_apres, interval="1h")

        for timestamp, row_price in data.iterrows():
            prix_close = float(row_price["Close"])
            prix_open = float(row_price["Open"])
            bas, haut = min(prix_close, prix_open), max(prix_close, prix_open)

            if bas < float(cours) < haut:
                df.at[i, "horaire"] = timestamp
                break

    return df


def _assign_qte_totale(df):
    """Quantité cumulée détenue par ticker, dans l'ordre chronologique des opérations."""

    df["qté_totale"] = 0.0
    mask = df["ticker"].notna()
    df.loc[mask, "qté_totale"] = df.loc[mask].groupby("ticker")["qté"].cumsum()
    return df


def find_etfs_non_suivis(df):
    """Achats/ventes dont le libellé ne correspond à aucun ETF de la config ETFS.

    Ces opérations sont bien déduites du cash (voir get_cash_and_frais) mais aucune
    position n'est calculée pour elles : sans ce signal, la valeur du portefeuille
    serait sous-évaluée en silence dès qu'un nouvel ETF est acheté avant d'être ajouté
    à ETFS.
    """

    mask = df["ordre"].isin(["achat_action", "vente_action"]) & df["ticker"].isna()
    colonnes = ["date_opération", "libellé", "montant_net"]
    return df.loc[mask, colonnes].reset_index(drop=True)


# ── Séries de prix / cash / frais ────────────────────────────────────────────
def get_daily_prices(df, ticker, start_date):
    """Cours de clôture journaliers d'un ticker, complétés par le nombre de titres détenus."""

    data = yf.download(ticker, start=start_date, interval="1d")
    data.columns = [c if not isinstance(c, tuple) else c[0] for c in data.columns]
    data = data[["Close"]].rename(columns={"Close": "open_price"}).reset_index()

    data["Date"] = pd.to_datetime(data["Date"])
    data["heure"] = pd.to_datetime("08:00").time()
    # NaN (pas 0.0) : une ligne de cours journalier n'est pas une opération, donc on ne
    # sait pas encore combien de titres sont détenus à cette date. 0.0 est réservé aux
    # vraies lignes d'opération qui soldent totalement la position (vente complète).
    data["nombre_actif"] = np.nan

    operations = df[df["ticker"] == ticker]
    if not operations.empty:
        nouvelles_lignes = pd.DataFrame({
            "Date": pd.to_datetime(operations["date_opération"]),
            "heure": operations["horaire"].apply(lambda h: pd.to_datetime(h).time()),
            "open_price": operations["cours"].astype(float),
            "nombre_actif": operations["qté_totale"].astype(float),
        })
        data = pd.concat([data, nouvelles_lignes], ignore_index=True)

    data = data.sort_values(by=["Date", "heure"]).reset_index(drop=True)
    data["nombre_actif"] = data["nombre_actif"].ffill().fillna(0.0)
    data["prix_tot"] = data["open_price"] * data["nombre_actif"]

    return data


def get_cash_and_frais(df, tickers, start_date):
    """Cash disponible et frais de transaction, cumulés jour par jour."""

    today = pd.Timestamp.today().normalize()
    dates = pd.date_range(start=pd.to_datetime(start_date), end=today, freq="D")

    df_cash = pd.DataFrame({"date": dates, "cash": 0.0, "cash_tot": 0.0})
    df_frais = pd.DataFrame({"date": dates, "frais": 0.0, "frais_tot": 0.0})

    for t in tickers:
        df_frais[f"frais_{t}"] = 0.0
        df_frais[f"frais_{t}_tot"] = 0.0

    for _, row in df.iterrows():
        date_de_mvt = pd.to_datetime(row["date_opération"]).normalize()
        idx_list = df_cash.index[df_cash["date"] == date_de_mvt].tolist()
        if not idx_list:
            continue
        idx = idx_list[0]

        df_cash.at[idx, "cash"] += float(row["montant_net"])

        if row["ordre"] in ("vente_action", "achat_action"):
            frais = abs(abs(float(row["montant_net"])) - abs(float(row["cours"]) * float(row["qté"])))
            df_frais.at[idx, "frais"] += frais

            ticker = row["ticker"]
            if ticker in tickers:
                df_frais.at[idx, f"frais_{ticker}"] += frais

    df_cash["cash_tot"] = df_cash["cash"].cumsum()
    df_frais["frais_tot"] = df_frais["frais"].cumsum()
    for t in tickers:
        df_frais[f"frais_{t}_tot"] = df_frais[f"frais_{t}"].cumsum()

    return df_cash, df_frais


# ── Indicateurs par ETF ───────────────────────────────────────────────────────
def compute_twr(data_prix, frais, ticker):
    """Time-Weighted Return : neutralise l'effet des apports/retraits de capital."""

    operations = []
    nombre_precedent = 0.0
    for i, row in data_prix.iterrows():
        if row["nombre_actif"] != nombre_precedent:
            operations.append(i)
            nombre_precedent = row["nombre_actif"]

    if not operations:
        return 0.0, pd.DataFrame()

    sous_periodes = []
    for k, idx_op in enumerate(operations):
        idx_debut = idx_op + 1
        idx_fin = operations[k + 1] - 1 if k + 1 < len(operations) else len(data_prix) - 1

        if idx_debut > idx_fin:
            continue

        v_depart = data_prix.at[idx_debut, "prix_tot"]
        v_fin = data_prix.at[idx_fin, "prix_tot"]

        date_op = data_prix.at[idx_op, "Date"]
        idx_frais_list = frais.index[frais["date"] == date_op].tolist()
        frais_transac = frais.at[idx_frais_list[0], f"frais_{ticker}"] if idx_frais_list else 0.0

        ri = 0.0 if (v_depart - frais_transac) == 0 else (v_fin - (v_depart - frais_transac)) / (v_depart - frais_transac)

        sous_periodes.append({
            "index_debut": idx_debut, "index_fin": idx_fin,
            "date_debut": data_prix.at[idx_debut, "Date"], "date_fin": data_prix.at[idx_fin, "Date"],
            "frais": frais_transac, "v_depart": v_depart, "v_fin": v_fin, "r": ri,
        })

    r = pd.DataFrame(sous_periodes)
    twr = 1.0
    for _, row in r.iterrows():
        twr *= (1 + row["r"])
    twr = (twr - 1) * 100

    return twr, r


def compute_cagr(data_prix, frais, ticker):
    """Rendement annualisé (Compound Annual Growth Rate) basé sur le TWR."""

    twr, _ = compute_twr(data_prix, frais, ticker)

    date_debut = data_prix["Date"].min()
    date_fin = pd.Timestamp.today().normalize()
    nb_annees = (date_fin - date_debut).days / 365.25

    if nb_annees <= 0:
        return 0.0

    cagr = (1 + twr / 100) ** (1 / nb_annees) - 1
    return round(cagr * 100, 2)


def compute_mwr(df, data_prix, ticker):
    """Money-Weighted Return : taux qui annule la valeur actuelle nette des flux réels."""

    flux = [
        (pd.to_datetime(row["date_opération"]).normalize(), float(row["montant_net"]))
        for _, row in df[df["ticker"] == ticker].iterrows()
    ]
    if not flux:
        return 0.0

    date_fin = pd.Timestamp.today().normalize()
    valeur_finale = data_prix["prix_tot"].iloc[-1]
    date_ref = flux[0][0]

    def van(r):
        total = sum(
            montant / (1 + r) ** ((date - date_ref).days / 365.25)
            for date, montant in flux
        )
        total += valeur_finale / (1 + r) ** ((date_fin - date_ref).days / 365.25)
        return total

    try:
        return round(brentq(van, -0.999, 10.0) * 100, 2)
    except ValueError:
        return None


def _positions_ouvertes(data_prix):
    """Filtre les jours où une position est détenue, hors jours d'opération (évite les sauts de prix)."""

    p = data_prix[["Date", "open_price", "nombre_actif"]].copy()
    p["Date"] = pd.to_datetime(p["Date"]).dt.normalize()
    p["nb_shift"] = p["nombre_actif"].shift(1)

    p = p[(p["nombre_actif"] == p["nb_shift"]) & (p["nombre_actif"] > 0) & (p["open_price"] > 0)]
    return p.groupby("Date")["open_price"].last()


def compute_volatilite(data_prix, ticker):
    """Volatilité annualisée du cours brut de l'ETF vs. celle réellement subie par l'investissement."""

    prix = data_prix[data_prix["open_price"] > 0]["open_price"]
    vol_etf = prix.pct_change().dropna().std() * (252 ** 0.5) * 100

    vol_invest = _positions_ouvertes(data_prix).pct_change().dropna().std() * (252 ** 0.5) * 100

    return round(vol_etf, 2), round(vol_invest, 2)


def compute_sharpe(cagr, vol_invest, taux_sans_risque=TAUX_SANS_RISQUE):
    if vol_invest == 0:
        return None
    return round((cagr - taux_sans_risque) / vol_invest, 2)


def compute_max_drawdown(data_prix):
    p = _positions_ouvertes(data_prix)
    drawdown = (p - p.cummax()) / p.cummax() * 100
    return round(drawdown.min(), 2)


def compute_sortino(data_prix, taux_sans_risque=TAUX_SANS_RISQUE):
    p = _positions_ouvertes(data_prix)
    rendements = p.pct_change().dropna()

    nb_annees = (p.index[-1] - p.index[0]).days / 365.25
    cagr = ((p.iloc[-1] / p.iloc[0]) ** (1 / nb_annees) - 1) * 100

    vol_baisse = rendements[rendements < 0].std() * (252 ** 0.5) * 100
    if vol_baisse == 0:
        return None

    return round((cagr - taux_sans_risque) / vol_baisse, 2)


def compute_indicateurs_par_etf(df, data_prix_dict, frais):
    """Calcule tous les indicateurs de performance pour chaque ETF du portefeuille."""

    indicateurs = {}
    for ticker, data_prix in data_prix_dict.items():
        twr, r = compute_twr(data_prix, frais, ticker)
        cagr = compute_cagr(data_prix, frais, ticker)
        vol_etf, vol_invest = compute_volatilite(data_prix, ticker)

        indicateurs[ticker] = {
            "twr": round(twr, 2),
            "r": r,
            "cagr": cagr,
            "mwr": compute_mwr(df, data_prix, ticker),
            "vol_etf": vol_etf,
            "vol_invest": vol_invest,
            "sharpe": compute_sharpe(cagr, vol_invest),
            "mdd": compute_max_drawdown(data_prix),
            "sortino": compute_sortino(data_prix),
        }

    return indicateurs


# ── Indicateurs sur le portefeuille global ───────────────────────────────────
def _rendements_par_ticker(data_prix_dict):
    rendements = {ticker: _positions_ouvertes(data).pct_change() for ticker, data in data_prix_dict.items()}
    return pd.DataFrame(rendements).dropna()


def compute_correlation_matrix(data_prix_dict):
    return _rendements_par_ticker(data_prix_dict).corr()


def compute_repartition(data_prix_dict):
    repartition = {ticker: data["prix_tot"].iloc[-1] for ticker, data in data_prix_dict.items()}
    valeur_totale = sum(repartition.values())
    poids = {ticker: round(valeur / valeur_totale * 100, 2) for ticker, valeur in repartition.items()}

    df_repartition = pd.DataFrame({"valeur (€)": repartition, "poids (%)": poids})
    return df_repartition, valeur_totale


def compute_sharpe_global(data_prix_dict, df_repartition, taux_sans_risque=TAUX_SANS_RISQUE):
    df_rend = _rendements_par_ticker(data_prix_dict)
    poids = df_repartition.loc[df_rend.columns, "poids (%)"] / 100

    rendement_global = (df_rend * poids).sum(axis=1)
    vol_global = rendement_global.std() * (252 ** 0.5) * 100
    cagr_global = ((1 + rendement_global.mean()) ** 252 - 1) * 100
    sharpe_global = (cagr_global - taux_sans_risque) / vol_global

    return round(cagr_global, 2), round(vol_global, 2), round(sharpe_global, 2)


def compute_risk_contribution(data_prix_dict, df_repartition):
    df_rend = _rendements_par_ticker(data_prix_dict)
    tickers_ordonnes = df_rend.columns.tolist()
    poids = np.array([df_repartition.at[t, "poids (%)"] / 100 for t in tickers_ordonnes])

    cov_matrix = df_rend.cov()
    variance_globale = poids @ cov_matrix.values @ poids
    contribution_marginale = cov_matrix.values @ poids
    contribution_risque = poids * contribution_marginale / variance_globale * 100

    return pd.DataFrame({"contribution_risque (%)": contribution_risque.round(2)}, index=tickers_ordonnes)


def compute_frontiere_efficiente(data_prix_dict, df_repartition, taux_sans_risque=TAUX_SANS_RISQUE, n_portfolios=1000, seed=42):
    """Simule des portefeuilles aléatoires et calcule le portefeuille optimal (max Sharpe)."""

    df_rend = _rendements_par_ticker(data_prix_dict)
    tickers = df_rend.columns.tolist()
    n = len(tickers)

    rendements_annuels = ((1 + df_rend.mean()) ** 252 - 1).values
    cov_matrix = df_rend.cov().values * 252

    rng = np.random.default_rng(seed)
    resultats = []
    for _ in range(n_portfolios):
        poids = rng.dirichlet(np.ones(n))
        ret = poids @ rendements_annuels * 100
        vol = (poids @ cov_matrix @ poids) ** 0.5 * 100
        sharpe = (ret - taux_sans_risque) / vol
        resultats.append({"vol": vol, "rendement": ret, "sharpe": sharpe, "poids": poids})

    df_frontiere = pd.DataFrame(resultats)

    def neg_sharpe(poids):
        ret = poids @ rendements_annuels * 100
        vol = (poids @ cov_matrix @ poids) ** 0.5 * 100
        return -(ret - taux_sans_risque) / vol

    contraintes = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
    bornes = [(0, 0.4) for _ in range(n)]
    result = minimize(neg_sharpe, np.ones(n) / n, method="SLSQP", bounds=bornes, constraints=contraintes)

    poids_optimal = result.x
    ret_optimal = poids_optimal @ rendements_annuels * 100
    vol_optimal = (poids_optimal @ cov_matrix @ poids_optimal) ** 0.5 * 100
    sharpe_optimal = (ret_optimal - taux_sans_risque) / vol_optimal

    df_poids_optimal = pd.DataFrame({"poids_optimal (%)": (poids_optimal * 100).round(2)}, index=tickers)

    poids_actuels = np.array([df_repartition.at[t, "poids (%)"] / 100 for t in tickers])
    ret_actuel = poids_actuels @ rendements_annuels * 100
    vol_actuel = (poids_actuels @ cov_matrix @ poids_actuels) ** 0.5 * 100
    sharpe_actuel = (ret_actuel - taux_sans_risque) / vol_actuel

    comparaison = {
        "actuel": {"vol": vol_actuel, "rendement": ret_actuel, "sharpe": sharpe_actuel},
        "optimal": {"vol": vol_optimal, "rendement": ret_optimal, "sharpe": sharpe_optimal},
    }

    return df_frontiere, df_poids_optimal, comparaison


# ── Orchestration ─────────────────────────────────────────────────────────────
def build_portfolio(excel_path=EXCEL_PATH, etfs_config=ETFS, start_date=START_DATE):
    """Point d'entrée unique : charge les données et calcule tous les indicateurs du portefeuille."""

    df = load_transactions(excel_path, etfs_config)
    tickers = list(etfs_config.keys())

    data_prix_dict = {t: get_daily_prices(df, t, start_date) for t in tickers}
    cash, frais = get_cash_and_frais(df, tickers, start_date)
    indicateurs = compute_indicateurs_par_etf(df, data_prix_dict, frais)

    df_repartition, valeur_totale = compute_repartition(data_prix_dict)
    cagr_global, vol_global, sharpe_global = compute_sharpe_global(data_prix_dict, df_repartition)

    return {
        "df": df,
        "data_prix_dict": data_prix_dict,
        "cash": cash,
        "frais": frais,
        "indicateurs": indicateurs,
        "etfs_non_suivis": find_etfs_non_suivis(df),
        "correlation_matrix": compute_correlation_matrix(data_prix_dict),
        "df_repartition": df_repartition,
        "valeur_totale": valeur_totale,
        "cagr_global": cagr_global,
        "vol_global": vol_global,
        "sharpe_global": sharpe_global,
        "df_contrib": compute_risk_contribution(data_prix_dict, df_repartition),
        **dict(zip(
            ("df_frontiere", "df_poids_optimal", "comparaison"),
            compute_frontiere_efficiente(data_prix_dict, df_repartition),
        )),
    }


if __name__ == "__main__":
    portfolio = build_portfolio()
    print(f"Valeur totale ETF : {portfolio['valeur_totale']:,.0f} €")
    print(f"CAGR global : {portfolio['cagr_global']} %  |  Vol globale : {portfolio['vol_global']} %  |  Sharpe : {portfolio['sharpe_global']}")

    non_suivis = portfolio["etfs_non_suivis"]
    if not non_suivis.empty:
        print(f"\n⚠️  {len(non_suivis)} opération(s) sur des ETF absents de ETFS, non comptées dans les totaux :")
        for libelle in non_suivis["libellé"].unique():
            print(f"   - {libelle}")