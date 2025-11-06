import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Diário de Bordo – Vendas", layout="wide")

@st.cache_data
def carregar_planilhas():
    usuarios_df = pd.read_excel("dados/usuarios.xlsx")
    vendas_df = pd.read_excel("dados/vendas.xlsx")
    metas_df = pd.read_excel("dados/metas.xlsx")
    metas_semanais_df = pd.read_excel("dados/meta_semanal.xlsx")
    return usuarios_df, vendas_df, metas_df, metas_semanais_df


usuarios_df, vendas_df, metas_df, metas_semanais_df = carregar_planilhas()

# --------------------------
# LOGIN
# --------------------------
st.title("🔐 Login – Diário de Bordo")

usuario = st.text_input("Usuário:")
senha = st.text_input("Senha:", type="password")
btn_login = st.button("Entrar")

if btn_login:
    usuario_validado = usuarios_df[
        (usuarios_df["usuario"] == usuario) &
        (usuarios_df["senha"] == senha)
    ]

    if usuario_validado.empty:
        st.error("❌ Usuário ou senha incorretos.")
        st.stop()

    representante = usuario_validado.iloc[0]["representante"]
    st.session_state["logado"] = True
    st.session_state["representante"] = representante
    st.rerun()

if "logado" not in st.session_state:
    st.stop()

# --------------------------
# PÁGINA PRINCIPAL
# --------------------------
representante = st.session_state["representante"]
st.subheader(f"👤 Bem-vindo, {representante}")

# Filtra vendas do representante
vendas_rep = vendas_df[vendas_df["representante"] == representante]

colecao = st.selectbox("Selecione a coleção:", sorted(vendas_rep["colecao"].unique()))
data_filtro = st.date_input("Selecione uma data referência para meta semanal:")

# --------------------------
# META MENSAL (tabela metas.xlsx)
# --------------------------
meta_mensal = metas_df[
    (metas_df["representante"] == representante) &
    (metas_df["colecao"] == colecao)
]

if not meta_mensal.empty:
    meta_mensal_valor = meta_mensal.iloc[0]["meta"]
else:
    meta_mensal_valor = 0

# Soma das vendas do representante na coleção
total_vendido = vendas_rep[vendas_rep["colecao"] == colecao]["valor"].sum()

# --------------------------
# META SEMANAL (geral por coleção)
# --------------------------
meta_semana = metas_semanais_df[
    (metas_semanais_df["colecao"] == colecao) &
    (metas_semanais_df["semana_inicio"] <= pd.to_datetime(data_filtro)) &
    (metas_semanais_df["semana_fim"] >= pd.to_datetime(data_filtro))
]

if not meta_semana.empty:
    percentual_semana = meta_semana.iloc[0]["percentual_da_meta"]
    meta_semana_valor = (meta_mensal_valor * percentual_semana)
else:
    percentual_semana = 0
    meta_semana_valor = 0

# --------------------------
# EXIBIÇÃO DAS INFORMAÇÕES
# --------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Meta Mensal", f"R$ {meta_mensal_valor:,.2f}".replace(",", "."))
col2.metric("Meta da Semana", f"R$ {meta_semana_valor:,.2f}".replace(",", "."))
col3.metric("Vendido", f"R$ {total_vendido:,.2f}".replace(",", "."))

st.write("📊 **Detalhamento das vendas**")
st.dataframe(vendas_rep[vendas_rep["colecao"] == colecao])
