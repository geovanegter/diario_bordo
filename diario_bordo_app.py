import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Diário de Bordo – Vendas", layout="wide")

@st.cache_data
def carregar_planilhas():
    usuarios_df = pd.read_excel("dados/usuarios.xlsx")  # email, senha, nome
    vendas_df = pd.read_excel("dados/vendas.xlsx")      # precisa ter coluna "nome" ou "representante"
    metas_df = pd.read_excel("dados/metas_colecao.xlsx")  # meta mensal por coleção
    metas_semanais_df = pd.read_excel("dados/meta_semanal.xlsx")  # percentual da meta por semana
    return usuarios_df, vendas_df, metas_df, metas_semanais_df


usuarios_df, vendas_df, metas_df, metas_semanais_df = carregar_planilhas()

# --------------------------
# LOGIN
# --------------------------
st.title("🔐 Login – Diário de Bordo")

email = st.text_input("E-mail:")
senha = st.text_input("Senha:", type="password")
btn_login = st.button("Entrar")

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if btn_login:
    usuario_validado = usuarios_df[
        (usuarios_df["email"] == email) &
        (usuarios_df["senha"] == senha)
    ]

    if usuario_validado.empty:
        st.error("❌ Usuário ou senha incorretos.")
        st.stop()

    st.session_state["logado"] = True
    st.session_state["nome"] = usuario_validado.iloc[0]["nome"]
    st.rerun()

if not st.session_state["logado"]:
    st.stop()

# --------------------------
# PÁGINA PRINCIPAL
# --------------------------
nome = st.session_state["nome"]
st.subheader(f"👤 Bem-vindo, {nome}")

# Certifica que vendas tem a coluna correta para filtragem
if "representante" in vendas_df.columns:
    vendas_rep = vendas_df[vendas_df["representante"] == nome]
else:
    vendas_rep = vendas_df[vendas_df["nome"] == nome]

colecao = st.selectbox("Selecione a coleção:", sorted(vendas_rep["colecao"].unique()))
data_filtro = st.date_input("Selecione uma data de referência para calcular a meta da semana:")

# --------------------------
# META MENSAL (metas_colecao.xlsx)
# --------------------------
meta_mensal = metas_df[metas_df["colecao"] == colecao]

meta_mensal_valor = meta_mensal["meta"].iloc[0] if not meta_mensal.empty else 0
total_vendido = vendas_rep[vendas_rep["colecao"] == colecao]["valor"].sum()

# --------------------------
# META SEMANAL (meta_semanal.xlsx)
# --------------------------
meta_semana = metas_semanais_df[
    (metas_semanais_df["colecao"] == colecao) &
    (metas_semanais_df["semana_inicio"] <= pd.to_datetime(data_filtro)) &
    (metas_semanais_df["semana_fim"] >= pd.to_datetime(data_filtro))
]

if not meta_semana.empty:
    percentual_semana = meta_semana.iloc[0]["percentual_da_meta"]
    meta_semana_valor = meta_mensal_valor * percentual_semana
else:
    percentual_semana = 0
    meta_semana_valor = 0

# --------------------------
# EXIBIÇÃO
# --------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Meta Mensal", f"R$ {meta_mensal_valor:,.2f}".replace(",", "."))
col2.metric("Meta da Semana", f"R$ {meta_semana_valor:,.2f}".replace(",", "."))
col3.metric("Vendido", f"R$ {total_vendido:,.2f}".replace(",", "."))

st.write("📊 **Detalhamento das vendas**")
st.dataframe(vendas_rep[vendas_rep["colecao"] == colecao])



