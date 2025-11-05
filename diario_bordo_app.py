import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Diário de Bordo Comercial",
    layout="wide"
)

# =========================
# FUNÇÃO: LOGIN
# =========================
@st.cache_data
def load_users():
    try:
        return pd.read_excel("usuarios.xlsx")
    except:
        st.error("❌ Arquivo usuarios.xlsx não encontrado no diretório do app.")
        return None

@st.cache_data
def load_sales():
    try:
        return pd.read_excel("vendas.xlsx")
    except:
        st.error("❌ Arquivo vendas.xlsx não encontrado.")
        return None

def login(email, senha, df_users):
    user = df_users[(df_users["email"] == email) & (df_users["senha"] == senha)]
    if len(user) == 1:
        return user.iloc[0]  # retorna a linha com nome e representante
    return None

# =========================
# TELA DE LOGIN
# =========================
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:

    st.title("🔐 Login — Diário de Bordo Comercial")

    usuarios = load_users()

    if usuarios is not None:
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            user = login(email, senha, usuarios)
            if user is not None:
                st.session_state.usuario = {
                    "nome": user["nome"],
                    "representante": user["representante"]
                }
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")
    st.stop()

# =========================
# A PARTIR DAQUI → USUÁRIO LOGADO
# =========================
user_name = st.session_state.usuario["nome"]
rep_code = st.session_state.usuario["representante"]

st.sidebar.success(f"✅ Logado como: **{user_name}**")

# Botão de logout
if st.sidebar.button("Logout"):
    st.session_state.usuario = None
    st.rerun()

# =========================
# CARREGA VENDAS
# =========================
vendas = load_sales()

if vendas is None:
    st.stop()

if rep_code != "ALL":
    vendas = vendas[vendas["representante"] == rep_code]

# =========================
# DASHBOARD INICIAL
# =========================
st.title(f"📊 Diário de Bordo - Bem vindo, {user_name.split()[0]}!")

meta_valor = st.sidebar.number_input("Meta da Semana (R$)", value=100000.0)
meta_clientes = st.sidebar.number_input("Meta de Clientes", value=20)

valor_atual = vendas["valor_vendido"].sum()
clientes_atuais = vendas["cliente"].nunique()

col1, col2 = st.columns(2)
col1.metric("Atingimento em R$", f"R$ {valor_atual:,.2f}", f"{(valor_atual/meta_valor)*100:.1f}%")
col2.metric("Clientes atingidos", clientes_atuais, f"{(clientes_atuais/meta_clientes)*100:.1f}%")

# =========================
# TOP CLIENTES NÃO ATENDIDOS
# =========================
st.subheader("📍 Top 5 clientes não atendidos ainda")
clientes_todos = vendas[["cliente", "cidade"]].drop_duplicates()
clientes_atendidos = vendas["cliente"].unique()

clientes_nao_atendidos = clientes_todos[~clientes_todos["cliente"].isin(clientes_atendidos)]

if len(clientes_nao_atendidos) > 0:
    st.table(clientes_nao_atendidos.head(5))
else:
    st.success("✅ Você já atendeu todos os clientes!")

# =========================
# GRÁFICO DE BARRAS (VENDA POR CIDADE)
# =========================
st.subheader("🌎 Ranking de vendas por cidade")

vendas_cidade = vendas.groupby("cidade")["valor_vendido"].sum().reset_index()

fig = px.bar(vendas_cidade, x="cidade", y="valor_vendido")
st.plotly_chart(fig, use_container_width=True)






