import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Diário de Bordo", layout="wide")

# -------------------------
# 1. LOGIN (VERSÃO QUE FUNCIONA)
# -------------------------
USERS = {
    "joao@empresa.com": {"password": "123", "nome": "João Silva", "representante_id": 1},
    "maria@empresa.com": {"password": "456", "nome": "Maria Souza", "representante_id": 2},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Diário de Bordo — Login")

    with st.form(key="login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            if email in USERS and USERS[email]["password"] == senha:
                st.session_state.logged_in = True
                st.session_state.user = USERS[email]
                st.experimental_rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")

else:
    nome_usuario = st.session_state.user["nome"]

    # -------------------------
    # 2. MENU LATERAL
    # -------------------------
    st.sidebar.title("📌 Navegação")
    pagina = st.sidebar.radio(
        "",
        ["Visão Geral", "Meus Objetivos", "Clientes", "Dossiê do Cliente"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    # -------------------------
    # 3. DASHBOARD — VISÃO GERAL
    # -------------------------
    if pagina == "Visão Geral":

        st.title(f"👋 Olá, {nome_usuario}")

        # Dados fictícios até carregarmos da planilha
        meta_vendas = 100000
        vendas_realizadas = 72000
        falta_vender = meta_vendas - vendas_realizadas
        percentual_meta_vendas = round((vendas_realizadas / meta_vendas) * 100, 1)

        meta_clientes = 45
        clientes_atendidos = 32
        falta_clientes = meta_clientes - clientes_atendidos
        percentual_clientes = round((clientes_atendidos / meta_clientes) * 100, 1)

        st.subheader("📈 Progresso da Coleção")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🎯 Meta de Vendas da Coleção")
            st.progress(percentual_meta_vendas / 100)
            st.write(f"**Meta:** R$ {meta_vendas:,.2f}")
            st.write(f"**Vendas realizadas:** R$ {vendas_realizadas:,.2f}")
            st.write(f"**Falta vender:** R$ {falta_vender:,.2f}")

        with col2:
            st.markdown("#### 👥 Meta de Clientes Atendidos")
            st.progress(percentual_clientes / 100)
            st.write(f"**Meta:** {meta_clientes}")
            st.write(f"**Clientes atendidos:** {clientes_atendidos}")
            st.write(f"**Faltam:** {falta_clientes}")

        st.markdown("---")

        st.subheader("📅 Semana em andamento")
        st.info("Aqui vai mostrar informações da semana, quantidade de visitas, agenda, etc.")

    # -------------------------
    # 4. OUTRAS PÁGINAS (placeholder por enquanto)
    # -------------------------
    if pagina == "Meus Objetivos":
        st.title("🎯 Meus objetivos")
        st.info("Em breve... (iremos conectar com metas da planilha)")

    if pagina == "Clientes":
        st.title("👥 Meus Clientes")
        st.info("Em breve... (iremos listar clientes e permitir registrar visitas)")

    if pagina == "Dossiê do Cliente":
        st.title("📄 Dossiê do Cliente")
        st.info("Em breve... (detalhes do cliente + histórico de visitas)")
