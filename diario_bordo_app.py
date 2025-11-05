import streamlit as st
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------
# CONFIGURAÇÕES DO STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="Diário de Bordo", layout="wide")

DATA_DIR = Path("dados")
DATA_DIR.mkdir(exist_ok=True)

USUARIOS_FILE = DATA_DIR / "usuarios.xlsx"
VENDAS_FILE = DATA_DIR / "vendas.xlsx"
METAS_FILE = DATA_DIR / "metas.xlsx"

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
def load_planilha(path, colunas_esperadas):
    if not path.exists():
        return pd.DataFrame(columns=colunas_esperadas)
    df = pd.read_excel(path, engine="openpyxl")
    df.columns = [c.strip().lower() for c in df.columns]
    return df


usuarios_df = load_planilha(USUARIOS_FILE, ["representante", "email", "senha"])
vendas_df = load_planilha(VENDAS_FILE, ["representante", "cliente", "valor_vendido"])
metas_df = load_planilha(METAS_FILE, ["representante", "colecao", "meta_vendas", "meta_clientes"])


# ---------------------------------------------------------
# AUTENTICAÇÃO
# ---------------------------------------------------------
def autenticar(email, senha):
    match = usuarios_df[
        (usuarios_df["email"] == email) & 
        (usuarios_df["senha"] == senha)
    ]
    if match.empty:
        return None
    return match.iloc[0]["representante"]


# ---------------------------------------------------------
# COMPONENTES GERAIS
# ---------------------------------------------------------
def barra_progresso(valor, meta, label):
    pct = (valor / meta) * 100 if meta > 0 else 0
    st.markdown(f"**{label}: {pct:.1f}% atingido**")
    st.progress(min(pct / 100, 1.0))


# ---------------------------------------------------------
# PÁGINAS
# ---------------------------------------------------------
def pagina_dashboard(rep):
    df_vendas = vendas_df[vendas_df["representante"] == rep]

    # META da coleção
    meta = metas_df[metas_df["representante"] == rep].reset_index(drop=True)
    if meta.empty:
        st.warning("⚠️ Não há metas cadastradas para esse representante.")
        return

    colecao = meta.loc[0, "colecao"]
    meta_vendas = meta.loc[0, "meta_vendas"]
    meta_clientes = meta.loc[0, "meta_clientes"]

    total_vendas = df_vendas["valor_vendido"].sum()
    total_clientes = df_vendas["cliente"].nunique()

    st.title(f"🚀 Coleção vigente: **{colecao}**")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Vendas da Coleção")
        barra_progresso(total_vendas, meta_vendas, "Meta de vendas")
        st.metric("Vendido até agora", f"R$ {total_vendas:,.2f}")
        st.metric("Meta", f"R$ {meta_vendas:,.2f}")
        st.metric("Falta vender", f"R$ {max(meta_vendas - total_vendas, 0):,.2f}")

    with col2:
        st.subheader("👥 Clientes")
        barra_progresso(total_clientes, meta_clientes, "Meta de clientes")
        st.metric("Clientes atendidos", total_clientes)
        st.metric("Meta de clientes", meta_clientes)
        st.metric("Faltam atender", max(meta_clientes - total_clientes, 0))


def pagina_objetivos(rep):
    st.title("🎯 Meus Objetivos")
    st.write("Em breve... (definição de metas por produto, região, etc.)")


def pagina_clientes(rep):
    st.title("📋 Clientes atendidos na coleção")
    df = vendas_df[vendas_df["representante"] == rep]
    if df.empty:
        st.info("Nenhuma venda registrada ainda.")
    else:
        st.dataframe(df)


def pagina_dossie(rep):
    st.title("🧠 Dossiê do Cliente")
    st.write("Módulo em construção...")


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
if "rep" not in st.session_state:
    st.title("🔐 Diário de Bordo — Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        usuario = autenticar(email, senha)
        if usuario:
            st.session_state["rep"] = usuario
            st.rerun()
        else:
            st.error("Email ou senha inválidos.")
    st.stop()


# ---------------------------------------------------------
# APÓS LOGIN
# ---------------------------------------------------------
rep = st.session_state["rep"]

# MENU LATERAL COM BOTÕES
st.sidebar.title("📌 Navegação")

if st.sidebar.button("Visão geral"):
    st.session_state["view"] = "dashboard"

if st.sidebar.button("Meus objetivos"):
    st.session_state["view"] = "objetivos"

if st.sidebar.button("Clientes"):
    st.session_state["view"] = "clientes"

if st.sidebar.button("Dossiê Cliente"):
    st.session_state["view"] = "dossie"

# Se não tiver nada selecionado ainda, abrir dashboard
view = st.session_state.get("view", "dashboard")

# ROTAS
if view == "dashboard":
    pagina_dashboard(rep)
elif view == "objetivos":
    pagina_objetivos(rep)
elif view == "clientes":
    pagina_clientes(rep)
elif view == "dossie":
    pagina_dossie(rep)

