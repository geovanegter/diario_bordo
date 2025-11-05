import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📘 Diário de Bordo Comercial", layout="wide")

# -------------------------------
# Funções
# -------------------------------

@st.cache_data
def carregar_planilhas():
    return {
        "usuarios": pd.read_excel("dados/usuarios.xlsx"),
        "vendas": pd.read_excel("dados/vendas.xlsx"),
        "colecoes": pd.read_excel("dados/colecoes.xlsx"),
        "metas": pd.read_excel("dados/metas_colecao.xlsx"),
        "planos": pd.read_excel("dados/planos_acoes.xlsx"),
    }

def autenticar(email, senha):
    usuarios = dfs["usuarios"]

    # Garante que colunas sejam string
    usuarios["email"] = usuarios["email"].astype(str)
    usuarios["senha"] = usuarios["senha"].astype(str)

    user = usuarios[
        (usuarios["email"].str.lower() == email.lower()) &
        (usuarios["senha"] == senha)
    ]

    if len(user) == 1:
        return user.iloc[0].to_dict()  # já retorna como dict
    return None

# -------------------------------
# Carrega planilhas
# -------------------------------
dfs = carregar_planilhas()

# -------------------------------
# Sessão inicial
# -------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = None
    st.session_state.pagina_atual = "Dashboard"  # página padrão

# -------------------------------
# LOGIN
# -------------------------------
if not st.session_state.logado:
    st.title("🔐 Diário de Bordo — Login")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviar = st.form_submit_button("Entrar")

        if enviar:
            user = autenticar(email, senha)

            if user is not None:
                st.session_state.logado = True
                st.session_state.user = user
                st.experimental_rerun()
            else:
                st.error("❌ Usuário ou senha inválidos!")
                st.stop()

# -------------------------------
# TELA PRINCIPAL (pós login)
# -------------------------------
user = st.session_state.get("user", None)

if not user or not isinstance(user, dict):
    st.error("❌ Usuário não autenticado. Faça login novamente.")
    st.stop()

representante = user.get("representante", "Não definido")
nome_usuario = user.get("nome", "Usuário")

st.sidebar.title(f"👋 Olá, {nome_usuario}")
st.sidebar.write(f"Representante: **{representante}**")

# Define página com persistência
pagina = st.sidebar.radio(
    "Navegar",
    ["Dashboard", "Registrar visita", "Plano de Ação", "Coleções / Metas"],
    index=["Dashboard", "Registrar visita", "Plano de Ação", "Coleções / Metas"].index(
        st.session_state.get("pagina_atual", "Dashboard")
    )
)
st.session_state["pagina_atual"] = pagina

# -------------------------------
# DASHBOARD
# -------------------------------
if pagina == "Dashboard":
    st.title("📊 Dashboard Comercial")

    vendas = dfs["vendas"]
    metas = dfs["metas"]

    vendas_rep = vendas[vendas["representante"] == representante]
    metas_rep = metas[metas["representante"] == representante]

    total_vendido = vendas_rep["valor"].sum()
    meta_total = metas_rep["meta"].sum()

    progresso = total_vendido / meta_total if meta_total > 0 else 0

    st.subheader("🎯 Progresso Geral da Meta")
    st.progress(progresso)

    st.metric("Total vendido", f"R$ {total_vendido:,.2f}".replace(",", "."))
    st.metric("Meta do período", f"R$ {meta_total:,.2f}".replace(",", "."))

# -------------------------------
# REGISTRAR VISITA
# -------------------------------
elif pagina == "Registrar visita":
    st.title("📝 Registro de Visitas")

    vendas = dfs["vendas"]
    colecoes = dfs["colecoes"]

    with st.form("form_visita"):
        cliente = st.text_input("Cliente")
        colecao = st.selectbox("Coleção", colecoes["colecao"].unique())
        valor = st.number_input("Valor do pedido (R$)", step=100.0)
        enviado = st.form_submit_button("Salvar registro")

        if enviado:
            novo = pd.DataFrame([{
                "data": datetime.now(),
                "representante": representante,
                "cliente": cliente,
                "colecao": colecao,
                "valor": valor,
            }])
            dfs["vendas"] = pd.concat([dfs["vendas"], novo], ignore_index=True)
            dfs["vendas"].to_excel("dados/vendas.xlsx", index=False)
            st.success("✅ Visita registrada!")

# -------------------------------
# PLANOS DE AÇÃO
# -------------------------------
elif pagina == "Plano de Ação":
    st.title("🚀 Plano de Ação Comercial")

    planos = dfs["planos"]
    planos_rep = planos[planos["responsavel"] == representante]

    st.table(planos_rep)

# -------------------------------
# COLEÇÕES / METAS
# -------------------------------
elif pagina == "Coleções / Metas":
    st.title("🏆 Metas por Coleção")

    metas = dfs["metas"]
    vendas = dfs["vendas"]

    metas_rep = metas[metas["representante"] == representante]

    for _, row in metas_rep.iterrows():
        colecao = row["colecao"]
        meta = row["meta"]

        vendido = vendas[
            (vendas["representante"] == representante) &
            (vendas["colecao"] == colecao)
        ]["valor"].sum()

        progresso = vendido / meta if meta > 0 else 0

        st.write(f"### {colecao}")
        st.progress(progresso)
        st.write(f"Vendido: **R$ {vendido:,.2f}** de R$ {meta:,.2f}".replace(",", "."))

# -------------------------------
# LOGOUT
# -------------------------------
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.logado = False
    st.experimental_rerun()
