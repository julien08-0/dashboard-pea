# Dashboard PEA

Dashboard de suivi de portefeuille PEA multi-ETF : à partir d'un export de
transactions, il calcule les indicateurs de performance par ETF et pour le
portefeuille global, et les affiche dans une interface Streamlit interactive.

**Démo en ligne :** [dashboard-pea-julien.streamlit.app](https://dashboard-pea-julien.streamlit.app/)
*(données anonymisées à but de démonstration — voir plus bas)*

## Fonctionnalités

- **Indicateurs par ETF** : TWR, CAGR, MWR, volatilité, ratio de Sharpe, ratio de
  Sortino, Max Drawdown
- **Portefeuille global** : répartition du capital, contribution au risque par
  actif, matrice de corrélation entre ETF
- **Frontière efficiente** : simulation de portefeuilles aléatoires et calcul
  du portefeuille optimal (max Sharpe) par rapport au portefeuille actuel
- **Historique** : courbe de cours par ETF avec points d'achat, évolution de
  la valeur de chaque position dans le temps

## Architecture

- `new_code.py` — chargement des transactions, récupération des cours
  historiques (yfinance) et calcul de tous les indicateurs. Un seul
  dictionnaire de configuration (`ETFS`) pilote l'ensemble : ajouter un ETF
  suivi ne nécessite de modifier que cette entrée, rien d'autre dans le
  reste du code.
- `new_dashboard.py` — interface Streamlit, entièrement générée à partir de
  cette même configuration (aucun ETF n'est codé en dur côté interface).

## Stack technique

Python · Streamlit · pandas · numpy · yfinance · scipy · plotly

## Lancer en local

```bash
cd code_PEA
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
streamlit run new_dashboard.py
```

Par défaut, l'application utilise le fichier de démo anonymisé
(`code_PEA/data/extraction_demo.xlsx`). Pour utiliser son propre export PEA,
définir la variable d'environnement `PEA_EXCEL_PATH` vers son fichier avant
de lancer Streamlit :

```bash
set PEA_EXCEL_PATH=chemin\vers\mon_export.xlsx   # Windows (cmd)
streamlit run new_dashboard.py
```

## À propos des données de démo

Le fichier `code_PEA/data/extraction_demo.xlsx` est une version anonymisée
d'un vrai historique de transactions PEA : les ETF suivis et les dates
d'opération sont réels, mais les quantités et les montants investis ont été
randomisés (et volontairement amplifiés) pour ne représenter aucun
portefeuille réel plausible. Les cours affichés restent les prix de marché
réels de chaque ETF, afin que les graphiques restent cohérents.
