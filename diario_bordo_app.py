import streamlit as st
import pandas as pd
from pathlib import Path

# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================
st.set_page_config(page_title="Diário de Bordo", layout="wide")

EXCEL_FILE = "diario_bordo_dados.xlsx"  # <-- ajuste aqui se estiver em outro caminho

# ============================================
# FUNÇÃO PARA CARREGAR PLANILHAS
# ============================================
@st.cache_data
def load_excel():
    if not Path(EXCEL_FILE).exists():
        st.error(f"❌ Não encontrei o arquivo: {EXCEL_FILE}")
        return None

    xls = pd.ExcelFile(EXCEL_FILE)

    data = {
        "usuarios": pd.read_excel(xls, "usuarios"),
        "planos": pd.read_excel(xls, "planos"),
        "colecoes": pd.read_excel(xls, "colecoes"),
        "clientes": pd.read_excel(xls, "clientes"),
        "semana": pd.read_excel(xls, "semana")
    }
    return data


data = load_excel()
if data is None:
    st.stop()


# ============================================
# AUTENTICAÇÃO
# ============================================
def autenticar(email, senha):
    usuarios = data["usuarios"]

    user = usuarios[
        (usuarios["email"] == email) & (usuarios["senha"] == senha)
    ]

    if len(user) == 1:
        d = user.iloc[0].to_dict()
        return d
    return None


# cria session state
if "user" not in st.session_state:
    st.session_state.user = None


# ============================================
# TELA DE LOGIN
# ============================================
if st.session_state.user is None:
    st.title("🔐 Diário de Bordo — Login")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            user = autenticar(email, senha)
            if user:
                st.session_state.user = user  # salva o dicionário inteiro
                st.success(f"Bem-vindo(a), {user['representante']}!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")

    st.stop()


# ============================================
# APLICATIVO PRINCIPAL
# ============================================
user = st.session_state.user
rep = user["representante"]

st.sidebar.title("📌 Navegação")
pagina = st.sidebar.radio(
    "",
    ["Visão geral", "Meus Objetivos", "Clientes", "Dossiê Cliente"]
)

st.sidebar.markdown("---")
st.sidebar.write(f"👤 **{rep}**")
if st.sidebar.button("Sair"):
    st.session_state.user = None
    st.rerun()


# ============================================
# VISÃO GERAL (Dashboard)
# ============================================
if pagina == "Visão geral":
    st.title(f"🚀 Bem-vindo(a), {rep}!")

    planos_df = data["planos"]
    colecoes_df = data["colecoes"]

    planos_rep = planos_df[planos_df["representante"] == rep].copy()
    colecao_atual = colecoes_df[colecoes_df["ativa"] == "sim"].iloc[0]

    col1, col2 = st.columns(2)

    # --- Bloco vendas coleção ---
    meta_vendas = int(planos_rep["meta_vendas"].sum())
    vendas_realizadas = int(planos_rep["vendas_realizadas"].sum())
    perc_vendas = vendas_realizadas / meta_vendas if meta_vendas > 0 else 0

    with col1:
        st.subheader("📊 Meta de vendas da coleção")
        st.progress(perc_vendas)
        st.metric("Meta de vendas", f"R$ {meta_vendas:,.0f}".replace(",", "."))
        st.metric("Vendido", f"R$ {vendas_realizadas:,.0f}".replace(",", "."))
        st.metric("Falta vender", f"R$ {(meta_vendas - vendas_realizadas):,.0f}".replace(",", "."))

    # --- Bloco clientes coleção ---
    clientes_meta = int(planos_rep["meta_clientes"].sum())
    clientes_atendidos = int(planos_rep["clientes_atendidos"].sum())
    perc_clientes = clientes_atendidos / clientes_meta if clientes_meta > 0 else 0

    with col2:
        st.subheader("🙋 Clientes atendidos na coleção")
        st.progress(perc_clientes)
        st.metric("Meta clientes", clientes_meta)
        st.metric("Atendidos", clientes_atendidos)
        st.metric("Faltam", clientes_meta - clientes_atendidos)


# ============================================
# MEUS OBJETIVOS
# =========================
