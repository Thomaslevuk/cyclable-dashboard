"""
Cyclable × Elwing — Dashboard Live
Sources : Shopify (sell-in B2B) + Google Sheets Essais (sell-out pipeline)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import base64
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────────────────────────────────────
SHOPIFY_SHOP        = "elwing-boards.myshopify.com"
SHOPIFY_API_VERSION = "2024-01"

st.set_page_config(
    page_title="Cyclable Dashboard",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  [data-testid="stMetric"] {
    background: #fff;
    border-radius: 12px;
    padding: 16px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,.07);
  }
  [data-testid="stMetricLabel"]  { font-size:.75rem!important; font-weight:700!important;
                                    text-transform:uppercase; letter-spacing:.5px; }
  [data-testid="stMetricValue"]  { font-size:1.9rem!important; font-weight:800!important; }
  .block-container               { padding-top:1.5rem; }
  h2 { color:#1a7a3c; border-bottom:2px solid #28a84f; padding-bottom:6px; }
  .stTabs [aria-selected="true"] { color:#1a7a3c; border-bottom-color:#1a7a3c; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTIFICATION
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
# CHARGEMENT — GOOGLE SHEETS ESSAIS (via Google Apps Script)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600 * 8, show_spinner="Chargement des essais…")
def load_essais() -> pd.DataFrame:
    """
    Lit l'onglet 'essai' via le Web App Google Apps Script.
    Colonnes attendues dans la réponse : store, date, product, dept, cp
    """
    gas_url = st.secrets.get("gas_url", "")
    if not gas_url:
        return pd.DataFrame()
    try:
        resp = requests.get(f"{gas_url}?mode=essais", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            st.warning(f"Google Sheets : {data['error']}")
            return pd.DataFrame()
        df = pd.DataFrame(data.get("rows", []))
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df
    except Exception as e:
        st.warning(f"Essais indisponibles : {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT — SHOPIFY (commandes B2B magasins)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600 * 8, show_spinner="Chargement des commandes Shopify…")
def load_shopify_orders() -> pd.DataFrame:
    """
    Récupère toutes les commandes Shopify.
    Authentification : Admin API Access Token (X-Shopify-Access-Token).
    Le nom du magasin Cyclable est dans le champ 'company' des commandes.
    """
    token = st.secrets.get("shopify_token", "")
    if not token:
        return pd.DataFrame()

    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }
    all_orders = []
    url = (
        f"https://{SHOPIFY_SHOP}/admin/api/{SHOPIFY_API_VERSION}"
        "/orders.json?limit=250&status=any"
    )

    while url:
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            all_orders.extend(r.json().get("orders", []))
            # Pagination curseur Shopify
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
        # Cherche le nom de l'entreprise dans plusieurs endroits
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
            "tags":       o.get("tags", ""),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce").dt.tz_localize(None)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# CROISEMENT ESSAIS × VENTES
# ─────────────────────────────────────────────────────────────────────────────
def normalize(name: str) -> str:
    """Normalise un nom de magasin pour le matching entre les deux sources."""
    n = str(name).lower().strip()
    for old, new in [
        ("cyclable ", ""), ("cyclable-", ""), ("cyclable_", ""),
        ("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"),
        ("â", "a"), ("ô", "o"), ("î", "i"), ("ù", "u"),
        ("-", " "), ("_", " "),
    ]:
        n = n.replace(old, new)
    return n.strip()


def build_summary(df_e: pd.DataFrame, df_o: pd.DataFrame) -> pd.DataFrame:
    stores: dict = {}

    if not df_e.empty and "store" in df_e.columns:
        for store, grp in df_e.groupby("store"):
            k = normalize(store)
            stores.setdefault(k, {"label": store, "essais": 0, "ca": 0.0, "commandes": 0, "articles": 0})
            stores[k]["essais"] += len(grp)

    if not df_o.empty and "store_raw" in df_o.columns:
        df_o = df_o.copy()
        df_o["_key"] = df_o["store_raw"].apply(normalize)
        for k, grp in df_o.groupby("_key"):
            stores.setdefault(k, {"label": grp["store_raw"].iloc[0], "essais": 0, "ca": 0.0, "commandes": 0, "articles": 0})
            stores[k]["ca"]        += grp["ca"].sum()
            stores[k]["commandes"] += len(grp)
            stores[k]["articles"]  += int(grp["nb_items"].sum())

    rows = []
    for v in stores.values():
        e, c = v["essais"], v["commandes"]
        rows.append({
            "Magasin":    v["label"],
            "Essais":     e,
            "Commandes":  c,
            "Articles":   v["articles"],
            "CA (€)":     round(v["ca"], 2),
            "Conv. %":    round(c / e * 100, 1) if e > 0 else 0.0,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("Essais", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT DES DONNÉES
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

    st.divider()
    if st.button("Déconnexion", use_container_width=True):
        st.session_state["auth"] = False
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 🚲 Cyclable × Elwing — Dashboard")
st.divider()

# ── KPIs GLOBAUX ──────────────────────────────────────────────────────────────
total_essais   = len(df_essais) if not df_essais.empty else 0
total_orders   = len(df_orders) if not df_orders.empty else 0
total_ca       = df_orders["ca"].sum()       if not df_orders.empty else 0.0
total_articles = int(df_orders["nb_items"].sum()) if not df_orders.empty else 0
total_stores   = df_summary["Magasin"].nunique() if not df_summary.empty else 0
conv_global    = round(total_orders / total_essais * 100, 1) if total_essais > 0 else 0.0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Essais totaux",     f"{total_essais}")
k2.metric("Commandes Shopify", f"{total_orders}")
k3.metric("Articles vendus",   f"{total_articles}")
k4.metric("CA sell-in",        f"{total_ca:,.0f} €".replace(",", " "))
k5.metric("Conversion",        f"{conv_global} %")
k6.metric("Magasins actifs",   f"{total_stores}")

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

# ── TAB 1 : CROISEMENT ───────────────────────────────────────────────────────
with tab1:
    st.markdown("## 📊 Synthèse par Magasin")

    if df_summary.empty:
        st.info("Connectez vos sources de données (voir sidebar) pour afficher le croisement.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            top_e = df_summary[df_summary["Essais"] > 0].head(15)
            fig = px.bar(
                top_e, x="Magasin", y="Essais",
                text="Essais", title="Essais par Magasin",
                color="Conv. %", color_continuous_scale="Blues",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_tickangle=-35, plot_bgcolor="white",
                              paper_bgcolor="white", height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            top_ca = df_summary[df_summary["CA (€)"] > 0].head(15)
            if not top_ca.empty:
                fig = px.bar(
                    top_ca, x="Magasin", y="CA (€)",
                    text="CA (€)", title="CA Sell-in par Magasin (Shopify)",
                    color_discrete_sequence=["#22c55e"],
                )
                fig.update_traces(texttemplate="%{y:,.0f}€", textposition="outside")
                fig.update_layout(xaxis_tickangle=-35, plot_bgcolor="white",
                                  paper_bgcolor="white", height=380)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune donnée Shopify pour les magasins trouvés.")

        # Scatter corrélation
        df_plot = df_summary[(df_summary["Essais"] > 0) | (df_summary["Commandes"] > 0)].copy()
        if not df_plot.empty:
            df_plot["_size"] = df_plot["CA (€)"].clip(lower=100)
            fig_s = px.scatter(
                df_plot, x="Essais", y="Commandes",
                text="Magasin",
                size="_size",
                title="Corrélation Essais × Commandes  (taille = CA)",
                color="Conv. %", color_continuous_scale="RdYlGn",
                hover_data={"Essais": True, "Commandes": True, "CA (€)": True, "_size": False},
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
                "Articles":  st.column_config.NumberColumn("Articles 🚲"),
            },
        )

# ── TAB 2 : ESSAIS ────────────────────────────────────────────────────────────
with tab2:
    if df_essais.empty:
        st.warning(
            "⚠️ Données essais non disponibles.\n\n"
            "**Étape requise :** déployez `CyclableAPI.gs` dans Google Sheets "
            "et ajoutez l'URL dans les secrets (voir SETUP.md)."
        )
    else:
        st.markdown(f"## 🔬 {len(df_essais)} essais enregistrés")

        stores_e = ["Tous"] + sorted(df_essais["store"].dropna().unique().tolist()) \
                   if "store" in df_essais.columns else ["Tous"]
        sel_s = st.selectbox("Filtrer par magasin", stores_e, key="filt_essais")
        df_e = df_essais if sel_s == "Tous" else df_essais[df_essais["store"] == sel_s]

        c1, c2 = st.columns(2)
        with c1:
            if "store" in df_e.columns:
                by_s = df_e.groupby("store").size().reset_index(name="Essais").sort_values("Essais")
                fig = px.bar(by_s, x="Essais", y="store", orientation="h",
                             text="Essais", title="Essais par Magasin",
                             color_discrete_sequence=["#3b82f6"])
                fig.update_traces(textposition="outside")
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=400)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            if "date" in df_e.columns:
                dated = df_e.dropna(subset=["date"]).copy()
                if not dated.empty:
                    dated["mois"] = dated["date"].dt.to_period("M").astype(str)
                    by_m = dated.groupby("mois").size().reset_index(name="Essais")
                    fig = px.bar(by_m, x="mois", y="Essais", text="Essais",
                                 title="Essais par Mois",
                                 color_discrete_sequence=["#6366f1"])
                    fig.update_traces(textposition="outside")
                    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=400)
                    st.plotly_chart(fig, use_container_width=True)

        cols_show = [c for c in ["date", "store", "product", "dept", "cp"] if c in df_e.columns]
        st.dataframe(
            df_e[cols_show].sort_values("date", ascending=False) if "date" in cols_show else df_e[cols_show],
            use_container_width=True, hide_index=True,
        )

# ── TAB 3 : SHOPIFY ──────────────────────────────────────────────────────────
with tab3:
    if df_orders.empty:
        st.warning(
            "⚠️ Données Shopify non disponibles.\n\n"
            "**Étape requise :** ajoutez votre `shopify_token` dans les secrets (voir SETUP.md)."
        )
    else:
        st.markdown(f"## 🛒 {len(df_orders)} commandes Shopify")

        stores_o = ["Tous"] + sorted(df_orders["store_raw"].dropna().unique().tolist())
        sel_o = st.selectbox("Filtrer par magasin", stores_o, key="filt_shop")
        df_o = df_orders if sel_o == "Tous" else df_orders[df_orders["store_raw"] == sel_o]

        c1, c2 = st.columns(2)
        with c1:
            by_s = (
                df_o.groupby("store_raw")
                .agg(CA=("ca", "sum"), Commandes=("order_id", "count"))
                .reset_index()
                .sort_values("CA")
            )
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
                fig.update_layout(title="CA Mensuel", plot_bgcolor="white",
                                  paper_bgcolor="white", height=420)
                st.plotly_chart(fig, use_container_width=True)

        show_cols = [c for c in ["created_at", "store_raw", "order_name", "ca", "nb_items", "currency"] if c in df_o.columns]
        st.dataframe(
            df_o[show_cols].sort_values("created_at", ascending=False),
            use_container_width=True, hide_index=True,
        )

# ── TAB 4 : ÉVOLUTION MENSUELLE ──────────────────────────────────────────────
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
            Commandes=("order_id", "count"), CA=("ca", "sum")
        ).reset_index()

    if has_e and has_o:
        merged = pd.merge(monthly_e, monthly_o, on="mois", how="outer").fillna(0).sort_values("mois")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=merged["mois"], y=merged["Essais"],
            name="Essais", marker_color="rgba(59,130,246,.75)",
            text=merged["Essais"].astype(int), textposition="outside",
        ))
        fig.add_trace(go.Bar(
            x=merged["mois"], y=merged["Commandes"],
            name="Commandes", marker_color="rgba(34,197,94,.75)",
            text=merged["Commandes"].astype(int), textposition="outside",
        ))
        fig.update_layout(
            title="Essais vs Commandes par Mois",
            barmode="group", plot_bgcolor="white", paper_bgcolor="white", height=400,
        )
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
        fig2.update_layout(
            title="CA Cumulé Shopify (€)",
            plot_bgcolor="white", paper_bgcolor="white", height=350,
        )
        st.plotly_chart(fig2, use_container_width=True)

    elif has_e:
        st.info("Connectez Shopify pour voir l'évolution croisée.")
        fig = px.bar(monthly_e, x="mois", y="Essais", text="Essais",
                     title="Essais par Mois", color_discrete_sequence=["#3b82f6"])
        fig.update_traces(textposition="outside")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    elif has_o:
        st.info("Connectez Google Sheets pour voir l'évolution croisée.")

    else:
        st.info("Connectez vos deux sources de données pour afficher l'évolution mensuelle.")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🚲 Cyclable × Elwing Dashboard · Sources : Shopify + Google Sheets · Accès réservé")
