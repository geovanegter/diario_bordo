import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# FUNÇÃO DE LOGIN
# ---------------------------
@st.cache_data
def carregar_usuarios():
    try:
        return pd.read_excel("usuarios.xlsx")
    except:
        st.error("⚠️ Arquivo usuarios.xlsx não encontrado no repositório.")
        return None

# ---------------------------
# FUNÇÃO PARA CARREGAR PLANILHA DE VENDAS
# ---------------------------
@st.cache_data
def carregar_vendas():
    try:
        return pd.read_excel("vendas.xlsx")
    except:
        st.error("⚠️ Arquivo vendas.xlsx não encontrado no repositório.")
        return None

# ---------------------------
# LOGIN
# ---------------------------
df_usuarios = carregar_usuarios()

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:

    st.title("🔐 Login — Diário de Bordo do Representante")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        user_match = df_usuarios[
            (df_usuarios["email"] == email) &
            (df_usuarios["senha"] == senha)
        ]

        if len(user_match) > 0:
            st.session_state.usuario_logado = user_match.iloc[0]["representante"]
            st.rerun()
        else:
            st.error("❌ Usuário ou senha inválidos.")
    st.stop()

# ---------------------------
# APÓS LOGIN
# ---------------------------
st.sidebar.success(f"✅ Usuário conectado: **{st.session_state.usuario_logado}**")

df_vendas = carregar_vendas()

# Filtrar vendas para o representante logado
df_rep = df_vendas[df_vendas["representante"] == st.session_state.usuario_logado]

st.title("📊 Diário de Bordo do Representante")

# ---------------------------
# PARÂMETROS DE META
# ---------------------------
st.sidebar.header("🎯 Metas da Semana")

meta_rs = st.sidebar.number_input("Meta da Semana (R$)", value=100000.0)
meta_clientes = st.sidebar.number_input("Meta de Clientes na Semana", value=20)

# ---------------------------
# CÁLCULOS
# ---------------------------
total_vendido = df_rep["valor_vendido"].sum()
clientes_atendidos = df_rep["cliente"].nunique()

pct_meta = total_vendido / meta_rs * 100 if meta_rs > 0 else 0
pct_clientes = clientes_atendidos / meta_clientes * 100 if meta_clientes > 0 else 0

# ---------------------------
# DASHBOARD
# ---------------------------
st.subheader("📌 Resumo da Semana")

col1, col2 = st.columns(2)

with col1:
    st.metric("Atingimento de Meta (R$)", f"R$ {total_vendido:,.2f}", f"{pct_meta:.1f}%")

with col2:
    st.metric("Clientes Atendidos", clientes_atendidos, f"{pct_clientes:.1f}%")

st.progress(min(pct_meta / 100, 1.0))

# ---------------------------
# TOP CLIENTES NÃO ATENDIDOS
# ---------------------------
df_todos_clientes = df_vendas["cliente"].unique()
df_meus_clientes = df_rep["cliente"].unique()

clientes_nao_atendidos = list(set(df_todos_clientes) - set(df_meus_clientes))

st.subheader("🚫 Top 5 Clientes Não Atendidos")
if len(clientes_nao_atendidos) > 0:
    st.write(clientes_nao_atendidos[:5])
else:
    st.success("✅ Você já atendeu todos os clientes!")

# ---------------------------
# TOP 5 CIDADES NÃO ATENDIDAS
# ---------------------------
df_cidades = df_vendas[~df_vendas["cliente"].isin(df_meus_clientes)]
top_cidades = (
    df_cidades.groupby("cidade")["cliente"]
    .nunique()
    .sort_values(ascending=False)
    .head(5)
)

st.subheader("🏙️ Top 5 Cidades com Oportunidade")
st.write(top_cidades)

# ---------------------------
# RANKING DE REPRESENTANTES
# ---------------------------
ranking = (
    df_vendas.groupby("representante")["valor_vendido"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

ranking["posicao"] = ranking.index + 1

minha_posicao = ranking[ranking["representante"] == st.session_state.usuario_logado]["posicao"].values[0]

st.subheader("🏆 Ranking de Representantes")
st.write(f"Você está na **posição {int(minha_posicao)}** do ranking 🎯")

fig_ranking = px.bar(ranking, x="representante", y="valor_vendido", title="Ranking de Vendas")
st.plotly_chart(fig_ranking)






