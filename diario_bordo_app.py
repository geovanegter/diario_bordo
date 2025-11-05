import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------
st.set_page_config(page_title="Diário de Bordo", layout="wide")

# -------------------------------------------------
# FUNÇÃO DE LOGIN / LEITURA PLANILHAS DE USUÁRIOS
# -------------------------------------------------
@st.cache_data
def load_users():
    return pd.read_excel("dados/usuarios.xlsx")

def authenticate(email, senha):
    users = load_users()
    user = users[(users["email"] == email) & (users["senha"].astype(str) == str(senha))]
    if len(user) == 1:
        return True, user.iloc[0]["representante"]
    return False, None


# ---------------------------------------------------------------------------------
# CARREGAR PLANILHAS DE METAS / COLEÇÕES / VENDAS
# ---------------------------------------------------------------------------------
@st.cache_data
def load_metas():
    return pd.read_excel("dados/metas.xlsx")

@st.cache_data
def load_colecoes():
    return pd.read_excel("dados/colecoes.xlsx")

@st.cache_data
def load_vendas():
    return pd.read_excel("dados/vendas.xlsx")


# ======================
# TELA DE LOGIN CORRIGIDA
# ======================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    st.markdown(
        """
        <h1 style="text-align:center;">🔐 Diário de Bordo — Login</h1>
        """,
        unsafe_allow_html=True
    )

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        valid, rep = authenticate(email, senha)
        if valid:
            st.session_state.login = True
            st.session_state.user_email = email
            st.session_state.representante = rep
            st.rerun()
        else:
            st.error("❌ E-mail ou senha incorretos.")

    st.stop()


# Se o usuário estiver logado ----------------------------------------------------
rep = st.session_state.representante
user_email = st.session_state.user_email

# MENU LATERAL
menu = st.sidebar.radio(
    "Navegação",
    ["Visão Geral", "Meus Objetivos", "Clientes", "Dossiê Cliente"]
)


# 📊 CARREGA PLANILHAS
df_metas = load_metas()
df_colecoes = load_colecoes()
df_vendas = load_vendas()

# Define coleção vigente
colecao = df_colecoes[df_colecoes["representante"] == rep]["colecao_vigente"].iloc[0]

# Filtra metas do representante
meta_rep = df_metas[(df_metas["representante"] == rep) & (df_metas["colecao"] == colecao)].iloc[0]
meta_vendas = meta_rep["meta_vendas"]
meta_clientes = meta_rep["meta_clientes"]

# Filtra vendas da coleção vigente
vendas_rep = df_vendas[(df_vendas["representante"] == rep) & (df_vendas["colecao"] == colecao)]

total_vendido = vendas_rep["valor_vendido"].sum()
clientes_atendidos = vendas_rep["cliente"].nunique()

pct_vendas = (total_vendido / meta_vendas) * 100
pct_clientes = (clientes_atendidos / meta_clientes) * 100

# ======================
# TELA: VISÃO GERAL
# ======================
if menu == "Visão Geral":

    st.markdown(f"### 👋 Olá, **{rep}**")
    st.markdown(f"📌 Coleção vigente: **{colecao}**")

    col1, col2 = st.columns(2)

    # -------- BLOCO META DE VENDAS --------
    with col1:
        st.subheader("💰 Meta de Vendas da Coleção")

        fig = px.pie(
            values=[total_vendido, max(meta_vendas - total_vendido, 0)],
            names=["Vendido", "Falta vender"],
            hole=0.5
        )
        st.plotly_chart(fig, use_container_width=True)

        st.metric("Vendas realizadas", f"R$ {total_vendido:,.2f}")
        st.metric("Meta da coleção", f"R$ {meta_vendas:,.2f}")
        st.metric("Falta vender", f"R$ {max(meta_vendas - total_vendido, 0):,.2f}")

    # -------- BLOCO META DE CLIENTES --------
    with col2:
        st.subheader("👥 Meta de Clientes da Coleção")

        fig = px.pie(
            values=[clientes_atendidos, max(meta_clientes - clientes_atendidos, 0)],
            names=["Clientes atendidos", "Faltam"],
            hole=0.5
        )
        st.plotly_chart(fig, use_container_width=True)

        st.metric("Clientes atendidos", clientes_atendidos)
        st.metric("Meta da coleção", meta_clientes)
        st.metric("Faltam atender", max(meta_clientes - clientes_atendidos, 0))


# ======================
# TELA: MEUS OBJETIVOS
# ======================
elif menu == "Meus Objetivos":
    st.header("🎯 Meus Objetivos")
    st.info("Tela em construção — vamos definir objetivos por coleção, ranking e desafios semanais.")

# ======================
# TELA: CLIENTES
# ======================
elif menu == "Clientes":
    st.header("📋 Minha carteira de clientes")
    st.dataframe(vendas_rep)

# ======================
# TELA: DOSSIÊ DO CLIENTE
# ======================
elif menu == "Dossiê Cliente":
    st.header("🧠 Dossiê do Cliente")
    cliente = st.selectbox("Selecione um cliente", vendas_rep["cliente"].unique())
    df_cli = vendas_rep[vendas_rep["cliente"] == cliente]
    st.write(df_cli)


