import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="📘 Diário de Bordo", layout="wide")

# ======= FUNÇÃO DE LOGIN =======
def autenticar_usuario(usuario, senha):
    try:
        usuarios = pd.read_excel("dados/usuarios.xlsx")
        dados_usuario = usuarios.loc[usuarios["usuario"] == usuario]
        if not dados_usuario.empty and dados_usuario.iloc[0]["senha"] == senha:
            return dados_usuario.iloc[0]["nome"]
        return None
    except Exception as e:
        st.error(f"Erro ao autenticar: {e}")
        return None

# ======= LOGIN =======
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Acesso ao Diário de Bordo")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        nome = autenticar_usuario(usuario, senha)
        if nome:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario
            st.session_state["nome"] = nome
            st.success(f"Bem-vindo(a), {nome} 👋")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# ======= SE CHEGOU AQUI, ESTÁ LOGADO =======
st.sidebar.title(f"👋 Olá, {st.session_state['nome']}")
if st.sidebar.button("Sair"):
    st.session_state["autenticado"] = False
    st.experimental_rerun()

st.title("📘 Diário de Bordo - Resumo Semanal")

# ======= LEITURA DE DADOS =======
try:
    dados = pd.read_excel("dados/diario_bordo.xlsx")
except FileNotFoundError:
    st.error("Arquivo 'diario_bordo.xlsx' não encontrado na pasta /dados")
    st.stop()

try:
    metas = pd.read_excel("dados/metas_colecao.xlsx")
except FileNotFoundError:
    st.error("Arquivo 'metas_colecao.xlsx' não encontrado na pasta /dados")
    st.stop()

# ======= FILTROS =======
usuario = st.session_state["usuario"]
dados_usuario = dados[dados["usuario"] == usuario]

if dados_usuario.empty:
    st.warning("Nenhum registro encontrado para este usuário.")
    st.stop()

# Selecionar semana
semanas = sorted(dados_usuario["semana"].unique(), reverse=True)
semana_selecionada = st.selectbox("Selecione a semana:", semanas)

week_row = dados_usuario[dados_usuario["semana"] == semana_selecionada]

# ======= VARIÁVEIS CORRIGIDAS =======
semana_inicio = (
    week_row["semana_inicio"].iloc[0]
    if "semana_inicio" in week_row.columns and not week_row.empty
    else "-"
)
semana_fim = (
    week_row["semana_fim"].iloc[0]
    if "semana_fim" in week_row.columns and not week_row.empty
    else "-"
)

# ======= CÁLCULOS =======
vendas_na_semana = week_row["vendas"].sum()
meta_semana = metas.loc[metas["usuario"] == usuario, "meta_semanal"].sum()
progresso = (vendas_na_semana / meta_semana * 100) if meta_semana > 0 else 0

# ======= EXIBIÇÃO =======
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div class='card' style='flex:1;'>
            <h4>💵 Vendido esta semana</h4>
            <p style='font-size:22px;margin:0;'>R$ {vendas_na_semana:,.2f}</p>
            <p class='muted'>Período: {semana_inicio} → {semana_fim}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class='card' style='flex:1;'>
            <h4>🎯 Meta semanal</h4>
            <p style='font-size:22px;margin:0;'>R$ {meta_semana:,.2f}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class='card' style='flex:1;'>
            <h4>📊 Progresso</h4>
            <p style='font-size:22px;margin:0;'>{progresso:.1f}%</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.progress(min(progresso / 100, 1.0))

st.markdown("---")
st.subheader("📈 Detalhes da Semana")
st.dataframe(week_row)

# ======= CSS =======
st.markdown(
    """
    <style>
    .card {
        background: #f9f9f9;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    .muted {
        color: #666;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
