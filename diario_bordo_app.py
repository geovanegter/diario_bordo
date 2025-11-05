# diario_bordo_app.py
import streamlit as st
import pandas as pd
from pathlib import Path

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="Diário de Bordo", layout="wide")
DATA_DIR = Path("dados")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "usuarios.xlsx"
VENDAS_FILE = DATA_DIR / "vendas.xlsx"
METAS_FILE = DATA_DIR / "metas.xlsx"
COLECOES_FILE = DATA_DIR / "colecoes.xlsx"

# -------------------------
# Helpers para carregar planilhas (robusto)
# -------------------------
@st.cache_data
def load_excel(path: Path, expected_cols=None):
    if not path.exists():
        return pd.DataFrame(columns=(expected_cols or []))
    df = pd.read_excel(path, engine="openpyxl")
    df.columns = [c.strip() for c in df.columns]
    return df

def normalize_users_df(df: pd.DataFrame):
    # garante colunas mínimas e tipos string
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ["email", "senha", "nome", "representante"]:
        if col not in df.columns:
            df[col] = ""
    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df["senha"] = df["senha"].astype(str).str.strip()
    df["nome"] = df["nome"].astype(str).str.strip()
    df["representante"] = df["representante"].astype(str).str.strip()
    return df

# -------------------------
# Carregar dados
# -------------------------
users_df = load_excel(USERS_FILE)
users_df = normalize_users_df(users_df)

vendas_df = load_excel(VENDAS_FILE)
# padroniza nomes das colunas de vendas
vendas_df.columns = [c.strip().lower() for c in vendas_df.columns]

metas_df = load_excel(METAS_FILE)
metas_df.columns = [c.strip().lower() for c in metas_df.columns]

colecoes_df = load_excel(COLECOES_FILE)
colecoes_df.columns = [c.strip().lower() for c in colecoes_df.columns]

# -------------------------
# Autenticação (usa users_df)
# -------------------------
def authenticate(email: str, senha: str):
    if users_df.empty:
        return None
    email = (email or "").strip().lower()
    senha = (senha or "").strip()
    match = users_df[
        (users_df["email"] == email) &
        (users_df["senha"] == senha)
    ]
    if not match.empty:
        row = match.iloc[0]
        return {"email": row["email"], "nome": row.get("nome", ""), "representante": row.get("representante", "")}
    return None

# -------------------------
# LOGIN (sem st.form)
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🔐 Diário de Bordo — Login")
    st.write("Faça login com seu e-mail e senha (planilha: dados/usuarios.xlsx).")

    email_input = st.text_input("E-mail")
    senha_input = st.text_input("Senha", type="password")

if st.button("Entrar"):
    user = authenticate(email_input, senha_input)
    if user:
        st.session_state.user = user
        st.success(f"Bem-vindo(a), {user.get('nome') or user['email']}!")
        st.rerun()
        else:
            st.error("E-mail ou senha incorretos. Verifique a planilha dados/usuarios.xlsx.")

    # Mostrar debug opcional (remova em produção)
    with st.expander("DEBUG: Usuários carregados (apenas para teste)"):
        st.dataframe(users_df[["email","senha","nome","representante"]].astype(str))
    st.stop()

# -------------------------
# USUÁRIO LOGADO — UI PRINCIPAL
# -------------------------
user = st.session_state.user
rep = user.get("representante", "")
st.sidebar.markdown(f"**Logado como:** {user.get('nome') or user['email']}  \n**Rep:** {rep}")

# -------------------------
# Menu lateral com botões (controlado por session_state)
# -------------------------
if "view" not in st.session_state:
    st.session_state.view = "Visão Geral"

st.sidebar.title("Navegação")
if st.sidebar.button("Visão geral"):
    st.session_state.view = "Visão Geral"
if st.sidebar.button("Meus objetivos"):
    st.session_state.view = "Meus Objetivos"
if st.sidebar.button("Clientes"):
    st.session_state.view = "Clientes"
if st.sidebar.button("Dossiê Cliente"):
    st.session_state.view = "Dossiê Cliente"
st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.view = "Visão Geral"
    st.experimental_rerun()

view = st.session_state.view

# -------------------------
# Função: barra de progresso custom (texto + st.progress)
# -------------------------
def progresso_card(valor, meta, label_prefix="", fmt_val=lambda v: f"R$ {v:,.2f}"):
    pct = (valor / meta) * 100 if meta and meta > 0 else 0
    st.markdown(f"**{label_prefix} {pct:.1f}%**")
    st.progress(min(pct/100, 1.0))
    st.write(f"{fmt_val(valor)} / {fmt_val(meta)}")
    return pct

# -------------------------
# Helpers para pegar metas/coleção do representante
# -------------------------
def get_colecao_vigente(rep_code):
    if colecoes_df.empty:
        return None
    row = colecoes_df[colecoes_df["representante"] == rep_code]
    if not row.empty and "colecao_vigente" in row.columns:
        return row.iloc[0]["colecao_vigente"]
    # fallback: se coluna tiver outro nome como 'colecao'
    if not row.empty and "colecao" in row.columns:
        return row.iloc[0]["colecao"]
    return None

def get_metas(rep_code, colecao):
    if metas_df.empty:
        return None
    row = metas_df[(metas_df["representante"] == rep_code) & (metas_df.get("colecao", "") == colecao)]
    # fallback: se o filtro por coleção não funcionar, tenta só por representante
    if row.empty:
        row = metas_df[metas_df["representante"] == rep_code]
    if row.empty:
        return None
    row = row.iloc[0]
    return {
        "meta_vendas": float(row.get("meta_vendas", 0) or 0),
        "meta_clientes": int(row.get("meta_clientes", 0) or 0),
        "colecao": row.get("colecao", colecao)
    }

# -------------------------
# Views
# -------------------------
def view_dashboard():
    st.title("Visão Geral")
    st.markdown(f"### Olá, **{user.get('nome') or user.get('email')}**")

    colecao = get_colecao_vigente(rep) or "—"
    st.markdown(f"**Coleção vigente:** {colecao}")

    metas = get_metas(rep, colecao)
    if metas is None:
        st.warning("Metas não encontradas para este representante. Verifique dados em dados/metas.xlsx.")
        return

    # filtra vendas por representante e coleção (se houver coluna colecao)
    df_rep = vendas_df.copy()
    if "representante" in df_rep.columns:
        df_rep = df_rep[df_rep["representante"] == rep]
    if "colecao" in df_rep.columns:
        df_rep = df_rep[df_rep["colecao"] == colecao]

    total_vendas = float(df_rep["valor_vendido"].sum()) if "valor_vendido" in df_rep.columns else 0.0
    total_clientes = int(df_rep["cliente"].nunique()) if "cliente" in df_rep.columns else 0

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Vendas da Coleção")
        progresso_card(total_vendas, metas["meta_vendas"], label_prefix="Atingimento de vendas -")
        st.metric("Vendido", f"R$ {total_vendas:,.2f}")
        st.metric("Meta (vendas)", f"R$ {metas['meta_vendas']:,.2f}")
        st.metric("Falta vender", f"R$ {max(metas['meta_vendas'] - total_vendas, 0):,.2f}")

    with c2:
        st.subheader("Clientes")
        progresso_card(total_clientes, metas["meta_clientes"], label_prefix="Atingimento clientes -", fmt_val=lambda v: f"{v}")
        st.metric("Clientes atendidos", total_clientes)
        st.metric("Meta (clientes)", metas["meta_clientes"])
        st.metric("Faltam atender", max(metas["meta_clientes"] - total_clientes, 0))

    st.markdown("---")
    st.subheader("Resumo da semana")
    st.write("Aqui você verá clientes prioritários, follow-ups e ações sugeridas (módulo a evoluir).")

def view_objetivos():
    st.title("Meus Objetivos")
    st.info("Página em construção — objetivos e KPIs semanais aparecerão aqui.")

def view_clientes():
    st.title("Clientes")
    df = vendas_df.copy()
    if "representante" in df.columns:
        df = df[df["representante"] == rep]
    if df.empty:
        st.info("Nenhuma venda/cliente encontrado para seu código de representante.")
    else:
        st.dataframe(df)

def view_dossie():
    st.title("Dossiê Cliente")
    st.info("Escolha um cliente na página 'Clientes' para ver o dossiê (em desenvolvimento).")

# -------------------------
# Roteamento
# -------------------------
if view == "Visão Geral":
    view_dashboard()
elif view == "Meus Objetivos":
    view_objetivos()
elif view == "Clientes":
    view_clientes()
elif view == "Dossiê Cliente":
    view_dossie()

