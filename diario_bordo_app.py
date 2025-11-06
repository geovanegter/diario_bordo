import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="📘 Diário de Bordo Comercial", layout="wide")

# -------------------------------
# Funções
# -------------------------------

@st.cache_data
def carregar_planilhas():
    return {
        "usuarios": pd.read_excel("dados/usuarios.xlsx"),
        "vendas": pd.read_excel("dados/vendas.xlsx"),
        "metas_colecao": pd.read_excel("dados/metas_colecao.xlsx"),
        "meta_semanal": pd.read_excel("dados/meta_semanal.xlsx")
    }

def autenticar(email, senha):
    usuarios = dfs["usuarios"]
    usuarios["email"] = usuarios["email"].astype(str)
    usuarios["senha"] = usuarios["senha"].astype(str)
    
    user = usuarios[
        (usuarios["email"].str.lower() == email.lower()) &
        (usuarios["senha"] == senha)
    ]

    if len(user) == 1:
        return user.iloc[0].to_dict()
    return None

def calcular_ticket_medio(rep):
    metas = dfs["metas_colecao"]
    meta_row = metas[metas["representante"] == rep]
    if meta_row.empty:
        return 0
    total_venda = meta_row["meta_vendas"].sum()
    total_clientes = meta_row["meta_clientes"].sum()
    return total_venda / total_clientes if total_clientes > 0 else 0

# -------------------------------
# Carrega planilhas
# -------------------------------
dfs = carregar_planilhas()

# -------------------------------
# LOGIN
# -------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = None

if not st.session_state.logado:
    st.title("🔐 Diário de Bordo — Login")
    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviar = st.form_submit_button("Entrar")

        if enviar:
            user = autenticar(email, senha)
            if user:
                st.session_state.logado = True
                st.session_state.user = user
            else:
                st.error("❌ Usuário ou senha incorretos!")
                st.stop()

# -------------------------------
# USUÁRIO LOGADO
# -------------------------------
user = st.session_state.user
representante = user["email"]  # ou se tiver campo "representante"

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "",
    ["Dashboard", "Clientes", "Ranking", "Dossiê Cliente"]
)
if st.sidebar.button("Logout"):
    st.session_state.logado = False
    st.session_state.user = None
    st.experimental_rerun()

# -------------------------------
# DASHBOARD PRINCIPAL
# -------------------------------
st.markdown(f"## 👋 Olá, {user['nome']}")
st.markdown(f"Você está em: 📍 Localização atual (em breve com geolocalização)")

vendas = dfs["vendas"]
metas_colecao = dfs["metas_colecao"]
meta_semanal = dfs["meta_semanal"]

# Filtra vendas do representante
vendas_rep = vendas[vendas["representante"] == representante]

# Calcula progresso de cada coleção
st.subheader("🎯 Progresso das metas por coleção")
for _, row in metas_colecao[metas_colecao["representante"] == representante].iterrows():
    colecao = row["colecao"]
    meta_valor = row["meta_vendas"]
    vendido = vendas_rep[vendas_rep["colecao"] == colecao]["valor_vendido"].sum()
    progresso = vendido / meta_valor if meta_valor > 0 else 0
    st.markdown(f"**Coleção {colecao}** — Você atingiu {progresso*100:.1f}% da meta")
    st.progress(progresso)

# -------------------------------
# Metas semanais
# -------------------------------
st.subheader("📅 Meta da semana")
hoje = datetime.today().date()
week_row = meta_semanal[meta_semanal["colecao"].isin(
    metas_colecao[metas_colecao["representante"] == representante]["colecao"]
)]
if not week_row.empty:
    for _, row in week_row.iterrows():
        semana_inicio = pd.to_datetime(row["semana_inicio"]).date()
        semana_fim = pd.to_datetime(row["semana_fim"]).date()
        percentual_meta = row["percentual_da_meta"]

        # Calcula vendas na semana
        vendas_semana = vendas_rep[
            (pd.to_datetime(vendas_rep["data"]) >= semana_inicio) &
            (pd.to_datetime(vendas_rep["data"]) <= semana_fim)
        ]["valor_vendido"].sum()

        st.markdown(f"**Coleção {row['colecao']}** — {percentual_meta}% da meta da semana")
        st.progress(min(vendas_semana / (percentual_meta / 100 * metas_colecao.loc[metas_colecao['colecao'] == row['colecao'], 'meta_vendas'].values[0]),1.0))

        # Clientes a atender
        ticket_medio = calcular_ticket_medio(representante)
        clientes_restantes = max((percentual_meta / 100 * metas_colecao.loc[metas_colecao['colecao'] == row['colecao'], 'meta_vendas'].values[0]) / ticket_medio - vendas_semana / ticket_medio,0)
        st.markdown(f"Vendas semanais realizadas: R$ {vendas_semana:,.2f}")
        st.markdown(f"Clientes a atender nesta semana: {clientes_restantes:.0f}")






