# diario_bordo_app.py
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import math
import requests

# try import for geolocation via browser
try:
    from streamlit_js_eval import streamlit_js_eval
    JS_AVAILABLE = True
except Exception:
    JS_AVAILABLE = False

# ---------------- config page ----------------
st.set_page_config(page_title="Diário de Bordo", layout="wide", page_icon="📘")

# ---------------- CSS (light, minimal, hover) ----------------
st.markdown("""
<style>
html, body, [class*="css"] { font-family: Inter, sans-serif; background: #F5F6FA; }
.block-container { padding-top: 12px; padding-left:16px; padding-right:16px; }

/* Header */
.header-card {
  display:flex; align-items:center; gap:16px;
  padding:16px; border-radius:12px;
  background:#fff; border:1px solid #ECEFF3;
  box-shadow: 0 6px 18px rgba(15,15,15,0.04);
  margin-bottom:14px;
}
.avatar { width:64px; height:64px; border-radius:50%; object-fit:cover; border:2px solid #f0f0f0; }
.user-title { font-size:18px; font-weight:700; margin:0; }
.user-sub { margin:0; color:#6b7280; font-size:13px; }

/* Sidebar styling */
section[data-testid="stSidebar"] { background:#fff; border-right:1px solid #E8EBF0; padding-top:18px; }
.menu-btn {
  display:block; width:100%; text-align:left; padding:10px 12px; margin-bottom:8px; border-radius:10px;
  background:transparent; border:1px solid transparent; color:#222; font-weight:600; cursor:pointer; transition:all .15s;
}
.menu-btn:hover { background:#F0F4FF; transform:translateX(4px); color:#1e40ff; }
.menu-active { background:#1e40ff !important; color:#fff !important; border-color:#1e40ff !important; }

/* Card */
.card { background:#fff; border-radius:12px; padding:16px; border:1px solid #ECEFF3; box-shadow:0 6px 14px rgba(12,12,12,0.03); }

</style>
""", unsafe_allow_html=True)

# ---------------- Helpers ----------------
DATA_DIR = Path("dados")
DATA_DIR.mkdir(exist_ok=True)

def read_excel_safe(path: Path, default_cols=None):
    """Leia Excel com fallback para colunas padrão se arquivo ausente."""
    if path.exists():
        try:
            return pd.read_excel(path)
        except Exception as e:
            st.error(f"Erro lendo {path.name}: {e}")
            return pd.DataFrame(columns=default_cols or [])
    else:
        return pd.DataFrame(columns=default_cols or [])

# expected columns
VENDAS_COLS = ["representante","cliente","cidade","colecao","marca","bairro","cep","qtd_pecas","valor_vendido","desconto","prazo","data"]
USUARIOS_COLS = ["email","senha","representante"]
META_COLECAO_COLS = ["representante","colecao","meta_vendas","meta_clientes"]
META_SEMANAL_COLS = ["colecao","semana_inicio","semana_fim","percentual_da_meta"]

# load sheets
usuarios_df = read_excel_safe(DATA_DIR / "usuarios.xlsx", default_cols=USUARIOS_COLS)
vendas_df    = read_excel_safe(DATA_DIR / "vendas.xlsx", default_cols=VENDAS_COLS)
meta_colecao = read_excel_safe(DATA_DIR / "meta_colecao.xlsx", default_cols=META_COLECAO_COLS)
meta_semanal = read_excel_safe(DATA_DIR / "meta_semanal.xlsx", default_cols=META_SEMANAL_COLS)

# normalize column names (strip)
usuarios_df.columns = usuarios_df.columns.str.strip()
vendas_df.columns = vendas_df.columns.str.strip()
meta_colecao.columns = meta_colecao.columns.str.strip()
meta_semanal.columns = meta_semanal.columns.str.strip()

# ensure data column parsed to datetime if exists
if "data" in vendas_df.columns and not vendas_df["data"].empty:
    # try parsing with dayfirst True
    try:
        vendas_df["data"] = pd.to_datetime(vendas_df["data"], dayfirst=True, errors='coerce')
    except Exception:
        vendas_df["data"] = pd.to_datetime(vendas_df["data"], errors='coerce')

# session init
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"
if "coords" not in st.session_state:
    st.session_state.coords = None
if "local_text" not in st.session_state:
    st.session_state.local_text = None

# Authentication
def autenticar(email, senha):
    if usuarios_df.empty:
        return None
    usuarios_df["email"] = usuarios_df["email"].astype(str).str.strip()
    usuarios_df["senha"] = usuarios_df["senha"].astype(str).str.strip()
    mask = (usuarios_df["email"].str.lower() == str(email).lower()) & (usuarios_df["senha"].astype(str) == str(senha))
    matched = usuarios_df[mask]
    if len(matched) == 1:
        row = matched.iloc[0].to_dict()
        if "representante" not in row or pd.isna(row.get("representante")):
            row["representante"] = row.get("email")
        return row
    return None

# geolocation helpers
def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
        r = requests.get(url, headers={"User-Agent":"diario-bordo-app"})
        if r.status_code == 200:
            j = r.json()
            addr = j.get("address", {})
            city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
            state = addr.get("state") or addr.get("region")
            if city and state:
                return f"{city} / {state}"
            return city or state or j.get("display_name")
    except:
        return None
    return None

def obter_coords_via_js_once():
    if not JS_AVAILABLE:
        return None
    try:
        coords = streamlit_js_eval(
            js_expression="""
            await new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    pos => resolve(pos.coords.latitude + ',' + pos.coords.longitude),
                    err => resolve(null),
                    { enableHighAccuracy: true, timeout: 5000 }
                );
            });
            """,
            key="get_coords_once",
        )
        if coords:
            lat, lon = coords.split(",")
            return float(lat), float(lon)
    except Exception:
        return None
    return None

# ---------- Login screen ----------
if not st.session_state.logado:
    st.markdown("<div style='max-width:720px;margin:28px auto;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center'>🔐 Diário de Bordo Comercial</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#6b7280'>Acesse com seu e-mail e senha</p>", unsafe_allow_html=True)

    with st.form("login_form"):
        email_in = st.text_input("E-mail")
        senha_in = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        user = autenticar(email_in.strip(), senha_in.strip())
        if user:
            st.session_state.logado = True
            st.session_state.user = user
            # attempt to get coords once
            coords = obter_coords_via_js_once()
            if coords:
                st.session_state.coords = coords
                loc = reverse_geocode(coords[0], coords[1])
                st.session_state.local_text = loc
            st.experimental_rerun()
        else:
            st.error("E-mail ou senha inválidos.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ---------- After login: header and sidebar ----------
user = st.session_state.user
representante = str(user.get("representante") or user.get("email") or "Usuário")

# try coords if not already
if st.session_state.coords is None:
    coords_try = obter_coords_via_js_once()
    if coords_try:
        st.session_state.coords = coords_try
        st.session_state.local_text = reverse_geocode(coords_try[0], coords_try[1])

local_text = st.session_state.local_text or "Localização não disponível"

avatar_src = f"https://ui-avatars.com/api/?name={representante}&background=ffffff&color=1e293b&bold=true"
st.markdown(f"""
<div class="header-card">
  <img src="{avatar_src}" class="avatar" />
  <div>
    <p class="user-title">👋 Bem-vindo, {representante}</p>
    <p class="user-sub">Você está em: <strong>{local_text}</strong></p>
  </div>
</div>
""", unsafe_allow_html=True)

# Sidebar menu (left) with icons + text
st.sidebar.markdown("## Navegação")
menu_items = [
    ("Dashboard","📊"),
    ("Clientes","👥"),
    ("Ranking","🏆"),
    ("Dossiê Cliente","📁"),
]
for name, emoji in menu_items:
    label = f"{emoji}  {name}"
    if st.sidebar.button(label):
        st.session_state.pagina = name

st.sidebar.write("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# ----------------- Main pages -----------------
pagina = st.session_state.pagina

# safe copies
vendas = vendas_df.copy()
metas = meta_colecao.copy()
meta_week_table = meta_semanal.copy()

# normalize representative column
if "representante" in vendas.columns:
    vendas["representante"] = vendas["representante"].astype(str)

# helper numeric
def to_numeric_series(df, col):
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(0)
    return pd.Series([0]*len(df))

# ---------- Dashboard ----------
if pagina == "Dashboard":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📊 Dashboard — visão rápida")

    # pick collection: get collections available for this rep (from meta_colecao)
    rep_meta = metas[metas["representante"].astype(str).str.lower() == representante.lower()] if not metas.empty else pd.DataFrame()
    collections = rep_meta["colecao"].dropna().unique().tolist() if not rep_meta.empty else []
    if not collections:
        # fallback: list unique collections in vendas for rep (if metas missing)
        if "colecao" in vendas.columns:
            col_list = vendas[vendas["representante"].str.lower() == representante.lower()]["colecao"].dropna().unique().tolist()
            collections = col_list
    if not collections:
        st.info("Nenhuma coleção encontrada (cadastre meta_colecao.xlsx).")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    colecao_atual = st.selectbox("Coleção ativa", collections, index=0)

    # meta for collection (per representative)
    meta_row = metas[
        (metas["representante"].astype(str).str.lower() == representante.lower()) &
        (metas["colecao"] == colecao_atual)
    ] if not metas.empty else pd.DataFrame()

    meta_vendas = 0.0
    meta_clientes = 0
    if not meta_row.empty:
        # prefer column names exactly meta_vendas and meta_clientes (as you confirmed)
        if "meta_vendas" in meta_row.columns:
            try:
                meta_vendas = float(meta_row["meta_vendas"].sum())
            except:
                meta_vendas = 0.0
        if "meta_clientes" in meta_row.columns:
            try:
                meta_clientes = int(meta_row["meta_clientes"].sum())
            except:
                meta_clientes = 0

    # total sold for that collection (across all dates)
    vendas_rep_coll = vendas[
        (vendas["representante"].astype(str).str.lower() == representante.lower()) &
        (vendas["colecao"] == colecao_atual)
    ] if "colecao" in vendas.columns else pd.DataFrame()

    total_vendido_coll = to_numeric_series(vendas_rep_coll, "valor_vendido").sum() if not vendas_rep_coll.empty else 0.0

    # percent of collection meta
    percent_meta = (total_vendido_coll / meta_vendas) if meta_vendas > 0 else 0.0

    # week calculation: find meta_semanal entry where today in [start,end] for this collection
    week_row = None
    if not meta_week_table.empty:
        # parse dates in table if needed (assume dd/mm/yyyy or ISO)
        if meta_week_table["semana_inicio"].dtype == object:
            meta_week_table["semana_inicio_parsed"] = pd.to_datetime(meta_week_table["semana_inicio"], dayfirst=True, errors='coerce')
        else:
            meta_week_table["semana_inicio_parsed"] = pd.to_datetime(meta_week_table["semana_inicio"], errors='coerce')
        if meta_week_table["semana_fim"].dtype == object:
            meta_week_table["semana_fim_parsed"] = pd.to_datetime(meta_week_table["semana_fim"], dayfirst=True, errors='coerce')
        else:
            meta_week_table["semana_fim_parsed"] = pd.to_datetime(meta_week_table["semana_fim"], errors='coerce')

        today_dt = pd.to_datetime(date.today())
        candidates = meta_week_table[meta_week_table["colecao"] == colecao_atual]
        # find row where today between start and end
        for _, r in candidates.iterrows():
            s = r.get("semana_inicio_parsed")
            e = r.get("semana_fim_parsed")
            if pd.notna(s) and pd.notna(e) and (s.date() <= today_dt.date() <= e.date()):
                week_row = r
                break

    # if week_row found compute weekly meta
    meta_semana_val = 0.0
    percent_semana = 0.0
    vendas_na_semana = 0.0
    if week_row is not None and meta_vendas > 0:
        perc = week_row.get("percentual_da_meta", 0)
        try:
            perc_num = float(str(perc).replace("%","").strip())/100.0 if isinstance(perc, str) and "%" in str(perc) else float(perc)
        except:
            perc_num = 0.0
        meta_semana_val = meta_vendas * perc_num
        # compute vendas in date range using vendas_df['data'] if present
        if "data" in vendas_rep_coll.columns and not vendas_rep_coll["data"].isnull().all():
            # ensure data parsed earlier; filter between s and e
            s = week_row["semana_inicio_parsed"]
            e = week_row["semana_fim_parsed"]
            if pd.notna(s) and pd.notna(e):
                mask = (vendas_rep_coll["data"] >= s) & (vendas_rep_coll["data"] <= e)
                vendas_na_semana = to_numeric_series(vendas_rep_coll[mask], "valor_vendido").sum()
            else:
                vendas_na_semana = 0.0
        else:
            # fallback: we can't filter by date, so use 0 for week sales
            vendas_na_semana = 0.0

        percent_semana = (vendas_na_semana / meta_semana_val) if meta_semana_val>0 else 0.0

    # ticket médio (Option A): use meta base (meta_vendas / meta_clientes) if meta_clientes>0
    if meta_clientes and meta_clientes > 0:
        ticket_medio = meta_vendas / meta_clientes
    else:
        # fallback ticket: compute from vendas_rep_coll
        ticket_medio = to_numeric_series(vendas_rep_coll, "valor_vendido").sum() / max(vendas_rep_coll["cliente"].nunique() if "cliente" in vendas_rep_coll.columns else 1, 1)

    # compute clients needed this week
    falta_semana = max(meta_semana_val - vendas_na_semana, 0.0)
    clientes_necessarios = math.ceil(falta_semana / ticket_medio) if ticket_medio>0 else None

    # SHOW: progress bar for collection meta
    st.write(f"Você atingiu **{percent_meta*100:.1f}%** da meta da coleção **{colecao_atual}**.")
    st.progress(min(percent_meta,1.0))
    st.write(" ")

    # show weekly info block
    st.markdown("<div style='display:flex;gap:12px;'>", unsafe_allow_html=True)
    st.markdown(f"<div class='card' style='flex:1;'><h4>🎯 Meta da semana</h4><p style='font-size:22px;margin:0;'>R$ {meta_semana_val:,.2f}</p><p class='muted'>Meta semanal definida pela tabela</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card' style='flex:1;'><h4>💵 Vendido esta semana</h4><p style='font-size:22px;margin:0;'>R$ {vendas_na_semana:,.2f}</p><p class='muted'>Período: {week_row.get('semana_inicio')} → {week_row.get('semana_fim') if week_row is not None else '-'}</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card' style='flex:1;'><h4>🔥 Falta vender (esta semana)</h4><p style='font-size:22px;margin:0;'>R$ {falta_semana:,.2f}</p></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write(" ")

    # cards summary with emojis
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='card'><h4>💰 Total vendido (coleção)</h4><h2>R$ {total_vendido_coll:,.2f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h4>🎯 Meta (coleção)</h4><h2>R$ {meta_vendas:,.2f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h4>📅 Falta vender (semana)</h4><h2>R$ {falta_semana:,.2f}</h2></div>", unsafe_allow_html=True)
    clientes_text = f"{clientes_necessarios}" if clientes_necessarios is not None else "—"
    c4.markdown(f"<div class='card'><h4>👥 Clientes esta semana</h4><h2>{clientes_text}</h2></div>", unsafe_allow_html=True)

    st.write(" ")
    st.subheader("Últimos registros (simples)")
    if not vendas_rep_coll.empty:
        # show last rows (no date ordering guaranteed if no date)
        last_n = vendas_rep_coll.tail(10).iloc[::-1]
        st.dataframe(last_n.reset_index(drop=True), use_container_width=True)
    else:
        st.info("Nenhuma venda registrada para essa coleção/representante.")

# ---------- Clientes ----------
elif pagina == "Clientes":
    st.subheader("👥 Clientes")
    if vendas.empty or "cliente" not in vendas.columns:
        st.info("Nenhum dado de clientes disponível.")
    else:
        clientes_rep = vendas[vendas["representante"].str.lower() == representante.lower()]["cliente"].dropna().unique().tolist()
        st.write(f"Total de clientes: **{len(clientes_rep)}**")
        if clientes_rep:
            st.dataframe(pd.DataFrame({"cliente": clientes_rep}), use_container_width=True)

# ---------- Ranking ----------
elif pagina == "Ranking":
    st.subheader("🏆 Ranking de Clientes (por valor vendido)")
    if vendas.empty or "cliente" not in vendas.columns or "valor_vendido" not in vendas.columns:
        st.info("Dados insuficientes para ranking.")
    else:
        vendas_rep = vendas[vendas["representante"].str.lower() == representante.lower()]
        if vendas_rep.empty:
            st.info("Nenhuma venda para esse representante.")
        else:
            rank = vendas_rep.groupby("cliente", dropna=True)["valor_vendido"].sum().sort_values(ascending=False)
            df_rank = rank.reset_index().rename(columns={"valor_vendido":"total_vendido"})
            df_rank["posicao"] = range(1, len(df_rank)+1)
            st.dataframe(df_rank[["posicao","cliente","total_vendido"]].head(50), use_container_width=True)

# ---------- Dossiê Cliente ----------
elif pagina == "Dossiê Cliente":
    st.subheader("📁 Dossiê do Cliente")
    if vendas.empty or "cliente" not in vendas.columns:
        st.info("Nenhum dado de clientes disponível.")
    else:
        clientes_rep = vendas[vendas["representante"].str.lower() == representante.lower()]["cliente"].dropna().unique().tolist()
        cliente_sel = st.selectbox("Selecione o cliente", options=clientes_rep if clientes_rep else ["-"])
        if cliente_sel and cliente_sel != "-":
            df_client = vendas[(vendas["representante"].str.lower() == representante.lower()) & (vendas["cliente"] == cliente_sel)]
            if df_client.empty:
                st.info("Nenhuma venda para esse cliente.")
            else:
                st.markdown(f"### Histórico — {cliente_sel}")
                st.dataframe(df_client.reset_index(drop=True), use_container_width=True)
                total_cli = to_numeric_series(df_client, "valor_vendido").sum()
                st.metric("Total vendido para o cliente", f"R$ {total_cli:,.2f}")

else:
    st.info("Selecione uma página no menu lateral.")


