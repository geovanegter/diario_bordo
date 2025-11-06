import streamlit as st
import pandas as pd

st.set_page_config(page_title="📘 Diário de Bordo Comercial", layout="wide")

# -------------------------------
# Carrega planilhas
# -------------------------------
@st.cache_data
def carregar_planilhas():
    return {
        "usuarios": pd.read_excel("dados/usuarios.xlsx"),
        "vendas": pd.read_excel("dados/vendas.xlsx"),
        "metas_colecao": pd.read_excel("dados/metas_colecao.xlsx"),
        "meta_semanal": pd.read_excel("dados/meta_semanal.xlsx")
    }

dfs = carregar_planilhas()

# -------------------------------
# Função de login
# -------------------------------
def autenticar(email, senha):
    usuarios = dfs["usuarios"]
    usuarios["email"] = usuarios["email"].astype(str)
    usuarios["senha"] = usuarios["senha"].astype(str)

    user = usuarios[
        (usuarios["email"].str.lower() == email.lower()) &
        (usuarios["senha"] == senha)
    ]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

# -------------------------------
# Função ticket médio
# -------------------------------
def calcular_ticket_medio(rep):
    metas = dfs["metas_colecao"]
    meta_row = metas[metas["representante"] == rep]
    if meta_row.empty:
        return 0
    total_venda = meta_row["meta_vendas"].sum()
    total_clientes = meta_row["meta_clientes"].sum()
    return total_venda / total_clientes if total_clientes > 0 else 0

# -------------------------------
# Sessão login
# -------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = None
    st.session_state.pagina = "Dashboard"

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
                st.experimental_rerun()
            else:
                st.error("❌ Usuário ou senha incorretos!")
                st.stop()

# -------------------------------
# Representante logado
# -------------------------------
user = st.session_state.user
representante = user.get("representante")
if not representante:
    st.error("❌ Usuário sem representante definido!")
    st.stop()

# -------------------------------
# Sidebar de navegação (botões)
# -------------------------------
st.sidebar.title("Navegação")
paginas = ["Dashboard", "Clientes", "Ranking", "Dossiê Cliente"]
for p in paginas:
    if st.sidebar.button(p):
        st.session_state.pagina = p

if st.sidebar.button("Logout"):
    st.session_state.logado = False
    st.session_state.user = None
    st.experimental_rerun()

pagina = st.session_state.get("pagina", "Dashboard")

# -------------------------------
# Conteúdo principal
# -------------------------------
st.markdown(f"## 👋 Olá, {representante}")
st.markdown(f"Você está em: 📍 Localização atual (em breve com geolocalização)")

vendas = dfs["vendas"]
metas_colecao = dfs["metas_colecao"]
meta_semanal = dfs["meta_semanal"]

vendas_rep = vendas[vendas["representante"] == representante]

# -------------------------------
# Dashboard
# -------------------------------
if pagina == "Dashboard":
    st.subheader("🎯 Progresso das metas por coleção")

    for _, row in metas_colecao[metas_colecao["representante"] == representante].iterrows():
        colecao = row["colecao"]
        meta_valor = row["meta_vendas"]
        vendido = vendas_rep[vendas_rep["colecao"] == colecao]["valor_vendido"].sum()
        progresso = min(vendido / meta_valor if meta_valor > 0 else 0, 1.0)

        st.markdown(f"**Coleção {colecao}** — Você atingiu {progresso*100:.1f}% da meta")
        st.progress(progresso)

    st.subheader("📅 Meta da semana")
    week_rows = meta_semanal[meta_semanal["colecao"].isin(
        metas_colecao[metas_colecao["representante"] == representante]["colecao"]
    )].drop_duplicates(subset=["colecao"])

    ticket_medio = calcular_ticket_medio(representante)

    for _, row in week_rows.iterrows():
        colecao = row["colecao"]
        percentual_meta = row["percentual_da_meta"]

        meta_total = metas_colecao.loc[metas_colecao["colecao"] == colecao, "meta_vendas"].values[0]
        vendido = vendas_rep[vendas_rep["colecao"] == colecao]["valor_vendido"].sum()
        progresso = min(vendido / (percentual_meta / 100 * meta_total), 1.0)

        clientes_restantes = max((percentual_meta / 100 * meta_total) / ticket_medio - vendido / ticket_medio, 0)

        st.markdown(f"**Coleção {colecao}** — {percentual_meta}% da meta da semana")
        st.progress(progresso)
        st.markdown(f"Vendas realizadas: R$ {vendido:,.2f}")
        st.markdown(f"Clientes a atender: {clientes_restantes:.0f}")

# -------------------------------
# Outras páginas
# -------------------------------
elif pagina == "Clientes":
    st.subheader("📋 Lista de clientes")
    st.dataframe(vendas_rep[["cliente","colecao","valor_vendido"]])

elif pagina == "Ranking":
    st.subheader("🏆 Ranking")
    ranking = vendas_rep.groupby("cliente")["valor_vendido"].sum().sort_values(ascending=False)
    st.dataframe(ranking)

elif pagina == "Dossiê Cliente":
    st.subheader("📂 Dossiê Cliente")
    cliente = st.selectbox("Escolha o cliente", vendas_rep["cliente"].unique())
    st.dataframe(vendas_rep[vendas_rep["cliente"] == cliente])

