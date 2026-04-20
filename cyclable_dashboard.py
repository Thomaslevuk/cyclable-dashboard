"""
Cyclable — Dashboard FY26
Sources : Google Sheets (ONE PAGE) + Shopify (sell-in B2B)
Déploiement : Streamlit Cloud — lien partageable + mot de passe
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
SHEET_ID          = "1EZdvK-6u0yDtpw-xJUlqqQ1heScSFdDPLVoBJvO5TSI"
SHEET_GID         = "1665770308"
SHOPIFY_SHOP      = "elwing-boards.myshopify.com"
SHOPIFY_API_VER   = "2024-01"

MONTHS = ["Oct 25","Nov 25","Déc 25","Jan 26","Fév 26","Mar 26",
          "Avr 26","Mai 26","Jun 26","Jul 26","Aoû 26","Sep 26"]
CUR = 6  # Avril 2026 (index 0 = Oct 25)

REP_COLORS  = {"Caroline": "#ec4899", "Thomas": "#3b82f6", "Tanguy": "#f59e0b"}
TYPE_COLORS = {"Filiale": "#3b82f6", "Franchisé": "#f59e0b"}

st.set_page_config(
    page_title="Cyclable · Dashboard FY26",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  [data-testid="stMetric"] {
    background: #fff; border-radius: 12px; padding: 16px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,.07);
  }
  [data-testid="stMetricLabel"] {
    font-size: .75rem !important; font-weight: 700 !important;
    text-transform: uppercase; letter-spacing: .5px;
  }
  [data-testid="stMetricValue"] {
    font-size: 1.9rem !important; font-weight: 800 !important;
  }
  .block-container { padding-top: 1.5rem; }
  h2 { color: #1a7a3c; border-bottom: 2px solid #28a84f; padding-bottom: 6px; }
  h3 { color: #1e2a38; font-size: 1rem; margin-bottom: 4px; }
  .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: .88rem; }
  .stTabs [aria-selected="true"] { color: #1a7a3c; border-bottom-color: #1a7a3c; }
  div[data-testid="stButton"] button[kind="primary"] {
    background-color: #1a7a3c; border: none;
  }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def login_page():
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🚲 Cyclable Dashboard FY26")
        st.markdown("Tableau de bord réservé — Accès Cyclable × Elwing.")
        st.divider()
        pwd = st.text_input("Mot de passe", type="password", placeholder="••••••••••")
        if st.button("Se connecter", use_container_width=True, type="primary"):
            correct = st.secrets.get("password", "Ritmic26")
            if pwd == correct:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")

if not st.session_state.get("auth"):
    login_page()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# DONNÉES STATIQUES (fallback si Google Sheets non partagé)
# ══════════════════════════════════════════════════════════════════════════════
def get_static_data() -> pd.DataFrame:
    stores_raw = [
        ("Cyclable Bordeaux",              "Tanguy",   "Filiale",   13801, 7, 40,  -33, 4, 4,  7,  44.837, -0.579, "2026-02-19"),
        ("Cyclable Le Havre",              "Caroline", "Franchisé",  7800, 4, 40,  -36, 5, 4,  4,  49.494,  0.108, None),
        ("Cyclable Lyon 6",                "Thomas",   "Filiale",    6905, 3, 30,  -27, 4, 2,  3,  45.764,  4.834, "2026-02-27"),
        ("Cyclable Paris 13",              "Caroline", "Filiale",    9662, 4, 40,  -36, 4, 2,  4,  48.831,  2.362, "2026-02-23"),
        ("Cyclable Nantes Beaujoire",      "Tanguy",   "Filiale",    4914, 1, 15,  -14, 1, 0,  1,  47.218, -1.534, "2026-02-17"),
        ("Cyclable Paris 19",              "Caroline", "Filiale",    3041, 0, 20,  -20, None, 0, 0, 48.885,  2.387, None),
        ("Cyclable Paris 14",              "Caroline", "Filiale",    3009, 0, 30,  -30, None, 0, 0, 48.828,  2.323, None),
        ("Cyclable Poitiers",              "Tanguy",   "Filiale",    4857, 2, 10,   -8, 4, 0,  2,  46.580,  0.340, "2026-02-18"),
        ("Cyclable Castelnau",             "Thomas",   "Filiale",    6722, 2, 10,   -8, 4, 0,  2,  43.622,  3.908, "2026-03-04"),
        ("Cyclable Rennes-Montgermont",    "Tanguy",   "Filiale",    3021, 0, 15,  -15, 2, 1,  0,  48.117, -1.678, "2026-02-13"),
        ("Cyclable Clermont",              "Thomas",   "Filiale",    3021, 0, 15,  -15, 1, 2,  0,  45.780,  3.086, "2026-02-17"),
        ("Cyclable Strasbourg Étoile",     "Thomas",   "Filiale",    3021, 0, 20,  -20, 2, 1,  0,  48.573,  7.752, "2026-02-24"),
        ("Cyclable Lyon 7",                "Thomas",   "Filiale",    3021, 0, 30,  -30, 4, 5,  0,  45.748,  4.831, "2026-02-27"),
        ("Cyclable Champagne",             "Thomas",   "Filiale",    3021, 0, 15,  -15, 3, 0,  0,  49.258,  4.031, "2026-02-17"),
        ("Cyclable Paris 17",              "Caroline", "Filiale",    3021, 0, 40,  -40, 4, 6,  0,  48.884,  2.311, "2026-02-12"),
        ("Cyclable Issy-Les-Moulineaux",   "Caroline", "Filiale",    3021, 0, 25,  -25, 3, 0,  0,  48.823,  2.270, "2026-02-11"),
        ("Cyclable Nancy",                 "Thomas",   "Franchisé",  1521, 0,  8,   -8, 4, 2,  0,  48.692,  6.184, "2026-02-25"),
        ("Cyclable Avignon",               "Thomas",   "Franchisé",  3443, 1, 10,   -9, 3, 1,  1,  43.949,  4.806, "2026-03-04"),
        ("Cyclable Dijon",                 "Thomas",   "Filiale",    1324, 0,  8,   -8, 3, 0,  0,  47.322,  5.041, "2026-02-18"),
        ("Cyclable Montpellier Centre",    "Thomas",   "Filiale",    1324, 0, 15,  -15, 4, 0,  0,  43.611,  3.877, "2026-03-04"),
        ("Cyclable Orléans",               "Caroline", "Filiale",    1324, 0, 10,  -10, 4, 0,  0,  47.903,  1.909, "2026-02-26"),
        ("Cyclable Lille Centre",          "Caroline", "Filiale",    1324, 0, 15,  -15, 3, 1,  0,  50.629,  3.057, "2026-03-12"),
        ("Cyclable Caen",                  "Caroline", "Filiale",    1308, 0,  5,   -5, 3, 0,  0,  49.183, -0.371, "2026-02-24"),
        ("Cyclable Royan",                 "Tanguy",   "Franchisé",     0, 0, 10,  -10, 4, 0,  0,  45.624, -1.029, None),
        ("Cyclable Saint-Étienne",         "Thomas",   "Franchisé",     0, 0,  5,   -5, 2, 2,  0,  45.440,  4.387, None),
        ("Cyclable Valence",               "Thomas",   "Franchisé",     0, 0,  3,   -3, 2, 0,  0,  44.933,  4.892, None),
        ("Cyclable Marseille",             "Thomas",   "Filiale",    1714, 0, 20,  -20, 5, 0,  0,  43.296,  5.370, None),
        ("Cyclable Mulhouse",              "Thomas",   "Franchisé",     0, 0,  5,   -5, 5, 0,  0,  47.751,  7.336, "2026-02-25"),
    ]
    df = pd.DataFrame(stores_raw, columns=[
        "Magasin", "Rep", "Type", "CA", "Vélos", "Objectif", "Gap",
        "Confiance", "Essais", "Ventes", "Lat", "Lng", "Formation"
    ])
    df["Conversion"] = df.apply(
        lambda r: round(r.Ventes / r.Essais * 100) if r.Essais > 0 else 0, axis=1
    )
    df["Magasin_court"] = df["Magasin"].str.replace("Cyclable ", "", regex=False)
    return df

# ══════════════════════════════════════════════════════════════════════════════
# DONNÉES MENSUELLES (Essais & Ventes par magasin)
# ══════════════════════════════════════════════════════════════════════════════
MONTHLY_E = {
    "Cyclable Bordeaux":           [0, 0, 0, 0, 2, 2, None, None, None, None, None, None],
    "Cyclable Le Havre":           [0, 0, 0, 0, 2, 2, None, None, None, None, None, None],
    "Cyclable Lyon 6":             [0, 0, 0, 0, 1, 1, None, None, None, None, None, None],
    "Cyclable Paris 13":           [0, 0, 0, 0, 1, 1, None, None, None, None, None, None],
    "Cyclable Paris 17":           [0, 0, 0, 0, 3, 3, None, None, None, None, None, None],
    "Cyclable Lyon 7":             [0, 0, 0, 0, 2, 3, None, None, None, None, None, None],
    "Cyclable Clermont":           [0, 0, 0, 0, 2, 0, None, None, None, None, None, None],
    "Cyclable Strasbourg Étoile":  [0, 0, 0, 0, 1, 0, None, None, None, None, None, None],
    "Cyclable Nancy":              [0, 0, 0, 0, 1, 1, None, None, None, None, None, None],
    "Cyclable Saint-Étienne":      [0, 0, 0, 0, 0, 2, None, None, None, None, None, None],
    "Cyclable Avignon":            [0, 0, 0, 0, 0, 1, None, None, None, None, None, None],
    "Cyclable Rennes-Montgermont": [0, 0, 0, 0, 0, 1, None, None, None, None, None, None],
    "Cyclable Lille Centre":       [0, 0, 0, 0, 0, 1, None, None, None, None, None, None],
}
MONTHLY_V = {
    "Cyclable Bordeaux":          [0, 0, 0, 0, 4, 3, None, None, None, None, None, None],
    "Cyclable Le Havre":          [0, 0, 0, 0, 2, 2, None, None, None, None, None, None],
    "Cyclable Lyon 6":            [0, 0, 0, 0, 1, 2, None, None, None, None, None, None],
    "Cyclable Paris 13":          [0, 0, 0, 0, 2, 2, None, None, None, None, None, None],
    "Cyclable Castelnau":         [0, 0, 0, 0, 1, 1, None, None, None, None, None, None],
    "Cyclable Poitiers":          [0, 0, 0, 0, 1, 1, None, None, None, None, None, None],
    "Cyclable Nantes Beaujoire":  [0, 0, 0, 0, 1, 0, None, None, None, None, None, None],
    "Cyclable Avignon":           [0, 0, 0, 0, 0, 1, None, None, None, None, None, None],
}

# ══════════════════════════════════════════════════════════════════════════════
# GPS — coordonnées par magasin (non présentes dans le sheet)
# ══════════════════════════════════════════════════════════════════════════════
GPS_LOOKUP = {
    "Cyclable Bordeaux":            (44.837, -0.579),
    "Cyclable Le Havre":            (49.494,  0.108),
    "Cyclable Lyon 6":              (45.764,  4.834),
    "Cyclable Paris 13":            (48.831,  2.362),
    "Cyclable Nantes Beaujoire":    (47.218, -1.534),
    "Cyclable Paris 19":            (48.885,  2.387),
    "Cyclable Paris 14":            (48.828,  2.323),
    "Cyclable Poitiers":            (46.580,  0.340),
    "Cyclable Castelnau":           (43.622,  3.908),
    "Cyclable Rennes-Montgermont":  (48.117, -1.678),
    "Cyclable Clermont":            (45.780,  3.086),
    "Cyclable Strasbourg Étoile":   (48.573,  7.752),
    "Cyclable Lyon 7":              (45.748,  4.831),
    "Cyclable Champagne":           (49.258,  4.031),
    "Cyclable Paris 17":            (48.884,  2.311),
    "Cyclable Issy-Les-Moulineaux": (48.823,  2.270),
    "Cyclable Nancy":               (48.692,  6.184),
    "Cyclable Avignon":             (43.949,  4.806),
    "Cyclable Dijon":               (47.322,  5.041),
    "Cyclable Montpellier Centre":  (43.611,  3.877),
    "Cyclable Orléans":             (47.903,  1.909),
    "Cyclable Lille Centre":        (50.629,  3.057),
    "Cyclable Caen":                (49.183, -0.371),
    "Cyclable Royan":               (45.624, -1.029),
    "Cyclable Saint-Étienne":       (45.440,  4.387),
    "Cyclable Valence":             (44.933,  4.892),
    "Cyclable Marseille":           (43.296,  5.370),
    "Cyclable Mulhouse":            (47.751,  7.336),
}

# Colonnes mensuelles dans le sheet (0-indexed, positionnelles)
# Structure réelle : colonnes décalées d'1 par rapport aux en-têtes
# Col 0=Magasin, 1=Rep, 2=Confiance, 6=Type, 8=Formation, 9=Vélos,
# 14=CA HT, 15=Objectif, 16=Gap(VS réel)
# Cols 17,18 = Oct25 Obj/Act ; 19,20 = Nov25 ; 21,22 = Déc25
# 23,24 = Jan26 ; 25,26 = Fév26 ; 27,28 = Mar26
# 29,30 = Avr26 ; 31,32 = Mai26
MONTH_OBJ_COLS = [17, 19, 21, 23, 25, 27, 29, 31]
MONTH_ACT_COLS = [18, 20, 22, 24, 26, 28, 30, 32]


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT — GOOGLE SHEETS (lecture CSV public)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600 * 4, show_spinner="Chargement ONE PAGE Google Sheets…")
def load_google_sheet():
    """
    Lit la feuille Google Sheets en CSV public.
    Partager : Partager > Toute personne disposant du lien > Lecteur.
    """
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/export?format=csv&gid={SHEET_GID}"
    )
    try:
        df = pd.read_csv(url, header=0, on_bad_lines="skip")
        return df, True
    except Exception:
        return None, False


def _clean_num(series: pd.Series) -> pd.Series:
    """Nettoie une colonne de valeurs numériques (€, espaces, virgules…)."""
    return pd.to_numeric(
        series.astype(str)
              .str.replace(r"[\u00a0\s€]", "", regex=True)
              .str.replace(",", ".", regex=False)
              .str.replace(r"[^\d.\-]", "", regex=True),
        errors="coerce",
    ).fillna(0)


def map_sheet_to_df(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Mapping positionnel du Google Sheet ONE PAGE vers le DataFrame du dashboard.
    Structure réelle du sheet (colonnes décalées d'1 par rapport aux en-têtes) :
      col 0  → Magasin       col 1  → Rep         col 2  → Confiance
      col 6  → Type          col 8  → Formation    col 9  → Vélos (sell-out YTD)
      col 14 → CA HT (€)     col 15 → Objectif     col 16 → Gap (VS réel)
    """
    if raw.shape[1] < 17:
        return None

    df = pd.DataFrame()
    df["Magasin"]   = raw.iloc[:, 0].astype(str).str.strip()
    df["Rep"]       = raw.iloc[:, 1].astype(str).str.strip()
    df["Confiance"] = _clean_num(raw.iloc[:, 2])
    df["Type"]      = raw.iloc[:, 6].astype(str).str.strip()
    df["Formation"] = raw.iloc[:, 8].astype(str).str.strip()
    df["Vélos"]     = _clean_num(raw.iloc[:, 9])
    df["CA"]        = _clean_num(raw.iloc[:, 14])
    df["Objectif"]  = _clean_num(raw.iloc[:, 15])
    df["Gap"]       = _clean_num(raw.iloc[:, 16])

    # Essais non disponibles dans cet onglet → 0
    df["Essais"]    = 0
    df["Ventes"]    = df["Vélos"]   # Ventes sell-out = Vélos

    # GPS depuis le lookup statique
    df["Lat"] = df["Magasin"].map(lambda n: GPS_LOOKUP.get(n, (46.5, 2.5))[0])
    df["Lng"] = df["Magasin"].map(lambda n: GPS_LOOKUP.get(n, (46.5, 2.5))[1])

    # Filtrer les lignes non valides (totaux, en-têtes parasites)
    df = df[df["Magasin"].str.len() > 3].copy()
    df = df[~df["Magasin"].str.lower().str.contains(
        r"^nan$|total|magasin|store|reps|---", na=True
    )].copy()

    if df.empty:
        return None

    df["Conversion"]    = df.apply(
        lambda r: round(r["Ventes"] / r["Essais"] * 100) if r["Essais"] > 0 else 0, axis=1
    )
    df["Magasin_court"] = df["Magasin"].str.replace("Cyclable ", "", regex=False)
    return df.reset_index(drop=True)


def extract_monthly_ventes(raw: pd.DataFrame) -> dict:
    """
    Extrait les ventes mensuelles (Actuals sell-out) par magasin depuis le sheet.
    Retourne un dict {Magasin: [v_oct, v_nov, ..., v_sep]} (12 valeurs, None si futur).
    """
    monthly = {}
    for _, row in raw.iterrows():
        magasin = str(row.iloc[0]).strip()
        if len(magasin) < 3 or magasin.lower() in ("nan", "total", "reps", "magasin"):
            continue
        vals = []
        for col_idx in MONTH_ACT_COLS:
            if col_idx < len(row):
                v = _clean_num(pd.Series([row.iloc[col_idx]])).iloc[0]
                vals.append(int(v) if v > 0 else None)
            else:
                vals.append(None)
        # Pad à 12 mois (Oct → Sep) — les mois après Mai restent None
        vals_12 = vals + [None] * (12 - len(vals))
        monthly[magasin] = vals_12
    return monthly


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT — SHOPIFY
# ══════════════════════════════════════════════════════════════════════════════
def get_shopify_token() -> str:
    client_id     = st.secrets.get("shopify_client_id", "")
    client_secret = st.secrets.get("shopify_client_secret", "")
    if not client_id or not client_secret:
        return ""
    try:
        r = requests.post(
            f"https://{SHOPIFY_SHOP}/admin/oauth/access_token",
            json={"client_id": client_id, "client_secret": client_secret,
                  "grant_type": "client_credentials"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("access_token", "")
    except Exception:
        return ""


@st.cache_data(ttl=3600 * 8, show_spinner="Chargement Shopify…")
def load_shopify_orders() -> pd.DataFrame:
    token = get_shopify_token()
    if not token:
        return pd.DataFrame()

    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    all_orders = []
    url = (
        f"https://{SHOPIFY_SHOP}/admin/api/{SHOPIFY_API_VER}"
        "/orders.json?limit=250&status=any"
    )
    while url:
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            all_orders.extend(r.json().get("orders", []))
            url = None
            for part in r.headers.get("Link", "").split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip().strip("<>")
        except Exception as e:
            st.warning(f"Shopify : {e}")
            break

    if not all_orders:
        return pd.DataFrame()

    rows = []
    for o in all_orders:
        company = ""
        if o.get("company"):
            company = o["company"].get("name", "")
        if not company:
            company = (o.get("billing_address") or {}).get("company", "")
        if not company:
            addrs = (o.get("customer") or {}).get("addresses") or []
            company = addrs[0].get("company", "") if addrs else ""

        rows.append({
            "store_raw":  company.strip() or "Non identifié",
            "order_id":   o["id"],
            "order_name": o.get("name", ""),
            "created_at": o.get("created_at", ""),
            "ca":         float(o.get("total_price") or 0),
            "currency":   o.get("currency", "EUR"),
            "nb_items":   sum(int(i.get("quantity", 0)) for i in o.get("line_items", [])),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce").dt.tz_localize(None)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DES DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
raw_sheet, sheet_ok = load_google_sheet()
df_orders = load_shopify_orders()

# Données ONE PAGE (Google Sheets ou statique)
df_all = None
monthly_v_live = {}   # Ventes mensuelles depuis le sheet

if sheet_ok and raw_sheet is not None:
    df_all         = map_sheet_to_df(raw_sheet)
    monthly_v_live = extract_monthly_ventes(raw_sheet)

if df_all is None or df_all.empty:
    df_all     = get_static_data()
    sheet_ok   = False

# Ventes mensuelles : live si disponible, sinon données statiques
MONTHLY_V_ACTIVE = monthly_v_live if monthly_v_live else MONTHLY_V

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🚲 Cyclable FY26")
    st.markdown("**Filtres**")
    st.divider()

    reps  = ["Tous"] + sorted(df_all["Rep"].dropna().unique().tolist())
    types = ["Tous"] + sorted(df_all["Type"].dropna().unique().tolist())

    sel_rep  = st.selectbox("👤 Commercial", reps)
    sel_type = st.selectbox("🏢 Type", types)
    search   = st.text_input("🔍 Rechercher", placeholder="ex: Bordeaux, Paris…")

    st.divider()

    if st.button("🔄 Rafraîchir les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    orders_ok = not df_orders.empty
    st.markdown(
        f"- ONE PAGE Sheets : {'✅ live' if sheet_ok else '⚠️ données locales'}\n"
        f"- Shopify : {'✅ connecté' if orders_ok else '⚠️ non connecté'}"
    )
    st.caption(f"Mis à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.divider()

    if st.button("Déconnexion", use_container_width=True):
        st.session_state["auth"] = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FILTRAGE
# ══════════════════════════════════════════════════════════════════════════════
df = df_all.copy()
if sel_rep  != "Tous": df = df[df["Rep"]  == sel_rep]
if sel_type != "Tous": df = df[df["Type"] == sel_type]
if search:             df = df[df["Magasin"].str.lower().str.contains(search.lower(), na=False)]

if sel_rep != "Tous" or sel_type != "Tous" or search:
    st.sidebar.info(f"🔎 {len(df)} / {len(df_all)} magasins affichés")

# ══════════════════════════════════════════════════════════════════════════════
# ALERTE SHEET NON PUBLIC
# ══════════════════════════════════════════════════════════════════════════════
if not sheet_ok:
    st.warning(
        "⚠️ **Données locales** — Le Google Sheet n'est pas encore partagé en public. "
        "Pour activer les données live : **Partager → Toute personne disposant du lien → Lecteur**, "
        "puis cliquer sur **Rafraîchir**."
    )

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    st.markdown("# 🚲 Cyclable — Dashboard FY26")
    src = "Google Sheets live" if sheet_ok else "données locales"
    st.caption(f"ONE PAGE B2C-B2B FY26 · Source : {src} · {datetime.now().strftime('%d %B %Y')}")
with col_h2:
    st.markdown("### `FY26 · Avr 2026`")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📊 Tableau Général",
    "🔬 Essais & Ventes",
    "📅 Février 2026",
    "📅 Mars 2026",
    "📅 Avril 2026",
    "🗺️ Carte",
    "📈 Suivi Mensuel",
    "🛒 Shopify",
])


# ═══════════════════════════════════════════════════════════════════
# TAB 1 — TABLEAU GÉNÉRAL
# ═══════════════════════════════════════════════════════════════════
with tabs[0]:
    ca_total   = df["CA"].sum()
    velos_tot  = df["Vélos"].sum()
    obj_tot    = df["Objectif"].replace(0, float("nan")).dropna().sum()
    gap_tot    = velos_tot - obj_tot
    essais_tot = df["Essais"].sum()
    ventes_tot = df["Ventes"].sum()
    conv_tot   = round(ventes_tot / essais_tot * 100, 1) if essais_tot > 0 else 0.0
    att_pct    = round(velos_tot / obj_tot * 100, 1) if obj_tot > 0 else 0.0

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("CA HT Total",       f"{ca_total:,.0f} €".replace(",", " "))
    k2.metric("Vélos Sell-out",    f"{int(velos_tot)} 🚲", f"Obj FY26 : {int(obj_tot)}")
    k3.metric("Atteinte Objectif", f"{att_pct} %",         f"{int(velos_tot)} / {int(obj_tot)} vélos")
    k4.metric("Gap vs Objectif",   f"−{int(abs(gap_tot))}", "vélos restants")
    k5.metric("Essais Total",      f"{int(essais_tot)}",   f"Conv. {conv_tot} %")
    k6.metric("Nb Magasins",       f"{len(df)}",
              f"{len(df[df.Type=='Filiale'])} fil. · {len(df[df.Type=='Franchisé'])} franch.")

    st.markdown("---")

    # Filiale vs Franchisé
    st.markdown("## 🏢 Filiales vs Franchisés")
    col_f, col_fr = st.columns(2)

    def vs_block(sub_df, label):
        ca  = sub_df["CA"].sum()
        vel = sub_df["Vélos"].sum()
        ob  = sub_df["Objectif"].replace(0, float("nan")).dropna().sum() or 0
        es  = sub_df["Essais"].sum()
        vt  = sub_df["Ventes"].sum()
        cv  = round(vt / es * 100, 1) if es > 0 else 0
        at  = round(vel / ob * 100, 1) if ob > 0 else 0
        st.markdown(f"**{label}** — {len(sub_df)} magasins")
        m1, m2, m3 = st.columns(3)
        m1.metric("CA HT",          f"{ca:,.0f} €".replace(",", " "))
        m2.metric("Vélos sell-out",  int(vel))
        m3.metric("Atteinte",        f"{at} %")
        n1, n2, n3 = st.columns(3)
        n1.metric("Essais démo",     int(es))
        n2.metric("Taux conv.",      f"{cv} %")
        n3.metric("Gap",             f"−{int(abs(vel - ob))}")

    with col_f:
        with st.container(border=True):
            vs_block(df[df["Type"] == "Filiale"], "🔵 Filiales")
    with col_fr:
        with st.container(border=True):
            vs_block(df[df["Type"] == "Franchisé"], "🟡 Franchisés")

    st.markdown("---")

    # Graphiques
    st.markdown("## 📊 Graphiques")
    ch1, ch2 = st.columns(2)

    with ch1:
        top10 = df.nlargest(10, "CA")
        fig_ca = px.bar(
            top10, x="Magasin_court", y="CA",
            color="Rep", color_discrete_map=REP_COLORS,
            title="🏆 Top Magasins — CA HT (€)", text="CA",
        )
        fig_ca.update_traces(texttemplate="%{y:,.0f}€", textposition="outside")
        fig_ca.update_layout(showlegend=True, height=350, xaxis_tickangle=-30,
                             plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_ca, use_container_width=True)

    with ch2:
        rep_data = df.groupby("Rep").agg(
            Objectif=("Objectif", "sum"), Vélos=("Vélos", "sum")
        ).reset_index()
        fig_vel = go.Figure()
        fig_vel.add_trace(go.Bar(
            name="Objectif", x=rep_data["Rep"], y=rep_data["Objectif"],
            marker_color=[REP_COLORS.get(r, "#94a3b8") for r in rep_data["Rep"]],
            opacity=0.25,
        ))
        fig_vel.add_trace(go.Bar(
            name="Vendus", x=rep_data["Rep"], y=rep_data["Vélos"],
            marker_color=[REP_COLORS.get(r, "#94a3b8") for r in rep_data["Rep"]],
            text=rep_data["Vélos"].astype(str) + " 🚲", textposition="outside",
        ))
        fig_vel.update_layout(
            title="🚲 Vélos Sell-out vs Objectif par Commercial",
            barmode="group", height=350, plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig_vel, use_container_width=True)

    st.markdown("---")

    # Performance par commercial
    st.markdown("## 👤 Performance par Commercial")
    rep_cols = st.columns(df["Rep"].nunique() or 1)
    for i, (rep, grp) in enumerate(df.groupby("Rep")):
        with rep_cols[i % len(rep_cols)]:
            with st.container(border=True):
                st.markdown(f"**{rep}** · {len(grp)} magasins")
                r1, r2 = st.columns(2)
                r1.metric("CA HT",     f"{grp['CA'].sum():,.0f} €".replace(",", " "))
                r2.metric("Vélos 🚲",  int(grp["Vélos"].sum()))
                r3, r4 = st.columns(2)
                ob_ = grp["Objectif"].replace(0, float("nan")).dropna().sum() or 0
                r3.metric("Objectif",  int(ob_))
                att = round(grp["Vélos"].sum() / ob_ * 100, 1) if ob_ > 0 else 0
                r4.metric("Atteinte",  f"{att} %")

    st.markdown("---")

    # Table
    st.markdown("## 🏪 Détail par Magasin")
    display_df = df[[
        "Magasin", "Rep", "Type", "CA", "Vélos", "Objectif", "Gap",
        "Confiance", "Essais", "Ventes", "Conversion"
    ]].copy()
    display_df["CA"]         = display_df["CA"].apply(lambda x: f"{x:,.0f} €".replace(",", " "))
    display_df["Conversion"] = display_df["Conversion"].apply(lambda x: f"{x}%" if x > 0 else "—")
    display_df["Confiance"]  = display_df["Confiance"].apply(
        lambda x: "⭐" * int(x) if pd.notna(x) and x > 0 else "—"
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True,
                 column_config={
                     "Vélos": st.column_config.NumberColumn("Vélos 🚲"),
                     "Gap":   st.column_config.NumberColumn("Gap", format="%d"),
                 })


# ═══════════════════════════════════════════════════════════════════
# TAB 2 — ESSAIS & VENTES
# ═══════════════════════════════════════════════════════════════════
with tabs[1]:
    e_tot = df["Essais"].sum()
    v_tot = df["Ventes"].sum()
    c_tot = round(v_tot / e_tot * 100, 1) if e_tot > 0 else 0

    fil = df[df["Type"] == "Filiale"];  fra = df[df["Type"] == "Franchisé"]
    fil_e = fil["Essais"].sum();  fil_v = fil["Ventes"].sum()
    fra_e = fra["Essais"].sum();  fra_v = fra["Ventes"].sum()

    ke1, ke2, ke3, ke4, ke5 = st.columns(5)
    ke1.metric("Total Essais",      int(e_tot))
    ke2.metric("Total Ventes",      f"{int(v_tot)} 🚲")
    ke3.metric("Taux Conv. Global", f"{c_tot} %", f"{int(v_tot)} / {int(e_tot)} essais")
    ke4.metric("Filiale",           f"{round(fil_v/fil_e*100,1) if fil_e else 0} %",
               f"{int(fil_e)}E → {int(fil_v)}V")
    ke5.metric("Franchisé",         f"{round(fra_v/fra_e*100,1) if fra_e else 0} %",
               f"{int(fra_e)}E → {int(fra_v)}V")

    st.markdown("---")

    st.markdown("## 👤 Synthèse par Commercial")
    rep_agg = df.groupby("Rep").agg(
        Essais=("Essais", "sum"), Ventes=("Ventes", "sum")
    ).reset_index()
    rep_agg["Conv"] = (rep_agg["Ventes"] / rep_agg["Essais"] * 100).round(1).fillna(0)

    rc1, rc2 = st.columns(2)
    with rc1:
        fig_ev = go.Figure()
        fig_ev.add_trace(go.Bar(
            name="Essais", x=rep_agg["Rep"], y=rep_agg["Essais"],
            marker_color=[REP_COLORS.get(r, "#94a3b8") for r in rep_agg["Rep"]],
            opacity=0.4, text=rep_agg["Essais"], textposition="outside",
        ))
        fig_ev.add_trace(go.Bar(
            name="Ventes", x=rep_agg["Rep"], y=rep_agg["Ventes"],
            marker_color=[REP_COLORS.get(r, "#94a3b8") for r in rep_agg["Rep"]],
            text=rep_agg["Ventes"].astype(str) + "🚲", textposition="outside",
        ))
        fig_ev.update_layout(title="📊 Essais vs Ventes par Commercial",
                             barmode="group", height=320,
                             plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_ev, use_container_width=True)

    with rc2:
        fig_conv = px.bar(
            rep_agg, x="Conv", y="Rep", orientation="h",
            color="Rep", color_discrete_map=REP_COLORS,
            text="Conv", title="🎯 Taux de Conversion (%)",
        )
        fig_conv.update_traces(texttemplate="%{x}%", textposition="outside")
        fig_conv.update_layout(showlegend=False, height=320,
                               plot_bgcolor="white", paper_bgcolor="white",
                               xaxis=dict(range=[0, 120]))
        st.plotly_chart(fig_conv, use_container_width=True)

    st.markdown("---")
    st.markdown("## 🏪 Essais & Ventes par Magasin")
    ev_df = df[df["Essais"] > 0].sort_values("Essais", ascending=False)
    if not ev_df.empty:
        fig_top_e = px.bar(
            ev_df, x="Magasin_court", y="Essais",
            color="Rep", color_discrete_map=REP_COLORS,
            text="Essais", title="Top Magasins — Essais",
        )
        fig_top_e.update_traces(textposition="outside")
        fig_top_e.update_layout(height=300, plot_bgcolor="white",
                                paper_bgcolor="white", xaxis_tickangle=-30)
        st.plotly_chart(fig_top_e, use_container_width=True)

    ess_display = df[["Magasin", "Type", "Rep", "Essais", "Ventes", "Conversion"]].copy()
    ess_display["Conversion"] = ess_display["Conversion"].apply(lambda x: f"{x}%" if x > 0 else "—")
    st.dataframe(ess_display.sort_values("Essais", ascending=False),
                 use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 3 — FÉVRIER 2026
# ═══════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("## 📅 Février 2026 — 11 magasins actifs")
    st.caption("Données cumulées YTD · magasins onboardés en janvier–février")

    kf1, kf2, kf3, kf4 = st.columns(4)
    kf1.metric("Vélos Vendus",    "8 🚲", "Février 2026")
    kf2.metric("Essais Réalisés", "14",   "tests effectués")
    kf3.metric("Taux Conversion", "57 %", "8 / 14 essais")
    kf4.metric("CA HT Estimé",   "~51 k€", "magasins actifs Fév")

    st.markdown("---")
    c1, c2 = st.columns(2)

    fev_velos  = pd.DataFrame({
        "Magasin": ["Bordeaux", "Le Havre", "Lyon 6", "Paris 13", "Nantes", "Poitiers"],
        "Vélos":   [4, 1, 1, 1, 1, 1],
    })
    fev_essais = pd.DataFrame({
        "Magasin": ["Paris 17", "Le Havre", "Lyon 7", "Clermont", "Lyon 6", "Paris 13"],
        "Essais":  [3, 2, 2, 2, 1, 1],
    })

    with c1:
        fig = px.bar(fev_velos, x="Magasin", y="Vélos", text="Vélos",
                     title="🚲 Vélos Vendus — Février",
                     color_discrete_sequence=["#6366f1"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(fev_essais, x="Magasin", y="Essais", text="Essais",
                     title="🔬 Essais Réalisés — Février",
                     color_discrete_sequence=["rgba(99,102,241,.65)"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    fev_detail = pd.DataFrame([
        {"Magasin": "Bordeaux", "Rep": "Tanguy", "Essais Fév": 2, "Ventes Fév": 4},
        {"Magasin": "Le Havre", "Rep": "Caroline", "Essais Fév": 2, "Ventes Fév": 1},
        {"Magasin": "Lyon 6", "Rep": "Thomas", "Essais Fév": 1, "Ventes Fév": 1},
        {"Magasin": "Paris 13", "Rep": "Caroline", "Essais Fév": 1, "Ventes Fév": 2},
        {"Magasin": "Paris 17", "Rep": "Caroline", "Essais Fév": 3, "Ventes Fév": 0},
        {"Magasin": "Lyon 7", "Rep": "Thomas", "Essais Fév": 2, "Ventes Fév": 0},
        {"Magasin": "Nantes Beaujoire", "Rep": "Tanguy", "Essais Fév": 0, "Ventes Fév": 1},
        {"Magasin": "Poitiers", "Rep": "Tanguy", "Essais Fév": 0, "Ventes Fév": 1},
        {"Magasin": "Clermont", "Rep": "Thomas", "Essais Fév": 2, "Ventes Fév": 0},
        {"Magasin": "Strasbourg Étoile", "Rep": "Thomas", "Essais Fév": 1, "Ventes Fév": 0},
        {"Magasin": "Nancy", "Rep": "Thomas", "Essais Fév": 1, "Ventes Fév": 0},
    ])
    st.markdown("### 🏪 Détail Magasins — Février 2026")
    st.dataframe(fev_detail, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 4 — MARS 2026
# ═══════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("## 📅 Mars 2026 — 15 magasins actifs")
    st.caption("11 magasins actifs depuis Fév + 4 nouveaux onboardés en Mars")

    km1, km2, km3, km4 = st.columns(4)
    km1.metric("Vélos Vendus",    "9 🚲", "Mars (1–31)")
    km2.metric("Essais Réalisés", "16",   "tests effectués")
    km3.metric("Taux Conversion", "56 %", "9 / 16 essais")
    km4.metric("CA HT Estimé",   "~31 k€", "magasins actifs Mars")

    st.markdown("---")
    c1, c2 = st.columns(2)

    mar_velos  = pd.DataFrame({
        "Magasin": ["Bordeaux", "Le Havre", "Lyon 6", "Paris 13"],
        "Vélos":   [3, 2, 2, 1],
    })
    mar_essais = pd.DataFrame({
        "Magasin": ["Le Havre", "Paris 17", "Lyon 7", "Lyon 6", "Paris 13", "Avignon"],
        "Essais":  [2, 2, 2, 1, 1, 1],
    })

    with c1:
        fig = px.bar(mar_velos, x="Magasin", y="Vélos", text="Vélos",
                     title="🚲 Vélos Vendus — Mars",
                     color_discrete_sequence=["#22c55e"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(mar_essais, x="Magasin", y="Essais", text="Essais",
                     title="🔬 Essais Réalisés — Mars",
                     color_discrete_sequence=["rgba(40,168,79,.65)"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    mar_detail = pd.DataFrame([
        {"Magasin": "Bordeaux", "Rep": "Tanguy", "Essais Mar": 2, "Ventes Mar": 3},
        {"Magasin": "Le Havre", "Rep": "Caroline", "Essais Mar": 2, "Ventes Mar": 2},
        {"Magasin": "Lyon 6", "Rep": "Thomas", "Essais Mar": 1, "Ventes Mar": 2},
        {"Magasin": "Paris 13", "Rep": "Caroline", "Essais Mar": 1, "Ventes Mar": 1},
        {"Magasin": "Castelnau", "Rep": "Thomas", "Essais Mar": 0, "Ventes Mar": 1},
        {"Magasin": "Poitiers", "Rep": "Tanguy", "Essais Mar": 0, "Ventes Mar": 1},
        {"Magasin": "Paris 17", "Rep": "Caroline", "Essais Mar": 3, "Ventes Mar": 0},
        {"Magasin": "Lyon 7", "Rep": "Thomas", "Essais Mar": 3, "Ventes Mar": 0},
        {"Magasin": "Avignon", "Rep": "Thomas", "Essais Mar": 1, "Ventes Mar": 1},
        {"Magasin": "Rennes-Montgermont", "Rep": "Tanguy", "Essais Mar": 1, "Ventes Mar": 0},
        {"Magasin": "Lille Centre", "Rep": "Caroline", "Essais Mar": 1, "Ventes Mar": 0},
        {"Magasin": "Saint-Étienne", "Rep": "Thomas", "Essais Mar": 2, "Ventes Mar": 0},
    ])
    st.markdown("### 🏪 Détail Magasins — Mars 2026")
    st.dataframe(mar_detail, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 5 — AVRIL 2026
# ═══════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("## 📅 Avril 2026 — Mois en cours")
    st.caption("Données en cours de collecte · Mise à jour automatique depuis Google Sheets")

    # KPIs April — calculés depuis df_all (live si sheet ok, sinon 0)
    avr_essais = df["Essais"].sum()   # Total YTD — adapte si tu as des colonnes par mois
    avr_ventes = df["Ventes"].sum()
    avr_ca     = df["CA"].sum()

    ka1, ka2, ka3, ka4 = st.columns(4)
    ka1.metric("Magasins Actifs",  f"{len(df[df['Vélos'] > 0])} 🏪")
    ka2.metric("Essais YTD",       f"{int(avr_essais)}", "cumulé FY26")
    ka3.metric("Ventes YTD",       f"{int(avr_ventes)} 🚲", "cumulé FY26")
    ka4.metric("CA HT YTD",        f"{avr_ca:,.0f} €".replace(",", " "), "cumulé FY26")

    st.markdown("---")

    # Progression vs objectif
    st.markdown("## 📈 Progression vs Objectif FY26")
    obj_total = df_all["Objectif"].replace(0, float("nan")).dropna().sum()
    vel_total = df_all["Vélos"].sum()
    pct_att   = round(vel_total / obj_total * 100, 1) if obj_total > 0 else 0

    prog_col1, prog_col2 = st.columns([2, 1])
    with prog_col1:
        fig_prog = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pct_att,
            delta={"reference": 100, "suffix": "%"},
            title={"text": "Atteinte Objectif FY26", "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#1a7a3c"},
                "steps": [
                    {"range": [0, 50], "color": "#fee2e2"},
                    {"range": [50, 75], "color": "#fef3c7"},
                    {"range": [75, 100], "color": "#dcfce7"},
                ],
                "threshold": {
                    "line": {"color": "#dc2626", "width": 4},
                    "thickness": 0.75,
                    "value": 100,
                },
            },
            number={"suffix": "%"},
        ))
        fig_prog.update_layout(height=280, margin=dict(t=40, b=10))
        st.plotly_chart(fig_prog, use_container_width=True)

    with prog_col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.metric("Vélos vendus", f"{int(vel_total)} 🚲")
        st.metric("Objectif FY26", f"{int(obj_total)} 🚲")
        st.metric("Restants", f"{int(obj_total - vel_total)} 🚲")

    st.markdown("---")

    # Top magasins actifs en Avril
    st.markdown("## 🏅 Classement Magasins — YTD Avril 2026")
    c1, c2 = st.columns(2)

    with c1:
        top_ca_avr = df[df["CA"] > 0].nlargest(10, "CA")
        fig = px.bar(
            top_ca_avr, x="Magasin_court", y="CA",
            color="Rep", color_discrete_map=REP_COLORS,
            text="CA", title="🏆 Top CA HT (€) — YTD",
        )
        fig.update_traces(texttemplate="%{y:,.0f}€", textposition="outside")
        fig.update_layout(height=340, plot_bgcolor="white", paper_bgcolor="white",
                          xaxis_tickangle=-30, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        top_vel_avr = df[df["Vélos"] > 0].sort_values("Vélos", ascending=True)
        fig = px.bar(
            top_vel_avr, x="Vélos", y="Magasin_court", orientation="h",
            color="Rep", color_discrete_map=REP_COLORS,
            text="Vélos", title="🚲 Vélos Vendus — YTD",
        )
        fig.update_traces(texttemplate="%{x} 🚲", textposition="outside")
        fig.update_layout(height=340, plot_bgcolor="white", paper_bgcolor="white",
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    if sheet_ok:
        st.success("✅ Données chargées depuis Google Sheets — rafraîchissement toutes les 4h")
    else:
        st.info("ℹ️ Pour voir les données Avril live, partagez le Google Sheet en public et cliquez Rafraîchir.")


# ═══════════════════════════════════════════════════════════════════
# TAB 6 — CARTE
# ═══════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("## 🗺️ Localisation des Magasins Cyclable")
    st.caption("Taille des cercles proportionnelle au CA HT · Couleur = commercial")

    map_df = df.copy()
    map_df["size"] = map_df["CA"].apply(lambda x: max(8, min(35, 8 + x / 600)))

    fig_map = px.scatter_mapbox(
        map_df,
        lat="Lat", lon="Lng",
        color="Rep", color_discrete_map=REP_COLORS,
        size="size",
        hover_name="Magasin",
        hover_data={"CA": True, "Vélos": True, "Essais": True,
                    "Lat": False, "Lng": False, "size": False},
        zoom=5, center={"lat": 46.5, "lon": 2.5},
        height=540,
        title="Magasins Cyclable — Performance FY26",
        symbol="Type",
    )
    fig_map.update_layout(
        mapbox_style="open-street-map",
        legend=dict(orientation="h", y=-0.05),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    st.plotly_chart(fig_map, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        region_map = {
            "Île-de-France":             ["Paris"],
            "Auvergne-Rhône-Alpes":      ["Lyon", "Clermont", "Valence", "Saint-Étienne"],
            "Nouvelle-Aquitaine":        ["Bordeaux", "Poitiers", "Royan"],
            "Normandie":                 ["Caen", "Havre"],
            "Bretagne/Pays-de-la-Loire": ["Nantes", "Rennes"],
            "Grand-Est":                 ["Strasbourg", "Nancy", "Mulhouse", "Champagne"],
            "Occitanie":                 ["Montpellier", "Castelnau", "Avignon"],
            "Autres":                    ["Dijon", "Orléans", "Lille", "Marseille", "Issy"],
        }
        region_ca = {}
        for region, keywords in region_map.items():
            mask = df["Magasin"].apply(lambda n: any(k in n for k in keywords))
            region_ca[region] = int(df[mask]["CA"].sum())
        region_ca = {k: v for k, v in region_ca.items() if v > 0}
        if region_ca:
            fig_reg = px.pie(
                names=list(region_ca.keys()), values=list(region_ca.values()),
                title="Répartition CA HT par Région", hole=0.35,
            )
            fig_reg.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_reg, use_container_width=True)

    with c2:
        villes_df = df[df["Vélos"] > 0].sort_values("Vélos", ascending=True)
        if not villes_df.empty:
            fig_v = px.bar(
                villes_df, x="Vélos", y="Magasin_court", orientation="h",
                color="Rep", color_discrete_map=REP_COLORS,
                text="Vélos", title="Vélos Sell-out par Magasin (actifs)",
            )
            fig_v.update_traces(texttemplate="%{x} 🚲", textposition="outside")
            fig_v.update_layout(height=350, plot_bgcolor="white", paper_bgcolor="white",
                                showlegend=False)
            st.plotly_chart(fig_v, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 7 — SUIVI MENSUEL
# ═══════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("## 📈 Suivi Annuel FY26 — Oct 25 → Sep 26")

    view = st.radio("Afficher :", ["Essais", "Ventes", "Conversion %"], horizontal=True)

    rows = []
    for _, s in df_all.iterrows():
        me = MONTHLY_E.get(s["Magasin"], [0] * 12)
        mv = MONTHLY_V_ACTIVE.get(s["Magasin"], [0] * 12)
        # Extend to 12 if shorter
        me = list(me) + [None] * (12 - len(me))
        mv = list(mv) + [None] * (12 - len(mv))

        row = {"Magasin": s["Magasin"], "Rep": s["Rep"]}
        ytd_e, ytd_v = 0, 0
        for i, m in enumerate(MONTHS):
            if i > CUR:
                row[m] = None
            else:
                e_val = (me[i] or 0) if me[i] is not None else 0
                v_val = (mv[i] or 0) if mv[i] is not None else 0
                ytd_e += e_val; ytd_v += v_val
                if view == "Essais":
                    row[m] = e_val
                elif view == "Ventes":
                    row[m] = v_val
                else:
                    row[m] = round(v_val / e_val * 100) if e_val > 0 else None
        row["Total YTD"] = (ytd_e if view == "Essais"
                            else ytd_v if view == "Ventes"
                            else round(ytd_v / ytd_e * 100) if ytd_e else None)
        rows.append(row)

    df_monthly = pd.DataFrame(rows)
    active_months = MONTHS[:CUR + 1]
    st.dataframe(
        df_monthly.set_index("Magasin"),
        use_container_width=True,
        column_config={m: st.column_config.NumberColumn(m, format="%d") for m in active_months},
    )

    st.markdown("---")

    glob_e = [
        sum((MONTHLY_E.get(s["Magasin"], [0]*12) or [0]*12)[i] or 0 for _, s in df_all.iterrows())
        for i in range(CUR + 1)
    ]
    glob_v = [
        sum((MONTHLY_V_ACTIVE.get(s["Magasin"], [0]*12) or [0]*12)[i] or 0 for _, s in df_all.iterrows())
        for i in range(CUR + 1)
    ]

    c1, c2 = st.columns(2)
    with c1:
        fig_m = go.Figure()
        fig_m.add_trace(go.Bar(x=active_months, y=glob_e, name="Essais",
                               marker_color="rgba(59,130,246,.55)",
                               text=glob_e, textposition="outside"))
        fig_m.add_trace(go.Bar(x=active_months, y=glob_v, name="Ventes",
                               marker_color="rgba(40,168,79,.8)",
                               text=glob_v, textposition="outside"))
        fig_m.update_layout(title="Évolution Mensuelle — Essais & Ventes",
                            barmode="group", height=320,
                            plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_m, use_container_width=True)

    with c2:
        cumul_v = [sum(glob_v[:i + 1]) for i in range(len(glob_v))]
        obj_fy26 = int(df_all["Objectif"].replace(0, float("nan")).dropna().sum())
        fig_c = go.Figure()
        fig_c.add_trace(go.Scatter(
            x=active_months, y=cumul_v,
            mode="lines+markers+text",
            name="Vélos vendus (cumulé)",
            line=dict(color="#28a84f", width=2.5),
            fill="tozeroy", fillcolor="rgba(40,168,79,.1)",
            text=[f"{v}🚲" for v in cumul_v],
            textposition="top center",
        ))
        fig_c.add_hline(y=obj_fy26, line_dash="dash", line_color="#e67e22",
                        annotation_text=f"Objectif {obj_fy26}",
                        annotation_position="right")
        fig_c.update_layout(
            title=f"Progression Cumulée vs Objectif ({obj_fy26})",
            height=320, plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(range=[0, max(obj_fy26 + 20, max(cumul_v) + 5)]),
        )
        st.plotly_chart(fig_c, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 8 — SHOPIFY (sell-in B2B)
# ═══════════════════════════════════════════════════════════════════
with tabs[7]:
    st.markdown("## 🛒 Commandes Shopify — Sell-in B2B")

    if df_orders.empty:
        st.warning(
            "⚠️ Données Shopify non disponibles.\n\n"
            "Vérifiez `shopify_client_id` et `shopify_client_secret` dans les secrets."
        )
    else:
        total_ca_shop  = df_orders["ca"].sum()
        total_cmds     = len(df_orders)
        total_articles = int(df_orders["nb_items"].sum())
        panier_moy     = total_ca_shop / total_cmds if total_cmds > 0 else 0

        ks1, ks2, ks3, ks4 = st.columns(4)
        ks1.metric("CA Sell-in",      f"{total_ca_shop:,.0f} €".replace(",", " "))
        ks2.metric("Commandes",       total_cmds)
        ks3.metric("Articles",        total_articles)
        ks4.metric("Panier Moyen",    f"{panier_moy:,.0f} €".replace(",", " "))

        st.markdown("---")

        stores_sel = ["Tous"] + sorted(df_orders["store_raw"].dropna().unique().tolist())
        sel_s = st.selectbox("Filtrer par magasin", stores_sel, key="sh_store")
        df_o = df_orders if sel_s == "Tous" else df_orders[df_orders["store_raw"] == sel_s]

        c1, c2 = st.columns(2)
        with c1:
            by_s = (df_o.groupby("store_raw")
                    .agg(CA=("ca", "sum"), Commandes=("order_id", "count"))
                    .reset_index().sort_values("CA"))
            fig = px.bar(by_s, x="CA", y="store_raw", orientation="h",
                         text="CA", title="CA par Magasin (€)",
                         color_discrete_sequence=["#22c55e"])
            fig.update_traces(texttemplate="%{x:,.0f}€", textposition="outside")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=420)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            if "created_at" in df_o.columns:
                dated_o = df_o.dropna(subset=["created_at"]).copy()
                dated_o["mois"] = dated_o["created_at"].dt.to_period("M").astype(str)
                by_m = dated_o.groupby("mois").agg(
                    CA=("ca", "sum"), Commandes=("order_id", "count")
                ).reset_index()
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=by_m["mois"], y=by_m["CA"],
                    name="CA (€)", marker_color="#22c55e",
                    text=by_m["CA"].apply(lambda x: f"{x:,.0f}€"),
                    textposition="outside",
                ))
                fig.update_layout(title="CA Mensuel Shopify",
                                  plot_bgcolor="white", paper_bgcolor="white", height=420)
                st.plotly_chart(fig, use_container_width=True)

        show_cols = [c for c in ["created_at", "store_raw", "order_name", "ca", "nb_items"] if c in df_o.columns]
        st.dataframe(df_o[show_cols].sort_values("created_at", ascending=False),
                     use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
src_label = "Google Sheets live" if sheet_ok else "données locales"
st.caption(
    f"🚲 Cyclable × Elwing Dashboard FY26 · "
    f"Source : {src_label} + Shopify · "
    f"Accès réservé — {datetime.now().strftime('%d/%m/%Y')}"
)
