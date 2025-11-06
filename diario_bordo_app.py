# diario_bordo_app.py
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import requests

# Geolocation helper lib (must be installed)
from streamlit_js_eval import streamlit_js_eval

# -----------------------------
# Config page
# -----------------------------
st.set_page_config(page_title="Diário de Bordo Comercial", layout="wide", page_icon="📘")

# -----------------------------
# CSS - visual moderno, light
# -----------------------------
st.markdown(
    """
    <style>
    /* Global */
    html, body, [class*="css"] { font-family: Inter, sans-serif; background: #F5F6FA; }
    .block-container { padding-top: 12px; padding-left: 16px; padding-right: 16px; }

    /* Header card */
    .header-card {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 18px;
        border-radius: 12px;
        background: #ffffff;
        border: 1px solid #ECEFF3;
        box-shadow: 0 6px 18px rgba(15, 15, 15, 0.04);
        margin-bottom: 18px;
    }
    .avatar {
        width: 64px; height: 64px; border-radius: 50%;
        object-fit: cover;
        border: 2px solid #f0f0f0;
    }
    .user-title { font-size: 18px; font-weight: 700; margin:0; }
    .user-sub { margin:0; color:#6c6c6c; font-size:14px; }

    /* Sidebar menu buttons */
    section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E8EBF0; padding-top: 20px; }
    .menu-btn {
        display: block;
        width: 100%;
        text-align: left;
        padding: 10px 12px;
        margin-bottom: 8px;
        border-radius: 10px;
        background: transparent;
        border: 1px solid transparent;
        color: #222;
        font-weight: 600;
        cursor: pointer;
        transition: all .15s ease;
    }
    .menu-btn:hover { background: #F0F4FF; transform: translateX(4px); color: #1e40ff; }
    .menu-active { background: #1e40ff !important; color: #fff !important; border-color: #1e40ff !important; }

    /* Cards */
    .card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #ECEFF3;
        box-shadow: 0 6px 14px rgba(12,12,12,0.03);
    }

    /* Small helpers */
    .muted { color: #6b7280; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Utilities: file load & safe columns
# -----------------------------
DATA_DIR = Path("dados")
DATA_DIR.mkdir(exist_ok=True)

def read_excel_safe(path: Path, default_cols=None):
    """Tenta ler planilha, se não existir retorna df com default_cols (se fornecido)."""
    if path.exists():
        try:
            return pd.read_excel(path)
        except Exception as e:
            st.error(f"Erro lendo {path.name}: {e}")
            return pd.DataFrame(columns=default_cols or [])
    else:
        return pd.DataFrame(columns=default_cols or [])

# Expected columns for vendas if created
VENDAS_COLS = [
    "data","representante","cliente","cidade","colecao","marca","bairro","cep",
    "qtd_pecas","valor_vendido","desconto","prazo"
]

# -----------------------------
# Carrega planilhas (robusto)
# -----------------------------
usuarios_df = read_excel_safe(DATA_DIR / "usuarios.xlsx", default_cols=["email","senha","representante"])
vendas_df = read_excel_safe(DATA_DIR / "vendas.xlsx", default_cols=VENDAS_COLS)
metas_df   = read_excel_safe(DATA_DIR / "metas_colecao.xlsx", default_cols=["representante","colecao","meta_vendas","meta_clientes"])

# Normaliza col names (strip)
usuarios_df.columns = usuarios_df.columns.str.strip()
vendas_df.columns = vendas_df.columns.str.strip()
metas_df.columns = metas_df.columns.str.strip()

# -----------------------------
# Session state initialization (prevent AttributeError)
# -----------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"
if "localizacao_text" not in st.session_state:
    st.session_state.localizacao_text = None
if "coords" not in st.session_state:
    st.session_state.coords = None

# -----------------------------
# Auth function (email + senha)
# -----------------------------
def autenticar(email: str, senha: str):
    if usuarios_df.empty:
        return None
    # ensure strings
    usuarios_df["email"] = usuarios_df["email"].astype(str)
    usuarios_df["senha"] = usuarios_df["senha"].astype(str)
    filtro = (usuarios_df["email"].str.lower() == str(email).lower()) & (usuarios_df["senha"].astype(str) == str(senha))
    matched = usuarios_df[filtro]
    if len(matched) == 1:
        # Return dict with keys as in sheet
        row = matched.iloc[0].to_dict()
        # ensure representative present
        if "representante" not in row or pd.isna(row.get("representante")):
            row["representante"] = row.get("email", "")
        return row
    return None

# -----------------------------
# Geocoding (reverse) via Nominatim
# -----------------------------
def reverse_geocode(lat: float, lon: float):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
        r = requests.get(url, headers={"User-Agent": "diario-bordo-app"})
        if r.status_code == 200:
            j = r.json()
            addr = j.get("address", {})
            city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
            state = addr.get("state") or addr.get("region")
            if city and state:
                return f"{city} / {state}"
            if city:
                return city
            if state:
                return state
            return j.get("display_name", None)
    except Exception:
        return None
    return None

# -----------------------------
# Login screen
# -----------------------------
if not st.session_state.logado:
    st.markdown("<div style='max-width:700px;margin:40px auto;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;margin-bottom:6px;'>🔐 Diário de Bordo Comercial</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#6b7280;margin-top:0;margin-bottom:18px;'>Faça login com seu e-mail e senha</p>", unsafe_allow_html=True)

    with st.form("login_form"):
        email_input = st.text_input("E-mail")
        senha_input = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        user = autenticar(email_input, senha_input)
        if user:
            st.session_state.logado = True
            st.session_state.user = user
            # set pagina default
            st.session_state.pagina = "Dashboard"
            st.experimental_rerun()
        else:
            st.error("Email ou senha inválidos. Verifique e tente novamente.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# -----------------------------
# Helper: attempt to get coords from browser (once)
# -----------------------------
def obter_coords_browser():
    # Use streamlit_js_eval to execute navigator.geolocation
    try:
        coords = streamlit_js_eval(
            js_expression="""
                await new Promise((resolve, reject) => {
                  navigator.geolocation.getCurrentPosition(
                    (pos) => resolve(pos.coords.latitude + ',' + pos.coords.longitude),
                    (err) => resolve(null),
                    {enableHighAccuracy: true, timeout: 5000}
                  );
                });
            """,
            key="get_coords_once",
        )
        if coords:
            lat_str, lon_str = coords.split(",")
            return float(lat_str), float(lon_str)
    except Exception:
        return None
    return None

# If not yet obtained, try (non-blocking)
if st.session_state.coords is None:
    coords = obter_coords_browser()
    if coords:
        st.session_state.coords = coords
        lat, lon = coords
        loc = reverse_geocode(lat, lon)
        st.session_state.localizacao_text = loc

# -----------------------------
# Build header card (top)
# -----------------------------
user = st.session_state.user
# representative used as display name (per your choice)
representante = user.get("representante") if user.get("representante") else user.get("email")

avatar_src = f"https://ui-avatars.com/api/?name={representante}&background=ffffff&color=1e293b&bold=true"

local_text = st.session_state.localizacao_text or "Localização não disponível"

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

# -----------------------------
# Sidebar navigation (left)
# -----------------------------
st.sidebar.markdown("## Navegação")
menu_items = ["Dashboard", "Metas", "Registrar Visita", "Vendas", "Clientes"]
for item in menu_items:
    # render button and set page
    if st.sidebar.button(item):
        st.session_state.pagina = item

st.sidebar.write("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# Visual note: we can't inject per-button classes easily, but the CSS hover gives good UX.

# -----------------------------
# MAIN AREA: route pages
# -----------------------------
pagina = st.session_state.pagina

# Safe accessor to vendas_df / metas_df
vendas = vendas_df.copy()
metas = metas_df.copy()

# Normalize string columns to avoid case issues when filtering representative
if "representante" in vendas.columns:
    vendas["representante"] = vendas["representante"].astype(str)
if "representante" in metas.columns:
    metas["representante"] = metas["representante"].astype(str)

# Dashboard page
if pagina == "Dashboard":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📊 Dashboard")

    # Filter by representative (case-insensitive)
    rep_mask = vendas["representante"].str.lower() == str(representante).lower() if "representante" in vendas.columns else pd.Series([False]*len(vendas))
    vendas_rep = vendas[rep_mask].copy()

    total_vendido = vendas_rep["valor_vendido"].sum() if "valor_vendido" in vendas_rep.columns else 0.0
    clientes_atendidos = vendas_rep["cliente"].nunique() if "cliente" in vendas_rep.columns else 0

    # detect meta vendas column (prefer explicit name 'meta_vendas')
    meta_col = None
    for c in metas.columns:
        if "meta" in c.lower() and "vendas" in c.lower():
            meta_col = c
            break
    # fallback: any column with 'meta' in name will be used
    if meta_col is None:
        for c in metas.columns:
            if "meta" in c.lower():
                meta_col = c
                break

    meta_vendas = 0
    if meta_col and "representante" in metas.columns:
        meta_vendas = metas[metas["representante"].str.lower() == str(representante).lower()][meta_col].sum()
        try:
            meta_vendas = float(meta_vendas)
        except:
            meta_vendas = 0.0

    # meta clients detection
    meta_clientes_col = None
    for c in metas.columns:
        if "cliente" in c.lower() and "meta" in c.lower():
            meta_clientes_col = c
            break
    meta_clientes = 0
    if meta_clientes_col and "representante" in metas.columns:
        meta_clientes = metas[metas["representante"].str.lower() == str(representante).lower()][meta_clientes_col].sum()
        try:
            meta_clientes = int(meta_clientes)
        except:
            meta_clientes = 0

    # Time calculations: remaining days in month (safe)
    hoje = datetime.now().date()
    # last day of current month
    next_month = hoje.replace(day=28) + timedelta(days=4)
    last_day = (next_month - timedelta(days=next_month.day)).day
    dias_restantes = max(last_day - hoje.day + 1, 1)

    falta_vender = max(meta_vendas - total_vendido, 0.0)
    venda_por_dia = falta_vender / dias_restantes if dias_restantes > 0 else falta_vender

    falta_clientes = max(meta_clientes - clientes_atendidos, 0)
    clientes_por_dia = falta_clientes / dias_restantes if dias_restantes > 0 else falta_clientes

    # show metrics in columns
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='card'><h4>Total vendido</h4><h2>R$ {total_vendido:,.2f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h4>Meta vendas</h4><h2>R$ {meta_vendas:,.2f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h4>Falta vender (R$ / dia)</h4><h2>R$ {venda_por_dia:,.2f}</h2></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='card'><h4>Clientes / dia</h4><h2>{clientes_por_dia:.1f}</h2></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write(" ")
    st.subheader("Últimas vendas registradas")
    if not vendas_rep.empty:
        # show last 10 rows
        st.dataframe(vendas_rep.sort_values("data", ascending=False).head(10), use_container_width=True)
    else:
        st.info("Nenhuma venda registrada para esse representante.")

# Metas page
elif pagina == "Metas":
    st.subheader("🏆 Metas e Coleções")
    if metas.empty:
        st.info("Planilha de metas vazia ou ausente.")
    else:
        metas_rep = metas[metas["representante"].str.lower() == str(representante).lower()] if "representante" in metas.columns else pd.DataFrame()
        if metas_rep.empty:
            st.info("Nenhuma meta cadastrada para esse representante.")
        else:
            st.dataframe(metas_rep, use_container_width=True)

# Registrar Visita page
elif pagina == "Registrar Visita":
    st.subheader("📝 Registrar Visita")
    with st.form("form_visita"):
        col1, col2 = st.columns(2)
        cliente = col1.text_input("Nome do cliente")
        cidade = col1.text_input("Cidade")
        colecao = col2.text_input("Coleção")
        valor = col2.number_input("Valor vendido (R$)", min_value=0.0, step=10.0)
        salvar = st.form_submit_button("Salvar registro")

    # Show small map or saved location if available
    if st.session_state.coords:
        lat, lon = st.session_state.coords
        st.caption(f"Local atual (lat, lon): {lat:.5f}, {lon:.5f}")
    else:
        st.caption("Localização do navegador não detectada ou negada.")

    if salvar:
        # Ensure vendas_df has expected columns
        for c in VENDAS_COLS:
            if c not in vendas_df.columns:
                vendas_df[c] = pd.NA

        novo = {
            "data": datetime.now(),
            "representante": representante,
            "cliente": cliente,
            "cidade": cidade,
            "colecao": colecao,
            "marca": "",
            "bairro": "",
            "cep": "",
            "qtd_pecas": 0,
            "valor_vendido": float(valor),
            "desconto": 0,
            "prazo": ""
        }
        vendas_df = vendas_df.append(novo, ignore_index=True) if hasattr(vendas_df, "append") else pd.concat([vendas_df, pd.DataFrame([novo])], ignore_index=True)

        # Save to excel
        try:
            vendas_df.to_excel(DATA_DIR / "vendas.xlsx", index=False)
            st.success("Visita registrada e salva com sucesso.")
        except Exception as e:
            st.error(f"Erro ao salvar arquivo de vendas: {e}")

# Vendas page
elif pagina == "Vendas":
    st.subheader("📄 Todas as vendas")
    if vendas.empty:
        st.info("Nenhum registro de vendas disponível.")
    else:
        st.dataframe(vendas.sort_values("data", ascending=False), use_container_width=True)

# Clientes page
elif pagina == "Clientes":
    st.subheader("👥 Clientes")
    if vendas.empty or "cliente" not in vendas.columns:
        st.info("Nenhum dado de clientes disponível.")
    else:
        cl = vendas["cliente"].dropna().unique().tolist()
        st.write(f"Total de clientes: {len(cl)}")
        st.dataframe(pd.DataFrame({"cliente": cl}), use_container_width=True)

# default fallback
else:
    st.write("Página não encontrada. Selecione no menu lateral.")

# End of app
