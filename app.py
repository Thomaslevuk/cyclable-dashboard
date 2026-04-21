"""
Cyclable × Elwing — Dashboard Live
Sources : Shopify (sell-in B2B) + Google Sheets Essais (CSV public)
"""

import io
import re
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
SHOPIFY_SHOP        = "elwing-boards.myshopify.com"
SHOPIFY_API_VERSION = "2024-01"

CYCLE_START = pd.Timestamp("2025-10-01")
CYCLE_END   = pd.Timestamp("2026-09-30 23:59:59")

# SKUs vélos exacts (d'après capture "nom des références vélos")
BIKE_SKUS = {
    # Solo
    "bk004622", "bk001714", "bk004623",
    # Duo
    "bk004631", "bk001552", "bk004632",
    # Jumbo
    "bk004624", "bk001804", "bk004626",
    # Ritmic Solo / Duo / Jumbo (AL005xxx = vélos uniquement, pas les kits)
    "al005820", "al005821", "al005823", "al005824", "al005825", "al005826",
    "al005834", "al005835", "al005836", "al005837", "al005839", "al005840",
    "al005841", "al005842", "al005843", "al005845", "al005846", "al005847",
}
# Yuvy : SKU commence par "yuvy" (pas dans l'image, détecté par titre)
BIKE_TITLE_KEYWORDS = ("solo", "duo", "jumbo", "yuvy")

CYCLABLE_KEY = "cyclable"

# Google Sheets essais (onglet "essai" — accès public CSV)
ESSAIS_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1EZdvK-6u0yDtpw-xJUlqqQ1heScSFdDPLVoBJvO5TSI"
    "/export?format=csv&gid=1377845477"
)


# ─────────────────────────────────────────────────────────────────────────────
# RÈGLES VÉLOS
# ─────────────────────────────────────────────────────────────────────────────
def is_bike(item: dict) -> bool:
    sku   = (item.get("sku")   or "").lower().strip()
    title = (item.get("title") or "").lower()
    if sku in BIKE_SKUS:
        return True
    if sku.startswith("yuvy"):
        return True
    # fallback titre (Solo/Duo/Jumbo/Yuvy sans SKU renseigné)
    return any(k in title for k in BIKE_TITLE_KEYWORDS)


def count_bikes(items: list) -> int:
    """Vélos payants dans une commande — 1er vélo exclu, 0€ exclus."""
    units = 0
    for it in items or []:
        if not is_bike(it):
            continue
        try:
            price = float(it.get("price") or 0)
        except (TypeError, ValueError):
            price = 0.0
        if price <= 0:
            continue
        try:
            qty = int(it.get("quantity") or 0)
        except (TypeError, ValueError):
            qty = 0
        units += qty
    return max(0, units - 1)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cyclable Dashboard",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  [data-testid="stMetric"] {
    background:#fff; border-radius:12px; padding:16px !important;
    box-shadow:0 2px 12px rgba(0,0,0,.07);
  }
  [data-testid="stMetricLabel"] { font-size:.75rem!important; font-weight:700!important;
    text-transform:uppercase; letter-spacing:.5px; }
  [data-testid="stMetricValue"] { font-size:1.9rem!important; font-weight:800!important; }
  .block-container { padding-top:1.5rem; }
  h2 { color:#1a7a3c; border-bottom:2px solid #28a84f; padding-bottom:6px; }
  .stTabs [aria-selected="true"] { color:#1a7a3c; border-bottom-color:#1a7a3c; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
def login_page():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🚲 Cyclable Dashboard")
        st.markdown("Entrez le mot de passe pour accéder au dashboard.")
        st.divider()
        pwd = st.text_input("Mot de passe", type="password", placeholder="••••••••••")
        if st.button("Se connecter", use_container_width=True, type="primary"):
            if pwd == st.secrets.get("password", ""):
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")

if not st.session_state.get("auth"):
    login_page()
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# SHOPIFY — Token OAuth2
# ─────────────────────────────────────────────────────────────────────────────
def get_shopify_token() -> str:
    token = (
        st.secrets.get("shopify_token", "")
        or st.secrets.get("shopify_access_token", "")
    )
    if token:
        return token
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


# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT — SHOPIFY
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600 * 6, show_spinner="Chargement des commandes Shopify…")
def load_shopify_orders() -> pd.DataFrame:
    token = get_shopify_token()
    if not token:
        return pd.DataFrame()

    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    all_orders = []
    url = (
        f"https://{SHOPIFY_SHOP}/admin/api/{SHOPIFY_API_VERSION}"
        f"/orders.json?limit=250&status=any"
        f"&created_at_min={CYCLE_START.strftime('%Y-%m-%dT%H:%M:%S-00:00')}"
        f"&created_at_max={CYCLE_END.strftime('%Y-%m-%dT%H:%M:%S-00:00')}"
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
            company = (o.get("billing_address") or {}).get("company", "") or ""
        if not company:
            addrs = (o.get("customer") or {}).get("addresses") or []
            company = addrs[0].get("company", "") if addrs else ""
        if not company:
            company = (o.get("shipping_address") or {}).get("company", "") or ""
        if CYCLABLE_KEY not in company.lower():
            continue

        items = o.get("line_items") or []
        rows.append({
            "store_raw":  company.strip() or "Non identifié",
            "order_id":   o["id"],
            "order_name": o.get("name", ""),
            "created_at": o.get("created_at", ""),
            "ca":         float(o.get("total_price") or 0),
            "currency":   o.get("currency", "EUR"),
            "velos":      count_bikes(items),
            "nb_items":   sum(int(i.get("quantity", 0)) for i in items),
            "tags":       o.get("tags", ""),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce").dt.tz_localize(None)
    df = df[(df["created_at"] >= CYCLE_START) & (df["created_at"] <= CYCLE_END)].reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT — ESSAIS (Google Sheets CSV public)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600 * 6, show_spinner="Chargement des essais…")
def load_essais() -> pd.DataFrame:
    try:
        r = requests.get(ESSAIS_CSV_URL, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.content.decode("utf-8")), low_memory=False)

        # Renommage colonnes
        col_map = {
            df.columns[0]:  "essai_num",
            df.columns[1]:  "produit",
            df.columns[3]:  "dept",
            df.columns[4]:  "cp",
            df.columns[5]:  "store",
            df.columns[6]:  "fiscal",
            df.columns[7]:  "year",
            df.columns[8]:  "month",
            df.columns[10]: "product",
            df.columns[16]: "date",
        }
        df = df.rename(columns=col_map)

        # Garder seulement les essais Cyclable
        df = df[df["store"].astype(str).str.lower().str.startswith("cyclable")].copy()

        # Nettoyage date
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # Filtre FY26
        df = df[(df["date"] >= CYCLE_START) & (df["date"] <= CYCLE_END)].reset_index(drop=True)

        # Normalise le nom de store pour affichage
        df["store_display"] = df["store"].apply(_utm_to_label)
        return df

    except Exception as e:
        st.warning(f"Essais indisponibles : {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# NORMALISATION — matching entre UTM essais et company Shopify
# ─────────────────────────────────────────────────────────────────────────────
_UTM_OVERRIDES = {
    "cyclablelemarseille": "cyclablemarseille",
    "cyclablesaintetienne": "cyclablesaintetienne",
}

def _norm(name: str) -> str:
    """Retire 'cyclable', les accents, les non-alphanum → clé de join."""
    n = str(name).lower()
    n = _UTM_OVERRIDES.get(n, n)
    n = n.replace("cyclable", "")
    for o, nw in [("é","e"),("è","e"),("ê","e"),("à","a"),("â","a"),
                  ("ô","o"),("î","i"),("ù","u"),("û","u"),("ç","c")]:
        n = n.replace(o, nw)
    n = re.sub(r"[^a-z0-9]", "", n)
    return n


def _utm_to_label(utm: str) -> str:
    """cyclablelyon6 → Cyclable Lyon 6 (best-effort)"""
    n = str(utm)
    # If it's already readable, return as-is
    if " " in n or n[0].isupper():
        return n
    # Remove 'cyclable' prefix and title-case the rest
    base = re.sub(r"^cyclable", "", n.lower())
    # Insert space before digits
    base = re.sub(r"(\D)(\d)", r"\1 \2", base)
    return "Cyclable " + base.title()


# ─────────────────────────────────────────────────────────────────────────────
# CROISEMENT ESSAIS × VENTES
# ─────────────────────────────────────────────────────────────────────────────
def build_summary(df_e: pd.DataFrame, df_o: pd.DataFrame) -> pd.DataFrame:
    stores: dict = {}

    def _blank(label):
        return {"label": label, "essais": 0, "ca": 0.0, "commandes": 0, "velos": 0}

    if not df_e.empty and "store" in df_e.columns:
        for store, grp in df_e.groupby("store"):
            k = _norm(store)
            label = grp["store_display"].iloc[0] if "store_display" in grp.columns else store
            stores.setdefault(k, _blank(label))
            stores[k]["essais"] += len(grp)

    if not df_o.empty and "store_raw" in df_o.columns:
        df_o2 = df_o.copy()
        df_o2["_key"] = df_o2["store_raw"].apply(_norm)
        for k, grp in df_o2.groupby("_key"):
            label = grp["store_raw"].iloc[0]
            stores.setdefault(k, _blank(label))
            stores[k]["ca"]        += grp["ca"].sum()
            stores[k]["commandes"] += len(grp)
            stores[k]["velos"]     += int(grp["velos"].sum())

    rows = []
    for v in stores.values():
        e, velos = v["essais"], v["velos"]
        rows.append({
            "Magasin":   v["label"],
            "Essais":    e,
            "Commandes": v["commandes"],
            "Vélos":     velos,
            "CA (€)":    round(v["ca"], 2),
            "Conv. %":   round(velos / e * 100, 1) if e > 0 else 0.0,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("Essais", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────────────────────────────────────
df_essais  = load_essais()
df_orders  = load_shopify_orders()
df_summary = build_summary(df_essais, df_orders)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚲 Cyclable")
    st.divider()

    if st.button("🔄 Rafraîchir les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Mis à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    essais_ok = not df_essais.empty
    orders_ok = not df_orders.empty
    st.markdown(
        f"- Essais Google Sheets : {'✅' if essais_ok else '❌ non connecté'}\n"
        f"- Commandes Shopify : {'✅' if orders_ok else '❌ non connecté'}"
    )
    if essais_ok:
        st.caption(f"  {len(df_essais)} essais Cyclable FY26")
    if orders_ok:
        st.caption(f"  {len(df_orders)} commandes Cyclable FY26")

    st.divider()
    if st.button("Déconnexion", use_container_width=True):
        st.session_state["auth"] = False
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 🚲 Cyclable × Elwing — Dashboard FY26")
st.caption(
    f"Compte **Cyclable uniquement** · "
    f"FY : {CYCLE_START.strftime('%d %b %Y')} → {CYCLE_END.strftime('%d %b %Y')} · "
    f"Vélos : Solo / Duo / Jumbo / Yuvy · hors 0 € · 1er vélo/commande exclu"
)
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_essais = len(df_essais) if not df_essais.empty else 0
total_orders = len(df_orders) if not df_orders.empty else 0
total_ca     = df_orders["ca"].sum()        if not df_orders.empty else 0.0
total_velos  = int(df_orders["velos"].sum()) if not df_orders.empty else 0
total_stores = df_summary["Magasin"].nunique() if not df_summary.empty else 0
conv_global  = round(total_velos / total_essais * 100, 1) if total_essais > 0 else 0.0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Essais Cyclable",     f"{total_essais}")
k2.metric("Commandes",           f"{total_orders}")
k3.metric("Vélos vendus",        f"{total_velos}")
k4.metric("CA magasin",          f"{total_ca:,.0f} €".replace(",", " "))
k5.metric("Conv. vélos/essais",  f"{conv_global} %")
k6.metric("Magasins actifs",     f"{total_stores}")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Croisement Essais × Ventes",
    "🔬 Essais (Google Sheets)",
    "🛒 Ventes Shopify",
    "📈 Évolution Mensuelle",
])

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("## 📊 Synthèse par Magasin")

    if df_summary.empty:
        st.info("Connectez vos sources de données pour afficher le croisement.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            top_e = df_summary[df_summary["Essais"] > 0].head(20)
            fig = px.bar(
                top_e, x="Magasin", y="Essais", text="Essais",
                title="Essais par Magasin",
                color="Conv. %", color_continuous_scale="Blues",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_tickangle=-40, plot_bgcolor="white",
                              paper_bgcolor="white", height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            top_ca = df_summary[df_summary["CA (€)"] > 0].head(20)
            if not top_ca.empty:
                fig = px.bar(
                    top_ca, x="Magasin", y="CA (€)",
                    text="CA (€)", title="CA Sell-in par Magasin (Shopify)",
                    color_discrete_sequence=["#22c55e"],
                )
                fig.update_traces(texttemplate="%{y:,.0f}€", textposition="outside")
                fig.update_layout(xaxis_tickangle=-40, plot_bgcolor="white",
                                  paper_bgcolor="white", height=400)
                st.plotly_chart(fig, use_container_width=True)

        # Scatter corrélation
        df_plot = df_summary[(df_summary["Essais"] > 0) | (df_summary["Commandes"] > 0)].copy()
        if not df_plot.empty:
            df_plot["_size"] = df_plot["CA (€)"].clip(lower=100)
            fig_s = px.scatter(
                df_plot, x="Essais", y="Vélos",
                text="Magasin", size="_size",
                title="Corrélation Essais × Vélos vendus  (taille = CA)",
                color="Conv. %", color_continuous_scale="RdYlGn",
                hover_data={"Essais": True, "Vélos": True, "CA (€)": True, "_size": False},
            )
            fig_s.update_traces(textposition="top center")
            fig_s.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=420)
            st.plotly_chart(fig_s, use_container_width=True)

        st.markdown("### Tableau détaillé")
        st.dataframe(
            df_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "CA (€)":    st.column_config.NumberColumn("CA (€)",    format="%.0f €"),
                "Conv. %":   st.column_config.NumberColumn("Conv. %",   format="%.1f %%"),
                "Essais":    st.column_config.NumberColumn("Essais 🔬"),
                "Commandes": st.column_config.NumberColumn("Cmdes 🛒"),
                "Vélos":     st.column_config.NumberColumn("Vélos 🚲"),
            },
        )

# ── TAB 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    if df_essais.empty:
        st.warning("⚠️ Données essais non disponibles.")
    else:
        st.markdown(f"## 🔬 {len(df_essais)} essais Cyclable FY26")

        label_col = "store_display" if "store_display" in df_essais.columns else "store"
        stores_e = ["Tous"] + sorted(df_essais[label_col].dropna().unique().tolist())
        sel_s = st.selectbox("Filtrer par magasin", stores_e, key="filt_essais")
        df_e = df_essais if sel_s == "Tous" else df_essais[df_essais[label_col] == sel_s]

        c1, c2 = st.columns(2)
        with c1:
            by_s = df_e.groupby(label_col).size().reset_index(name="Essais").sort_values("Essais")
            fig = px.bar(by_s, x="Essais", y=label_col, orientation="h",
                         text="Essais", title="Essais par Magasin",
                         color_discrete_sequence=["#3b82f6"])
            fig.update_traces(textposition="outside")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=460)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            dated = df_e.dropna(subset=["date"]).copy()
            if not dated.empty:
                dated["mois"] = dated["date"].dt.to_period("M").astype(str)
                by_m = dated.groupby("mois").size().reset_index(name="Essais")
                fig = px.bar(by_m, x="mois", y="Essais", text="Essais",
                             title="Essais par Mois",
                             color_discrete_sequence=["#6366f1"])
                fig.update_traces(textposition="outside")
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=460)
                st.plotly_chart(fig, use_container_width=True)

        cols_show = [c for c in ["date", label_col, "product", "dept", "cp"] if c in df_e.columns]
        df_show = df_e[cols_show].copy()
        if "date" in df_show.columns:
            df_show = df_show.sort_values("date", ascending=False)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    if df_orders.empty:
        st.warning("⚠️ Données Shopify non disponibles.")
    else:
        st.markdown(f"## 🛒 {len(df_orders)} commandes Cyclable FY26")

        stores_o = ["Tous"] + sorted(df_orders["store_raw"].dropna().unique().tolist())
        sel_o = st.selectbox("Filtrer par magasin", stores_o, key="filt_shop")
        df_o = df_orders if sel_o == "Tous" else df_orders[df_orders["store_raw"] == sel_o]

        c1, c2 = st.columns(2)
        with c1:
            by_s = (
                df_o.groupby("store_raw")
                .agg(CA=("ca", "sum"), Commandes=("order_id", "count"), Vélos=("velos", "sum"))
                .reset_index().sort_values("CA")
            )
            fig = px.bar(by_s, x="CA", y="store_raw", orientation="h",
                         text="CA", title="CA par Magasin (€)",
                         color_discrete_sequence=["#22c55e"])
            fig.update_traces(texttemplate="%{x:,.0f}€", textposition="outside")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=460)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            dated_o = df_o.dropna(subset=["created_at"]).copy()
            dated_o["mois"] = dated_o["created_at"].dt.to_period("M").astype(str)
            by_m = dated_o.groupby("mois").agg(
                CA=("ca", "sum"), Commandes=("order_id", "count"), Vélos=("velos", "sum")
            ).reset_index()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=by_m["mois"], y=by_m["CA"], name="CA (€)",
                                  marker_color="#22c55e",
                                  text=by_m["CA"].apply(lambda x: f"{x:,.0f}€"),
                                  textposition="outside"))
            fig.update_layout(title="CA Mensuel", plot_bgcolor="white",
                              paper_bgcolor="white", height=460)
            st.plotly_chart(fig, use_container_width=True)

        show_cols = [c for c in ["created_at", "store_raw", "order_name", "ca", "velos", "currency"]
                     if c in df_o.columns]
        st.dataframe(
            df_o[show_cols].sort_values("created_at", ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "ca":    st.column_config.NumberColumn("CA (€)",  format="%.0f €"),
                "velos": st.column_config.NumberColumn("Vélos 🚲"),
            },
        )

# ── TAB 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("## 📈 Évolution Mensuelle")

    has_e = not df_essais.empty and "date" in df_essais.columns
    has_o = not df_orders.empty and "created_at" in df_orders.columns

    if has_e:
        em = df_essais.dropna(subset=["date"]).copy()
        em["mois"] = em["date"].dt.to_period("M").astype(str)
        monthly_e = em.groupby("mois").size().reset_index(name="Essais")

    if has_o:
        om = df_orders.dropna(subset=["created_at"]).copy()
        om["mois"] = om["created_at"].dt.to_period("M").astype(str)
        monthly_o = om.groupby("mois").agg(
            Commandes=("order_id", "count"),
            Vélos=("velos", "sum"),
            CA=("ca", "sum"),
        ).reset_index()

    if has_e and has_o:
        merged = pd.merge(monthly_e, monthly_o, on="mois", how="outer").fillna(0).sort_values("mois")

        fig = go.Figure()
        fig.add_trace(go.Bar(x=merged["mois"], y=merged["Essais"], name="Essais",
                              marker_color="rgba(59,130,246,.75)",
                              text=merged["Essais"].astype(int), textposition="outside"))
        fig.add_trace(go.Bar(x=merged["mois"], y=merged["Vélos"], name="Vélos vendus",
                              marker_color="rgba(34,197,94,.85)",
                              text=merged["Vélos"].astype(int), textposition="outside"))
        fig.add_trace(go.Bar(x=merged["mois"], y=merged["Commandes"], name="Commandes",
                              marker_color="rgba(99,102,241,.55)",
                              text=merged["Commandes"].astype(int), textposition="outside"))
        fig.update_layout(title="Essais vs Vélos vendus vs Commandes / Mois",
                          barmode="group", plot_bgcolor="white", paper_bgcolor="white", height=400)
        st.plotly_chart(fig, use_container_width=True)

        merged["CA_cumulé"] = merged["CA"].cumsum()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=merged["mois"], y=merged["CA_cumulé"],
            mode="lines+markers+text",
            text=merged["CA_cumulé"].apply(lambda x: f"{x:,.0f}€"),
            textposition="top center",
            line=dict(color="#22c55e", width=2.5),
            fill="tozeroy", fillcolor="rgba(34,197,94,.1)",
        ))
        fig2.update_layout(title="CA Cumulé Shopify (€)",
                           plot_bgcolor="white", paper_bgcolor="white", height=350)
        st.plotly_chart(fig2, use_container_width=True)

    elif has_e:
        fig = px.bar(monthly_e, x="mois", y="Essais", text="Essais",
                     title="Essais par Mois", color_discrete_sequence=["#3b82f6"])
        fig.update_traces(textposition="outside")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    elif has_o:
        st.info("Google Sheets connecté pour voir l'évolution croisée.")

    else:
        st.info("Connectez vos deux sources de données pour afficher l'évolution mensuelle.")

# ── FOOTER ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🚲 Cyclable × Elwing Dashboard · Sources : Shopify + Google Sheets · Accès réservé")
