"""
Cyclable — Dashboard FY26
Source : Google Sheets ONE PAGE
Déploiement : Streamlit Cloud
Design : Ritmic (#081119 · #FFF359)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
SHEET_ID  = "1EZdvK-6u0yDtpw-xJUlqqQ1heScSFdDPLVoBJvO5TSI"
SHEET_GID = "1665770308"

MONTHS = ["Oct 25","Nov 25","Déc 25","Jan 26","Fév 26","Mar 26",
          "Avr 26","Mai 26","Jun 26","Jul 26","Aoû 26","Sep 26"]
CUR = 6   # Avril 2026

INK    = "#0D0D12"
YELLOW = "#FFF359"
BG     = "#F4F4F0"
CARD   = "#FFFFFF"
MID    = "#64748b"

REP_COLORS  = {"Caroline": "#e879f9", "Thomas": "#38bdf8", "Tanguy": "#fb923c"}
TYPE_COLORS = {"Filiale": "#38bdf8",  "Franchisé": "#fb923c"}

st.set_page_config(
    page_title="Cyclable · Dashboard FY26",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# STYLES — RITMIC
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, sans-serif;
  }}

  /* ── App background ── */
  .stApp {{ background: {BG}; }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{
    background: {INK} !important;
  }}
  [data-testid="stSidebar"] * {{
    color: rgba(255,255,255,.85) !important;
  }}
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stTextInput label {{
    color: rgba(255,255,255,.5) !important;
    font-size: .7rem !important;
    text-transform: uppercase;
    letter-spacing: .6px;
  }}
  [data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,.1) !important;
  }}
  [data-testid="stSidebar"] .stButton button {{
    background: rgba(255,255,255,.08) !important;
    color: rgba(255,255,255,.85) !important;
    border: 1px solid rgba(255,255,255,.15) !important;
    border-radius: 8px !important;
    font-size: .8rem !important;
  }}
  [data-testid="stSidebar"] .stButton button:hover {{
    background: {YELLOW} !important;
    color: {INK} !important;
    border-color: {YELLOW} !important;
  }}

  /* ── Metric cards ── */
  [data-testid="stMetric"] {{
    background: {CARD};
    border-radius: 12px;
    padding: 20px 18px 16px !important;
    border-top: 3px solid {YELLOW};
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    transition: transform .15s;
  }}
  [data-testid="stMetric"]:hover {{ transform: translateY(-2px); }}
  [data-testid="stMetricLabel"] {{
    font-size: .68rem !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: .7px;
    color: {MID} !important;
  }}
  [data-testid="stMetricValue"] {{
    font-size: 1.85rem !important;
    font-weight: 900 !important;
    color: {INK} !important;
    letter-spacing: -.5px;
  }}
  [data-testid="stMetricDelta"] {{ font-size: .78rem !important; font-weight: 600 !important; }}

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
    background: {CARD};
    border-radius: 10px 10px 0 0;
    padding: 0 8px;
    border-bottom: 2px solid #e5e5e0;
    gap: 0;
  }}
  .stTabs [data-baseweb="tab"] {{
    font-weight: 700;
    font-size: .78rem;
    text-transform: uppercase;
    letter-spacing: .5px;
    color: {MID};
    padding: 14px 18px;
    border-bottom: 3px solid transparent;
    margin-bottom: -2px;
  }}
  .stTabs [aria-selected="true"] {{
    color: {INK} !important;
    border-bottom-color: {YELLOW} !important;
  }}
  .stTabs [data-baseweb="tab-panel"] {{
    padding-top: 24px;
  }}

  /* ── Primary button ── */
  button[kind="primary"] {{
    background: {YELLOW} !important;
    color: {INK} !important;
    border: none !important;
    font-weight: 800 !important;
    border-radius: 8px !important;
  }}
  button[kind="primary"]:hover {{
    background: #ede820 !important;
  }}

  /* ── Section headers ── */
  h2 {{
    color: {INK};
    font-weight: 900;
    letter-spacing: -.4px;
    border-left: 4px solid {YELLOW};
    padding-left: 12px;
    margin-bottom: 16px !important;
  }}
  h3 {{ color: {INK}; font-weight: 800; font-size: 1rem; }}

  /* ── Containers / cards ── */
  [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD};
    border-radius: 12px;
    border: 1px solid #e5e5e0 !important;
    padding: 16px !important;
  }}

  /* ── DataFrames ── */
  [data-testid="stDataFrame"] {{
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e5e5e0;
  }}

  /* ── Warnings / info ── */
  [data-testid="stAlert"] {{ border-radius: 10px; }}

  /* ── Remove top padding ── */
  .block-container {{ padding-top: 1.2rem !important; padding-bottom: 2rem !important; }}

  /* ── Divider ── */
  hr {{ border-color: #e5e5e0 !important; }}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def login_page():
    st.markdown(f"""
    <style>
      .stApp {{ background: {INK} !important; }}
      .login-box {{
        max-width: 400px; margin: 80px auto 0;
        background: #141c26; border-radius: 16px;
        padding: 40px; border: 1px solid rgba(255,255,255,.08);
      }}
      .login-logo {{
        width: 48px; height: 48px; background: {YELLOW};
        border-radius: 10px; display: flex; align-items: center;
        justify-content: center; font-size: 24px; margin-bottom: 20px;
      }}
      .login-title {{
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem; font-weight: 900;
        color: #fff; margin-bottom: 4px; letter-spacing: -.4px;
      }}
      .login-sub {{
        font-size: .82rem; color: rgba(255,255,255,.4);
        margin-bottom: 28px;
      }}
    </style>
    <div class="login-box">
      <div class="login-logo">🚲</div>
      <div class="login-title">Cyclable Dashboard</div>
      <div class="login-sub">FY26 · Accès réservé Cyclable × Elwing</div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        pwd = st.text_input("", type="password", placeholder="Mot de passe",
                            label_visibility="collapsed")
        if st.button("Accéder au dashboard", use_container_width=True, type="primary"):
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
# DONNÉES STATIQUES (fallback)
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
    df["Conversion"]    = df.apply(lambda r: round(r.Ventes / r.Essais * 100) if r.Essais > 0 else 0, axis=1)
    df["Magasin_court"] = df["Magasin"].str.replace("Cyclable ", "", regex=False)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# GPS LOOKUP
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

MONTH_ACT_COLS = [18, 20, 22, 24, 26, 28, 30, 32]

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
# CHARGEMENT GOOGLE SHEETS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600 * 4, show_spinner="Chargement Google Sheets…")
def load_google_sheet():
    url = (f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
           f"/export?format=csv&gid={SHEET_GID}")
    try:
        df = pd.read_csv(url, header=0, on_bad_lines="skip")
        return df, True
    except Exception:
        return None, False


def _clean_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
              .str.replace("\u00a0", "", regex=False)
              .str.replace(" ",     "", regex=False)
              .str.replace("€",     "", regex=False)
              .str.replace(",",     ".", regex=False)
              .str.replace(r"[^\d.\-]", "", regex=True),
        errors="coerce",
    ).fillna(0)


def map_sheet_to_df(raw: pd.DataFrame) -> pd.DataFrame:
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
    df["Essais"]    = 0
    df["Ventes"]    = df["Vélos"]
    df["Lat"]       = df["Magasin"].map(lambda n: GPS_LOOKUP.get(n, (46.5, 2.5))[0])
    df["Lng"]       = df["Magasin"].map(lambda n: GPS_LOOKUP.get(n, (46.5, 2.5))[1])
    df = df[df["Magasin"].str.len() > 3].copy()
    df = df[~df["Magasin"].str.lower().str.contains(
        r"^nan$|total|magasin|store|reps|---", na=True)].copy()
    if df.empty:
        return None
    df["Conversion"]    = 0
    df["Magasin_court"] = df["Magasin"].str.replace("Cyclable ", "", regex=False)
    return df.reset_index(drop=True)


def extract_monthly_ventes(raw: pd.DataFrame) -> dict:
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
        vals_12 = vals + [None] * (12 - len(vals))
        monthly[magasin] = vals_12
    return monthly


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT
# ══════════════════════════════════════════════════════════════════════════════
raw_sheet, sheet_ok = load_google_sheet()
monthly_v_live = {}

if sheet_ok and raw_sheet is not None:
    df_all         = map_sheet_to_df(raw_sheet)
    monthly_v_live = extract_monthly_ventes(raw_sheet)
else:
    df_all = None

if df_all is None or df_all.empty:
    df_all   = get_static_data()
    sheet_ok = False

MONTHLY_V_ACTIVE = monthly_v_live if monthly_v_live else MONTHLY_V


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
      <div style="width:34px;height:34px;background:{YELLOW};border-radius:8px;
                  display:flex;align-items:center;justify-content:center;font-size:16px">🚲</div>
      <div>
        <div style="font-weight:900;font-size:.95rem;color:#fff">Cyclable</div>
        <div style="font-size:.65rem;color:rgba(255,255,255,.35);text-transform:uppercase;
                    letter-spacing:.5px">Dashboard FY26</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    reps  = ["Tous"] + sorted(df_all["Rep"].dropna().unique().tolist())
    types = ["Tous"] + sorted(df_all["Type"].dropna().unique().tolist())
    sel_rep  = st.selectbox("Commercial", reps)
    sel_type = st.selectbox("Type", types)
    search   = st.text_input("Rechercher", placeholder="ex: Bordeaux…")
    st.divider()

    if st.button("Rafraîchir les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    src_icon = "🟢" if sheet_ok else "🟡"
    src_txt  = "Google Sheets live" if sheet_ok else "Données locales"
    st.markdown(
        f"<div style='font-size:.72rem;color:rgba(255,255,255,.4)'>"
        f"{src_icon} {src_txt}<br>"
        f"Mis à jour {datetime.now().strftime('%d/%m %H:%M')}</div>",
        unsafe_allow_html=True,
    )
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
    st.sidebar.markdown(
        f"<div style='font-size:.75rem;color:{YELLOW};margin-top:4px'>"
        f"🔎 {len(df)} / {len(df_all)} magasins</div>",
        unsafe_allow_html=True,
    )

if not sheet_ok:
    st.warning("⚠️ Google Sheet non accessible — données locales affichées. "
               "Vérifiez le partage public du sheet, puis **Rafraîchir**.")


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="display:flex;align-items:flex-end;justify-content:space-between;
            margin-bottom:24px">
  <div>
    <div style="font-size:1.7rem;font-weight:900;color:{INK};letter-spacing:-.6px;
                line-height:1.1">
      Cyclable <span style="color:{MID}">× Elwing</span>
    </div>
    <div style="font-size:.8rem;color:{MID};margin-top:2px">
      ONE PAGE B2C-B2B · FY26 · {datetime.now().strftime('%d %B %Y')}
    </div>
  </div>
  <div style="background:{INK};color:{YELLOW};padding:6px 18px;border-radius:20px;
              font-size:.75rem;font-weight:800;letter-spacing:.4px">
    AVRIL 2026
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "Vue Générale",
    "Essais & Ventes",
    "Février",
    "Mars",
    "Avril",
    "Carte",
    "Suivi Mensuel",
])

PLOT_LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter, system-ui, sans-serif", color=INK),
    margin=dict(t=40, b=20, l=10, r=10),
)


# ═══════════════════════════════════════════════════════════════════
# TAB 1 — VUE GÉNÉRALE
# ═══════════════════════════════════════════════════════════════════
with tabs[0]:
    ca_total   = df["CA"].sum()
    velos_tot  = df["Vélos"].sum()
    obj_tot    = df["Objectif"].replace(0, float("nan")).dropna().sum() or 1
    gap_tot    = velos_tot - obj_tot
    essais_tot = df["Essais"].sum()
    ventes_tot = df["Ventes"].sum()
    conv_tot   = round(ventes_tot / essais_tot * 100, 1) if essais_tot > 0 else 0.0
    att_pct    = round(velos_tot / obj_tot * 100, 1)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("CA HT Total",       f"{ca_total:,.0f} €".replace(",", " "))
    k2.metric("Vélos Sell-out",    f"{int(velos_tot)} 🚲", f"Obj : {int(obj_tot)}")
    k3.metric("Atteinte Objectif", f"{att_pct} %",         f"{int(velos_tot)} / {int(obj_tot)}")
    k4.metric("Gap vs Objectif",   f"−{int(abs(gap_tot))}", "vélos restants")
    k5.metric("Essais Total",      f"{int(essais_tot)}",   f"Conv. {conv_tot} %")
    k6.metric("Magasins",          f"{len(df)}",
              f"{len(df[df.Type=='Filiale'])} fil. · {len(df[df.Type=='Franchisé'])} fr.")

    st.markdown("---")
    st.markdown("## Filiales vs Franchisés")
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
        m1.metric("CA HT",         f"{ca:,.0f} €".replace(",", " "))
        m2.metric("Vélos sell-out", int(vel))
        m3.metric("Atteinte",      f"{at} %")
        n1, n2, n3 = st.columns(3)
        n1.metric("Essais démo",   int(es))
        n2.metric("Taux conv.",    f"{cv} %")
        n3.metric("Gap",           f"−{int(abs(vel - ob))}")

    with col_f:
        with st.container(border=True):
            vs_block(df[df["Type"] == "Filiale"], "Filiales")
    with col_fr:
        with st.container(border=True):
            vs_block(df[df["Type"] == "Franchisé"], "Franchisés")

    st.markdown("---")
    st.markdown("## Graphiques")
    ch1, ch2 = st.columns(2)

    with ch1:
        top10 = df.nlargest(10, "CA")
        fig = px.bar(top10, x="Magasin_court", y="CA",
                     color="Rep", color_discrete_map=REP_COLORS,
                     title="Top Magasins — CA HT (€)", text="CA")
        fig.update_traces(texttemplate="%{y:,.0f}€", textposition="outside")
        fig.update_layout(**PLOT_LAYOUT, height=350, xaxis_tickangle=-30, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        rep_data = df.groupby("Rep").agg(
            Objectif=("Objectif", "sum"), Vélos=("Vélos", "sum")).reset_index()
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="Objectif", x=rep_data["Rep"], y=rep_data["Objectif"],
            marker_color=[REP_COLORS.get(r, "#94a3b8") for r in rep_data["Rep"]],
            opacity=0.25))
        fig2.add_trace(go.Bar(
            name="Vendus", x=rep_data["Rep"], y=rep_data["Vélos"],
            marker_color=[REP_COLORS.get(r, "#94a3b8") for r in rep_data["Rep"]],
            text=rep_data["Vélos"].astype(str) + " 🚲", textposition="outside"))
        fig2.update_layout(**PLOT_LAYOUT, title="Vélos Sell-out vs Objectif / Commercial",
                           barmode="group", height=350)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("## Performance par Commercial")
    rep_cols = st.columns(df["Rep"].nunique() or 1)
    for i, (rep, grp) in enumerate(df.groupby("Rep")):
        with rep_cols[i % len(rep_cols)]:
            with st.container(border=True):
                st.markdown(f"**{rep}** · {len(grp)} magasins")
                r1, r2 = st.columns(2)
                r1.metric("CA HT",    f"{grp['CA'].sum():,.0f} €".replace(",", " "))
                r2.metric("Vélos 🚲", int(grp["Vélos"].sum()))
                r3, r4 = st.columns(2)
                ob_ = grp["Objectif"].replace(0, float("nan")).dropna().sum() or 0
                r3.metric("Objectif", int(ob_))
                att = round(grp["Vélos"].sum() / ob_ * 100, 1) if ob_ > 0 else 0
                r4.metric("Atteinte", f"{att} %")

    st.markdown("---")
    st.markdown("## Détail par Magasin")
    disp = df[["Magasin","Rep","Type","CA","Vélos","Objectif","Gap","Confiance","Essais","Ventes","Conversion"]].copy()
    disp["CA"]         = disp["CA"].apply(lambda x: f"{x:,.0f} €".replace(",", " "))
    disp["Conversion"] = disp["Conversion"].apply(lambda x: f"{x}%" if x > 0 else "—")
    disp["Confiance"]  = disp["Confiance"].apply(lambda x: "⭐"*int(x) if pd.notna(x) and x > 0 else "—")
    st.dataframe(disp, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 2 — ESSAIS & VENTES
# ═══════════════════════════════════════════════════════════════════
with tabs[1]:
    e_tot = df["Essais"].sum(); v_tot = df["Ventes"].sum()
    c_tot = round(v_tot / e_tot * 100, 1) if e_tot > 0 else 0
    fil = df[df["Type"]=="Filiale"]; fra = df[df["Type"]=="Franchisé"]
    fil_e = fil["Essais"].sum(); fil_v = fil["Ventes"].sum()
    fra_e = fra["Essais"].sum(); fra_v = fra["Ventes"].sum()

    ke1, ke2, ke3, ke4, ke5 = st.columns(5)
    ke1.metric("Total Essais",      int(e_tot))
    ke2.metric("Total Ventes",      f"{int(v_tot)} 🚲")
    ke3.metric("Taux Conv. Global", f"{c_tot} %", f"{int(v_tot)} / {int(e_tot)}")
    ke4.metric("Filiale",           f"{round(fil_v/fil_e*100,1) if fil_e else 0} %",
               f"{int(fil_e)}E → {int(fil_v)}V")
    ke5.metric("Franchisé",         f"{round(fra_v/fra_e*100,1) if fra_e else 0} %",
               f"{int(fra_e)}E → {int(fra_v)}V")
    st.markdown("---")

    rep_agg = df.groupby("Rep").agg(Essais=("Essais","sum"), Ventes=("Ventes","sum")).reset_index()
    rep_agg["Conv"] = (rep_agg["Ventes"]/rep_agg["Essais"]*100).round(1).fillna(0)

    rc1, rc2 = st.columns(2)
    with rc1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Essais", x=rep_agg["Rep"], y=rep_agg["Essais"],
            marker_color=[REP_COLORS.get(r,"#94a3b8") for r in rep_agg["Rep"]],
            opacity=0.4, text=rep_agg["Essais"], textposition="outside"))
        fig.add_trace(go.Bar(name="Ventes", x=rep_agg["Rep"], y=rep_agg["Ventes"],
            marker_color=[REP_COLORS.get(r,"#94a3b8") for r in rep_agg["Rep"]],
            text=rep_agg["Ventes"].astype(str)+"🚲", textposition="outside"))
        fig.update_layout(**PLOT_LAYOUT, title="Essais vs Ventes / Commercial",
                          barmode="group", height=320)
        st.plotly_chart(fig, use_container_width=True)
    with rc2:
        fig2 = px.bar(rep_agg, x="Conv", y="Rep", orientation="h",
                      color="Rep", color_discrete_map=REP_COLORS,
                      text="Conv", title="Taux de Conversion (%)")
        fig2.update_traces(texttemplate="%{x}%", textposition="outside")
        fig2.update_layout(**PLOT_LAYOUT, showlegend=False, height=320,
                           xaxis=dict(range=[0, 120]))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    ev_df = df[df["Essais"] > 0].sort_values("Essais", ascending=False)
    if not ev_df.empty:
        fig3 = px.bar(ev_df, x="Magasin_court", y="Essais",
                      color="Rep", color_discrete_map=REP_COLORS,
                      text="Essais", title="Essais par Magasin")
        fig3.update_traces(textposition="outside")
        fig3.update_layout(**PLOT_LAYOUT, height=300, xaxis_tickangle=-30)
        st.plotly_chart(fig3, use_container_width=True)

    ess = df[["Magasin","Type","Rep","Essais","Ventes","Conversion"]].copy()
    ess["Conversion"] = ess["Conversion"].apply(lambda x: f"{x}%" if x > 0 else "—")
    st.dataframe(ess.sort_values("Essais", ascending=False), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 3 — FÉVRIER
# ═══════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("## Février 2026 — 11 magasins actifs")
    kf1, kf2, kf3, kf4 = st.columns(4)
    kf1.metric("Vélos Vendus",    "8 🚲");  kf2.metric("Essais", "14")
    kf3.metric("Taux Conv.",     "57 %");   kf4.metric("CA HT Estimé", "~51 k€")
    st.markdown("---")
    c1, c2 = st.columns(2)
    fev_velos  = pd.DataFrame({"Magasin":["Bordeaux","Le Havre","Lyon 6","Paris 13","Nantes","Poitiers"],"Vélos":[4,1,1,1,1,1]})
    fev_essais = pd.DataFrame({"Magasin":["Paris 17","Le Havre","Lyon 7","Clermont","Lyon 6","Paris 13"],"Essais":[3,2,2,2,1,1]})
    with c1:
        fig = px.bar(fev_velos, x="Magasin", y="Vélos", text="Vélos",
                     title="Vélos Vendus — Février", color_discrete_sequence=[YELLOW])
        fig.update_traces(textposition="outside", marker_line_color=INK, marker_line_width=1.5)
        fig.update_layout(**PLOT_LAYOUT, height=300, font_color=INK)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(fev_essais, x="Magasin", y="Essais", text="Essais",
                     title="Essais Réalisés — Février", color_discrete_sequence=["#c4c000"])
        fig.update_traces(textposition="outside")
        fig.update_layout(**PLOT_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pd.DataFrame([
        {"Magasin":"Bordeaux","Rep":"Tanguy","Essais Fév":2,"Ventes Fév":4},
        {"Magasin":"Le Havre","Rep":"Caroline","Essais Fév":2,"Ventes Fév":1},
        {"Magasin":"Lyon 6","Rep":"Thomas","Essais Fév":1,"Ventes Fév":1},
        {"Magasin":"Paris 13","Rep":"Caroline","Essais Fév":1,"Ventes Fév":2},
        {"Magasin":"Paris 17","Rep":"Caroline","Essais Fév":3,"Ventes Fév":0},
        {"Magasin":"Lyon 7","Rep":"Thomas","Essais Fév":2,"Ventes Fév":0},
        {"Magasin":"Nantes Beaujoire","Rep":"Tanguy","Essais Fév":0,"Ventes Fév":1},
        {"Magasin":"Poitiers","Rep":"Tanguy","Essais Fév":0,"Ventes Fév":1},
        {"Magasin":"Clermont","Rep":"Thomas","Essais Fév":2,"Ventes Fév":0},
        {"Magasin":"Strasbourg Étoile","Rep":"Thomas","Essais Fév":1,"Ventes Fév":0},
        {"Magasin":"Nancy","Rep":"Thomas","Essais Fév":1,"Ventes Fév":0},
    ]), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 4 — MARS
# ═══════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("## Mars 2026 — 15 magasins actifs")
    km1, km2, km3, km4 = st.columns(4)
    km1.metric("Vélos Vendus",   "9 🚲");  km2.metric("Essais", "16")
    km3.metric("Taux Conv.",    "56 %");   km4.metric("CA HT Estimé", "~31 k€")
    st.markdown("---")
    c1, c2 = st.columns(2)
    mar_velos  = pd.DataFrame({"Magasin":["Bordeaux","Le Havre","Lyon 6","Paris 13"],"Vélos":[3,2,2,1]})
    mar_essais = pd.DataFrame({"Magasin":["Le Havre","Paris 17","Lyon 7","Lyon 6","Paris 13","Avignon"],"Essais":[2,2,2,1,1,1]})
    with c1:
        fig = px.bar(mar_velos, x="Magasin", y="Vélos", text="Vélos",
                     title="Vélos Vendus — Mars", color_discrete_sequence=[YELLOW])
        fig.update_traces(textposition="outside", marker_line_color=INK, marker_line_width=1.5)
        fig.update_layout(**PLOT_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(mar_essais, x="Magasin", y="Essais", text="Essais",
                     title="Essais Réalisés — Mars", color_discrete_sequence=["#c4c000"])
        fig.update_traces(textposition="outside")
        fig.update_layout(**PLOT_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pd.DataFrame([
        {"Magasin":"Bordeaux","Rep":"Tanguy","Essais Mar":2,"Ventes Mar":3},
        {"Magasin":"Le Havre","Rep":"Caroline","Essais Mar":2,"Ventes Mar":2},
        {"Magasin":"Lyon 6","Rep":"Thomas","Essais Mar":1,"Ventes Mar":2},
        {"Magasin":"Paris 13","Rep":"Caroline","Essais Mar":1,"Ventes Mar":1},
        {"Magasin":"Castelnau","Rep":"Thomas","Essais Mar":0,"Ventes Mar":1},
        {"Magasin":"Poitiers","Rep":"Tanguy","Essais Mar":0,"Ventes Mar":1},
        {"Magasin":"Paris 17","Rep":"Caroline","Essais Mar":3,"Ventes Mar":0},
        {"Magasin":"Lyon 7","Rep":"Thomas","Essais Mar":3,"Ventes Mar":0},
        {"Magasin":"Avignon","Rep":"Thomas","Essais Mar":1,"Ventes Mar":1},
        {"Magasin":"Rennes-Montgermont","Rep":"Tanguy","Essais Mar":1,"Ventes Mar":0},
        {"Magasin":"Lille Centre","Rep":"Caroline","Essais Mar":1,"Ventes Mar":0},
        {"Magasin":"Saint-Étienne","Rep":"Thomas","Essais Mar":2,"Ventes Mar":0},
    ]), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 5 — AVRIL
# ═══════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("## Avril 2026 — Mois en cours")
    vel_total = df_all["Vélos"].sum()
    obj_total = df_all["Objectif"].replace(0, float("nan")).dropna().sum() or 1
    pct_att   = round(vel_total / obj_total * 100, 1)

    ka1, ka2, ka3, ka4 = st.columns(4)
    ka1.metric("Magasins Actifs", f"{len(df[df['Vélos']>0])} 🏪")
    ka2.metric("Vélos YTD",       f"{int(vel_total)} 🚲")
    ka3.metric("Objectif FY26",   f"{int(obj_total)} 🚲")
    ka4.metric("CA HT YTD",       f"{df_all['CA'].sum():,.0f} €".replace(",", " "))
    st.markdown("---")

    prog1, prog2 = st.columns([2, 1])
    with prog1:
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pct_att,
            delta={"reference": 100, "suffix": "%"},
            title={"text": "Atteinte Objectif FY26", "font": {"size": 17, "color": INK}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": YELLOW},
                "bgcolor": "#f4f4f0",
                "steps": [
                    {"range": [0,  50], "color": "#fee2e2"},
                    {"range": [50, 75], "color": "#fef3c7"},
                    {"range": [75,100], "color": "#dcfce7"},
                ],
                "threshold": {"line": {"color": INK, "width": 3},
                              "thickness": 0.75, "value": 100},
            },
            number={"suffix": "%", "font": {"color": INK, "size": 42}},
        ))
        fig_g.update_layout(height=280, margin=dict(t=40, b=10),
                            paper_bgcolor="white", font_family="Inter")
        st.plotly_chart(fig_g, use_container_width=True)
    with prog2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.metric("Vélos vendus",  f"{int(vel_total)} 🚲")
        st.metric("Objectif FY26", f"{int(obj_total)} 🚲")
        st.metric("Restants",      f"{int(obj_total - vel_total)} 🚲")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        top_ca = df[df["CA"]>0].nlargest(10,"CA")
        fig = px.bar(top_ca, x="Magasin_court", y="CA",
                     color="Rep", color_discrete_map=REP_COLORS,
                     text="CA", title="Top CA HT (€) — YTD")
        fig.update_traces(texttemplate="%{y:,.0f}€", textposition="outside")
        fig.update_layout(**PLOT_LAYOUT, height=340, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        top_vel = df[df["Vélos"]>0].sort_values("Vélos", ascending=True)
        fig = px.bar(top_vel, x="Vélos", y="Magasin_court", orientation="h",
                     color="Rep", color_discrete_map=REP_COLORS,
                     text="Vélos", title="Vélos Vendus — YTD")
        fig.update_traces(texttemplate="%{x} 🚲", textposition="outside")
        fig.update_layout(**PLOT_LAYOUT, height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 6 — CARTE
# ═══════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("## Localisation des Magasins Cyclable")
    map_df = df.copy()
    map_df["size"] = map_df["CA"].apply(lambda x: max(8, min(35, 8 + x/600)))
    fig_map = px.scatter_mapbox(
        map_df, lat="Lat", lon="Lng",
        color="Rep", color_discrete_map=REP_COLORS,
        size="size", hover_name="Magasin",
        hover_data={"CA":True,"Vélos":True,"Essais":True,"Lat":False,"Lng":False,"size":False},
        zoom=5, center={"lat":46.5,"lon":2.5}, height=520,
        title="Performance FY26", symbol="Type",
    )
    fig_map.update_layout(mapbox_style="open-street-map",
                          legend=dict(orientation="h", y=-0.05),
                          margin={"r":0,"t":40,"l":0,"b":0},
                          paper_bgcolor="white")
    st.plotly_chart(fig_map, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        region_map = {
            "Île-de-France":             ["Paris","Issy"],
            "Auvergne-Rhône-Alpes":      ["Lyon","Clermont","Valence","Saint-Étienne"],
            "Nouvelle-Aquitaine":        ["Bordeaux","Poitiers","Royan"],
            "Normandie":                 ["Caen","Havre"],
            "Bretagne/Pays-de-la-Loire": ["Nantes","Rennes"],
            "Grand-Est":                 ["Strasbourg","Nancy","Mulhouse","Champagne"],
            "Occitanie":                 ["Montpellier","Castelnau","Avignon"],
            "Autres":                    ["Dijon","Orléans","Lille","Marseille"],
        }
        region_ca = {r: int(df[df["Magasin"].apply(lambda n: any(k in n for k in kws))]["CA"].sum())
                     for r, kws in region_map.items()}
        region_ca = {k: v for k, v in region_ca.items() if v > 0}
        if region_ca:
            fig_r = px.pie(names=list(region_ca.keys()), values=list(region_ca.values()),
                           title="CA HT par Région", hole=0.35,
                           color_discrete_sequence=[YELLOW,"#0D0D12","#64748b","#e2e8f0",
                                                    "#c4c000","#374151","#9ca3af","#f3f4f6"])
            fig_r.update_traces(textposition="inside", textinfo="percent+label")
            fig_r.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig_r, use_container_width=True)
    with c2:
        villes_df = df[df["Vélos"]>0].sort_values("Vélos", ascending=True)
        if not villes_df.empty:
            fig_v = px.bar(villes_df, x="Vélos", y="Magasin_court", orientation="h",
                           color="Rep", color_discrete_map=REP_COLORS,
                           text="Vélos", title="Vélos Sell-out par Magasin")
            fig_v.update_traces(texttemplate="%{x} 🚲", textposition="outside")
            fig_v.update_layout(**PLOT_LAYOUT, height=350, showlegend=False)
            st.plotly_chart(fig_v, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 7 — SUIVI MENSUEL
# ═══════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("## Suivi Annuel FY26 — Oct 25 → Sep 26")
    view = st.radio("Afficher :", ["Essais", "Ventes", "Conversion %"], horizontal=True)

    rows = []
    for _, s in df_all.iterrows():
        me = list(MONTHLY_E.get(s["Magasin"], [0]*12)) + [None]*12
        mv = list(MONTHLY_V_ACTIVE.get(s["Magasin"], [0]*12)) + [None]*12
        me, mv = me[:12], mv[:12]
        row = {"Magasin": s["Magasin"], "Rep": s["Rep"]}
        ytd_e, ytd_v = 0, 0
        for i, m in enumerate(MONTHS):
            if i > CUR:
                row[m] = None
            else:
                e_v = (me[i] or 0) if me[i] is not None else 0
                v_v = (mv[i] or 0) if mv[i] is not None else 0
                ytd_e += e_v; ytd_v += v_v
                row[m] = (e_v if view == "Essais"
                           else v_v if view == "Ventes"
                           else round(v_v/e_v*100) if e_v > 0 else None)
        row["Total YTD"] = (ytd_e if view == "Essais"
                             else ytd_v if view == "Ventes"
                             else round(ytd_v/ytd_e*100) if ytd_e else None)
        rows.append(row)

    df_monthly = pd.DataFrame(rows)
    active_months = MONTHS[:CUR+1]
    st.dataframe(df_monthly.set_index("Magasin"), use_container_width=True,
                 column_config={m: st.column_config.NumberColumn(m, format="%d")
                                for m in active_months})
    st.markdown("---")

    glob_e = [sum((list(MONTHLY_E.get(s["Magasin"],[0]*12))+[0]*12)[:12][i] or 0
                  for _, s in df_all.iterrows()) for i in range(CUR+1)]
    glob_v = [sum((list(MONTHLY_V_ACTIVE.get(s["Magasin"],[0]*12))+[0]*12)[:12][i] or 0
                  for _, s in df_all.iterrows()) for i in range(CUR+1)]

    c1, c2 = st.columns(2)
    with c1:
        fig_m = go.Figure()
        fig_m.add_trace(go.Bar(x=active_months, y=glob_e, name="Essais",
                               marker_color="rgba(56,189,248,.6)",
                               text=glob_e, textposition="outside"))
        fig_m.add_trace(go.Bar(x=active_months, y=glob_v, name="Ventes",
                               marker_color=YELLOW,
                               text=glob_v, textposition="outside",
                               marker_line_color=INK, marker_line_width=1.5))
        fig_m.update_layout(**PLOT_LAYOUT, title="Essais & Ventes par Mois",
                            barmode="group", height=320)
        st.plotly_chart(fig_m, use_container_width=True)
    with c2:
        cumul_v = [sum(glob_v[:i+1]) for i in range(len(glob_v))]
        obj_fy26 = int(df_all["Objectif"].replace(0, float("nan")).dropna().sum())
        fig_c = go.Figure()
        fig_c.add_trace(go.Scatter(
            x=active_months, y=cumul_v, mode="lines+markers+text",
            name="Cumulé", line=dict(color=YELLOW, width=3),
            fill="tozeroy", fillcolor="rgba(255,243,89,.12)",
            text=[f"{v}🚲" for v in cumul_v], textposition="top center",
            marker=dict(color=INK, size=8),
        ))
        fig_c.add_hline(y=obj_fy26, line_dash="dash", line_color=INK,
                        annotation_text=f"Objectif {obj_fy26}",
                        annotation_position="right")
        fig_c.update_layout(**PLOT_LAYOUT, title=f"Progression Cumulée vs Objectif ({obj_fy26})",
                            height=320, yaxis=dict(range=[0, max(obj_fy26+20, max(cumul_v, default=0)+5)]))
        st.plotly_chart(fig_c, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;font-size:.7rem;color:{MID}'>"
    f"Cyclable × Elwing · Dashboard FY26 · "
    f"Source : {'Google Sheets live' if sheet_ok else 'données locales'} · "
    f"Accès réservé · {datetime.now().strftime('%d/%m/%Y')}</div>",
    unsafe_allow_html=True,
)
