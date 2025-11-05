import streamlit as st
import pandas as pd
from pathlib import Path

# ======================================================
# CONFIGURAÇÕES
# ======================================================

st.set_page_config(
    page_title="Diário de Bordo",
    page_icon="📋",
    layout="wide"
)

DATA_FOLDER = Path("dados")  # Pasta onde estão os arquivos

# ======================================================
# FUNÇÕES DE CARREGAMENTO
# ======================================================

@st.cache_data
def carregar_planilha(nome_arquivo):
    caminho = DATA_FOLDER / nome_arquivo
    if not caminho.exists():
        st.error(f"❌ Arquivo não encontrado: `{nome_arquivo}` dentro da pasta /dados")
        return pd.DataFrame()
    return pd.read_excel(caminho)


def carregar_dados():
    return {
        "usuarios": carregar_planilha("usuarios.xlsx"),
        "vendas": carregar_planilha("vendas.xlsx"),
        "clientes": carregar_planilha("clientes.xlsx"),
        "metas": carregar_planilha("metas_colecao.xlsx"),
        "colecoes": carregar_planilha("colecoes.xlsx")
    }

# ======================================================
# AUTENTICAÇÃO
# ======================================================

def autenticar(email, senha, df_usuarios):
    usuario = df_usuarios[
        (df_usuarios["email"] == email) &
        (df_usuarios["senha"] == senha)
    ]
    if len(usuario) > 0:
        return usuario.iloc[0].to_dict()
    return None


# ======================================================
# INÍCIO DO APP
# ======================================================

dados = carregar_dados()
usuarios_df = dados["usuarios"]

if "usuario" not in st.session_state:
    st.session_state.usuario = None


if st.session_state.usuario is None:
    st.title("🔐 Diário de Bordo — Login")

    with st.form("login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            user = autenticar(email, senha, usuarios_df)

            if user:
                st.session_state.usuario = user
                st.success(f"✅ Bem-vindo(a), **{user['nome']}**!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos")
    st.stop()


# ======================================================
# ÁREA LOGADA
# ======================================================

usuario = st.session_state.usuario
st.sidebar.title(f"👤 {usuario['nome']}")
st.sidebar.write(f"📧 {usuario['email']}")

pagina = st.sidebar.radio("Navegação", ["Visão Geral", "Meus Objetivos", "Clientes", "Dossiê Cliente"])

st.sidebar.button("🔓 Logout", on_click=lambda: st.session_state.update({"usuario": None}))
st.title("📊 Diário de Bordo — Dashboard")

# ======================================================
# LÓGICA DE CONSULTA — APÓS LOGIN
# ======================================================

vendas_df = dados["vendas"]
metas_df = dados["metas"]

rep = usuario["representante"]

vendas_rep = vendas_df[vendas_df["representante"] == rep]
metas_rep = metas_df[metas_df["representante"] == rep]

# ======================================================
# PÁGINAS
# ======================================================

if pagina == "Visão Geral":
    st.subheader("📌 Visão Geral do Representante")

    col1, col2 = st.columns(2)

    # meta coleção
    meta_valor = float(metas_rep["meta_vendas"].sum())
    realizado = float(vendas_rep["valor_vendido"].sum())
    progresso = realizado / meta_valor if meta_valor > 0 else 0

    with col1:
        st.write("💰 Meta de Vendas da Coleção")
        st.progress(progresso)
        st.write(f"**Meta:** R$ {meta_valor:,.2f}")
        st.write(f"**Vendido:** R$ {realizado:,.2f}")
        st.write(f"**Falta:** R$ {meta_valor - realizado:,.2f}")

    meta_cli = int(metas_rep["meta_clientes"].sum())
    clientes_atendidos = vendas_rep["cliente"].nunique()
    progresso_cli = clientes_atendidos / meta_cli if meta_cli > 0 else 0

    with col2:
        st.write("🧾 Meta de Clientes")
        st.progress(progresso_cli)
        st.write(f"**Meta:** {meta_cli} clientes")
        st.write(f"**Atendidos:** {clientes_atendidos}")
        st.write(f"**Faltam:** {meta_cli - clientes_atendidos}")

elif pagina == "Clientes":
    st.subheader("📋 Clientes atendidos na coleção")
    st.dataframe(vendas_rep)

elif pagina == "Dossiê Cliente":
    st.subheader("📚 Dossiê do Cliente")
    cliente = st.selectbox("Selecione um cliente", vendas_rep["cliente"].unique())
    st.dataframe(vendas_rep[vendas_rep["cliente"] == cliente])

else:
    st.subheader("🎯 Meus Objetivos")
    st.dataframe(metas_rep)


