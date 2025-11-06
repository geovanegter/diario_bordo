import streamlit as st
import pandas as pd
from datetime import date

st.write("Usuários carregados:", usuarios_df)

# ==================== CONFIGURAÇÕES GERAIS ====================
st.set_page_config(page_title="Diário de Bordo", layout="wide")

# ==================== FUNÇÕES AUXILIARES ====================
def carregar_dados():
    try:
        usuarios = pd.read_excel("dados/usuarios.xlsx")
    except Exception:
        st.error("❌ Erro ao carregar arquivo: usuarios.xlsx")
        return None, None, None

    try:
        metas_colecao = pd.read_excel("dados/metas_colecao.xlsx")
    except Exception:
        st.error("❌ Erro ao carregar arquivo: metas_colecao.xlsx")
        return None, None, None

    try:
        metas_semana = pd.read_excel("dados/meta_semanal.xlsx")
    except Exception:
        st.error("❌ Erro ao carregar arquivo: meta_semanal.xlsx")
        return None, None, None

    return usuarios, metas_colecao, metas_semana


# ==================== LOGIN ====================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Login")

    email = st.text_input("Usuário (e-mail)")
    senha = st.text_input("Senha", type="password")
    botao = st.button("Entrar")

    if botao:
        usuarios, _, _ = carregar_dados()

        if usuarios is None:
            st.stop()

        usuario = usuarios[(usuarios["email"] == email) & (usuarios["senha"] == senha)]

        if not usuario.empty:
            st.session_state.autenticado = True
            st.session_state.nome = usuario.iloc[0]["nome"]
            st.experimental_rerun()
        else:
            st.error("❌ Usuário ou senha incorretos!")

    st.stop()

# ==================== PÁGINA PRINCIPAL ====================
st.sidebar.title(f"👋 Olá, {st.session_state['nome']}")

usuarios, metas_colecao, metas_semana = carregar_dados()
if usuarios is None:
    st.stop()

st.title("📊 Diário de Bordo - Dashboard do Representante")

representante = st.session_state["nome"]
colecao = st.selectbox("Selecione a coleção", metas_colecao["colecao"].unique())

meta_rep = metas_colecao[(metas_colecao["representante"] == representante) & (metas_colecao["colecao"] == colecao)]

if meta_rep.empty:
    st.warning("⚠️ Nenhuma meta encontrada para este representante nesta coleção.")
    st.stop()

meta_vendas = float(meta_rep.iloc[0]["meta_vendas"])
meta_clientes = float(meta_rep.iloc[0]["meta_clientes"])
ticket_medio = meta_vendas / meta_clientes if meta_clientes > 0 else 0

# pegar semana atual
hoje = date.today()
semana = metas_semana[metas_semana["data_inicio"] <= hoje]
semana = semana[semana["data_fim"] >= hoje].reset_index()

if semana.empty:
    st.error("❌ Não encontrou semana no arquivo meta_semanal.xlsx para a data de hoje")
    st.stop()

semana_atual = float(semana.iloc[0]["percentual_meta"])
meta_semana_vendas = meta_vendas * semana_atual
clientes_semana = meta_semana_vendas / ticket_medio if ticket_medio > 0 else 0

# ==================== CARDS ====================
st.markdown(f"""
<div style='display:flex; gap:16px;'>
    <div style='flex:1; background:#f4f4f4; padding:20px; border-radius:10px;'>
        <h3>🎯 % da Meta da Coleção</h3>
        <p style='font-size:28px; margin:0;'><b>{semana_atual*100:.1f}%</b></p>
    </div>

    <div style='flex:1; background:#f4f4f4; padding:20px; border-radius:10px;'>
        <h3>📈 Meta de vendas da semana</h3>
        <p style='font-size:28px; margin:0;'>R$ {meta_semana_vendas:,.2f}</p>
    </div>

    <div style='flex:1; background:#f4f4f4; padding:20px; border-radius:10px;'>
        <h3>👥 Clientes a vender na semana</h3>
        <p style='font-size:28px; margin:0;'>{clientes_semana:.0f}</p>
    </div>
</div>
""", unsafe_allow_html=True)

