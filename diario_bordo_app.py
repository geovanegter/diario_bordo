# diario_bordo_app.py
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import requests

# tentativa de usar streamlit_js_eval; se não instalado, fallback gracefully
try:
    from streamlit_js_eval import streamlit_js_eval
    JS_AVAILABLE = True
except Exception:
    JS_AVAILABLE = False

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="Diário de Bordo Comercial", layout="wide", page_icon="📘")

# -------------------------
# CSS (theme light, hover, minimal)
# -------------------------
st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-family: Inter, sans-serif; background: #F5F6FA; }
    .block-container { padding-top: 12px; padding-left: 18px; padding-right: 18px; }

    /* Header card */
    .header-card {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        border-radius: 12px;
        background: #ffffff;
        border: 1px solid #ECEFF3;
        box-shadow: 0 6px 18px rgba(15,15,15,0.04);
        margin-bottom: 14px;
    }
    .avatar { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid #f0f0f0; }
    .user-title { font-size: 18px; font-weight: 700; margin:0; }
    .user-sub { margin:0; color:#6b7280; font-size:13px; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #E8EBF0; padding-top: 18px; }

    .menu-btn {
        display:block;
        width:100%;
        text-align:left;
        padding:10px 12px;
        margin-bottom:8px;
        border-radius:10px;
        background:transparent;
        border:1px solid transparent;
        color:#222;
        font-weight:600;
        cursor:pointer;
        transition: all .15s ease;
    }
    .menu-btn:hover { background: #F0F4FF; transform: translateX(4px); color: #1e40ff; }
    .menu-active { background:#1e40ff !important; color: #fff !important; border-color:#1e40ff !important; }

    .card { background:#FFFFFF; border-radius:12px; padding:16px; border:1px solid #ECEFF3; box-shadow: 0 6px 14px rgba(12,12,12,0.03); }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Helpers: file reading safe
# -------------------------
DATA_DIR = Path("dados")
DATA_DIR.mkdir(exist_ok=True)

def read_excel_safe(path: Path, default_cols=None):
    if path.exists():
        try:
            return pd.read_excel(path)
        except Exception as e:
            st.error(f"Erro lendo {path.name}: {e}")
            return pd.DataFrame(columns=default_cols or [])
    else:
        return pd.DataFrame(columns=default_cols or [])

VENDAS_COLS = [
    "representante","cliente","cidade","colecao","marca","bairro","cep",
    "qtd_pecas","valor_vendido","desconto","prazo"
]

# -------------------------
# Load data safely
# -------------------------
usuarios_df = read_excel_safe(DATA_DIR / "usuarios.xlsx", default_cols=["email","senha","representante"])
vendas_df = read_excel_safe(DATA_DIR / "vendas.xlsx", default_cols=VENDAS_COLS)
metas_df  = read_excel_safe(DATA_DIR / "metas_colecao.xlsx", default_cols=["representante","colecao","meta_vendas","meta_clientes"])

# normalize column names (strip)
usuarios_df.columns = usuarios_df.columns.str.strip()
vendas_df.columns = vendas_df.columns.str.strip()
metas_df.columns = metas_df.columns.str.strip()

# -------------------------
# Session state init
# -------------------------
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

# -------------------------
# Auth
# -------------------------
def autenticar(email: str, senha: str):
    if usuarios_df.empty:
        return None
    # ensure strings and strip
    usuarios_df["email"] = usuarios_df["email"].astype(str).str.strip()
    usuarios_df["senha"] = usuarios_df["senha"].astype(str).str.strip()
    filtro = (usuarios_df["email"].str.lower() == str(email).lower()) & (usuarios_df["senha"].astype(str) == str(senha))
    matched = usuarios_df[filtro]
    if len(matched) == 1:
        # return row as dict
        row = matched.iloc[0].to_dict()
        # ensure representative exists
        if "representante" not in row or pd.isna(row.get("representante")):
            row["representante"] = row.get("email", "")
        return row
    return None

# -------------------------
# Geolocation helpers
# -------------------------
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
    except Exception:
        return None
    return None

def obter_coords_via_js():
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

# -------------------------
# Login screen
# -------------------------
if not st.session_state.logado:
    st.markdown("<div style='max-width:720px;margin:28px auto;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center'>🔐 Diário de Bordo Comercial</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#6b7280'>Faça login com e-mail e senha</p>", unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        user = autenticar(email.strip(), senha.strip())
        if user:
            st.session_state.logado = True
            st.session_state.user = user
            # try to get coords once
            coords = obter_coords_via_js()
            if coords:
                st.session_state.coords = coords
                loc = reverse_geocode(coords[0], coords[1])
                st.session_state.local_text = loc
            st.experimental_rerun()
        else:
            st.error("E-mail ou senha inválidos.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# -------------------------
# After login: header + sidebar (left)
# -------------------------
user = st.session_state.user
representante = str(user.get("representante") or user.get("email") or "Usuário")

# If coords not set yet, try once (non-blocking)
if st.session_state.coords is None:
    coords = obter_coords_via_js()
    if coords:
        st.session_state.coords = coords
        st.session_state.local_text = reverse_geocode(coords[0], coords[1])

local_text = st.session_state.local_text or "Localização não disponível"

# header card
avatar_src = f"https://ui-avatars.com/api/?name={representante}&background=ffffff&color=1e293b&bold=true"
st.markdown(
    f"""
    <div class="header-card">
        <img src="{avatar_src}" class="avatar" />
        <div>
            <p class="user-title">👋 Bem-vindo, {representante}</p>
            <p class="user-sub">Você está em: <strong>{local_text}</strong></p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar menu (left)
st.sidebar.markdown("## Navegação")
menu_items = ["Dashboard", "Clientes", "Cidades", "Ranking", "Dossiê Cliente"]
for key in menu_items:
    if st.sidebar.button(key):
        st.session_state.pagina = key

st.sidebar.write("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# -------------------------
# MAIN: pages
# -------------------------
pagina = st.session_state.pagina

# Work on safe copies
vendas = vendas_df.copy()
metas = metas_df.copy()

# Normalize representative columns to string
if "representante" in vendas.columns:
    vendas["representante"] = vendas["representante"].astype(str)
if "representante" in metas.columns:
    metas["representante"] = metas["representante"].astype(str)

# Helper: safe numeric column
def get_numeric_series(df, col):
    if col in df.columns:
        try:
            return pd.to_numeric(df[col], errors="coerce").fillna(0)
        except:
            return pd.Series([0]*len(df))
    else:
        return pd.Series([0]*len(df))

# PAGE: Dashboard
if pagina == "Dashboard":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📊 Dashboard")

    # filter by representative
    if "representante" in vendas.columns:
        vendas_rep = vendas[vendas["representante"].str.lower() == representante.lower()].copy()
    else:
        vendas_rep = pd.DataFrame(columns=vendas.columns)

    total_vendido = get_numeric_series(vendas_rep, "valor_vendido").sum() if not vendas_rep.empty else 0.0
    clientes_unicos = vendas_rep["cliente"].nunique() if "cliente" in vendas_rep.columns else 0

    # detect meta_vendas column in metas
    meta_vendas_col = None
    for c in metas.columns:
        if "meta" in c.lower() and "vendas" in c.lower():
            meta_vendas_col = c
            break
    if meta_vendas_col is None:
        for c in metas.columns:
            if "meta" in c.lower():
                meta_vendas_col = c
                break

    meta_vendas = 0.0
    if meta_vendas_col and "representante" in metas.columns:
        try:
            meta_vendas = float(metas[metas["representante"].str.lower() == representante.lower()][meta_vendas_col].sum())
        except:
            meta_vendas = 0.0

    # meta clients
    meta_clientes_col = None
    for c in metas.columns:
        if "cliente" in c.lower() and "meta" in c.lower():
            meta_clientes_col = c
            break
    meta_clientes = 0
    if meta_clientes_col and "representante" in metas.columns:
        try:
            meta_clientes = int(metas[metas["representante"].str.lower() == representante.lower()][meta_clientes_col].sum())
        except:
            meta_clientes = 0

    # days remaining in month
    today = datetime.now().date()
    next_month = today.replace(day=28) + timedelta(days=4)
    last_day = (next_month - timedelta(days=next_month.day)).day
    days_remaining = max(last_day - today.day + 1, 1)

    falta_vender = max(meta_vendas - total_vendido, 0.0)
    venda_por_dia = falta_vender / days_remaining if days_remaining > 0 else falta_vender

    falta_clientes = max(meta_clientes - clientes_unicos, 0)
    clientes_por_dia = falta_clientes / days_remaining if days_remaining > 0 else falta_clientes

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='card'><h4>Total vendido</h4><h2>R$ {total_vendido:,.2f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h4>Meta vendas</h4><h2>R$ {meta_vendas:,.2f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h4>Falta vender (R$/dia)</h4><h2>R$ {venda_por_dia:,.2f}</h2></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='card'><h4>Clientes / dia</h4><h2>{clientes_por_dia:.1f}</h2></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write(" ")
    st.subheader("Últimos registros (exibição simplificada)")
    if not vendas_rep.empty:
        # display last N by insertion order (no date column)
        last_n = vendas_rep.tail(10).iloc[::-1]
        st.dataframe(last_n.reset_index(drop=True), use_container_width=True)
    else:
        st.info("Nenhuma venda encontrada para esse representante.")

# PAGE: Clientes
elif pagina == "Clientes":
    st.subheader("👥 Clientes")
    if ventas := vendas:  # just to use variable name ventas locally
        pass
    if vendas.empty or "cliente" not in vendas.columns:
        st.info("Nenhum dado de clientes disponível.")
    else:
        clientes_rep = vendas[vendas["representante"].str.lower() == representante.lower()]["cliente"].dropna().unique() if "representante" in vendas.columns else []
        st.write(f"Total de clientes (únicos): {len(clientes_rep)}")
        if len(clientes_rep) > 0:
            st.dataframe(pd.DataFrame({"cliente": clientes_rep}), use_container_width=True)

# PAGE: Cidades
elif pagina == "Cidades":
    st.subheader("🏙️ Vendas por Cidade")
    if vendas.empty or "cidade" not in vendas.columns or "valor_vendido" not in vendas.columns:
        st.info("Dados de cidades ou valores não disponíveis.")
    else:
        vendas_rep = vendas[vendas["representante"].str.lower() == representante.lower()] if "representante" in vendas.columns else pd.DataFrame()
        if vendas_rep.empty:
            st.info("Nenhuma venda para esse representante.")
        else:
            agg = vendas_rep.groupby("cidade", dropna=True)["valor_vendido"].sum().sort_values(ascending=False)
            st.dataframe(agg.reset_index().rename(columns={"valor_vendido":"total_vendido"}), use_container_width=True)

# PAGE: Ranking (top clients by revenue)
elif pagina == "Ranking":
    st.subheader("🏆 Ranking de Clientes (por valor vendido)")
    if vendas.empty or "cliente" not in vendas.columns or "valor_vendido" not in vendas.columns:
        st.info("Dados insuficientes para ranking.")
    else:
        vendas_rep = vendas[vendas["representante"].str.lower() == representante.lower()] if "representante" in vendas.columns else pd.DataFrame()
        if vendas_rep.empty:
            st.info("Nenhuma venda para esse representante.")
        else:
            rank = vendas_rep.groupby("cliente", dropna=True)["valor_vendido"].sum().sort_values(ascending=False)
            st.dataframe(rank.reset_index().rename(columns={"valor_vendido":"total_vendido"}).head(50), use_container_width=True)

# PAGE: Dossiê Cliente
elif pagina == "Dossiê Cliente" or pagina == "Dossiê Cliente":
    st.subheader("📁 Dossiê do Cliente")
    if vendas.empty or "cliente" not in vendas.columns:
        st.info("Nenhum dado de clientes disponível.")
    else:
        # list of unique clients for this rep
        clients = vendas[vendas["representante"].str.lower() == representante.lower()]["cliente"].dropna().unique() if "representante" in vendas.columns else []
        cliente_sel = st.selectbox("Selecione o cliente", options=clients if len(clients)>0 else ["-"])
        if cliente_sel and cliente_sel != "-":
            df_client = vendas[(vendas["representante"].str.lower() == representante.lower()) & (vendas["cliente"] == cliente_sel)]
            if df_client.empty:
                st.info("Nenhuma venda registrada para esse cliente.")
            else:
                st.markdown(f"### Histórico de vendas — {cliente_sel}")
                st.dataframe(df_client.reset_index(drop=True), use_container_width=True)
                total_cli = get_numeric_series(df_client, "valor_vendido").sum()
                st.metric("Total vendido para o cliente", f"R$ {total_cli:,.2f}")

else:
    st.info("Página não encontrada. Selecione uma opção no menu lateral.")
