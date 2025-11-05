# ============================================================
# Diário de Bordo - MVP
# ============================================================
# Estrutura esperada:
# 📁 dados/
#     ├── usuarios.xlsx  (colunas: representante, email, senha)
#     ├── vendas.xlsx    (colunas: representante, cliente, cidade, colecao, marca, bairro, cep, qtd_pecas, valor_vendido, desconto, prazo)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px

# ---------------------- CONFIGURAÇÕES ----------------------
st.set_page_config(page_title="Diário de Bordo", layout="wide")

DATA_DIR = Path("dados")
DATA_DIR.mkdir(exist_ok=True)

USUARIOS_FILE = DATA_DIR / "usuarios.xlsx"
VENDAS_FILE = DATA_DIR / "vendas.xlsx"
PLANOS_FILE = DATA_DIR / "planos_acoes.xlsx"

# ---------------------- FUNÇÕES AUXILIARES ----------------------

def carregar_usuarios():
    if not USUARIOS_FILE.exists():
        exemplo = pd.DataFrame([
            {"representante":"João Silva","email":"joao@example.com","senha":"1234"},
            {"representante":"Maria Souza","email":"maria@example.com","senha":"abcd"},
        ])
        exemplo.to_excel(USUARIOS_FILE, index=False)
    return pd.read_excel(USUARIOS_FILE)

def carregar_vendas():
    if not VENDAS_FILE.exists():
        exemplo = pd.DataFrame([
            {"representante":"João Silva","cliente":"Loja A","cidade":"Jaraguá do Sul","colecao":"Verão 2025","marca":"Marca X","bairro":"Centro","cep":"89254-000","qtd_pecas":120,"valor_vendido":5800,"desconto":5,"prazo":"30/11/2025"},
            {"representante":"Maria Souza","cliente":"Boutique Bela","cidade":"Joinville","colecao":"Inverno 2025","marca":"Marca Y","bairro":"América","cep":"89201-000","qtd_pecas":80,"valor_vendido":4300,"desconto":3,"prazo":"10/12/2025"},
        ])
        exemplo.to_excel(VENDAS_FILE, index=False)
    return pd.read_excel(VENDAS_FILE)

def carregar_planos():
    if not PLANOS_FILE.exists():
        df = pd.DataFrame(columns=[
            "representante","cliente","acao_sugerida","status_acao","comentarios",
            "cidade","colecao","marca","valor_vendido","qtd_pecas"
        ])
        df.to_excel(PLANOS_FILE, index=False)
    return pd.read_excel(PLANOS_FILE)

def salvar_planos(df):
    df.to_excel(PLANOS_FILE, index=False)

# ---------------------- AUTENTICAÇÃO ----------------------

def authenticate(email, senha, usuarios_df):
    if usuarios_df.empty:
        st.error("⚠️ Nenhum usuário encontrado em usuarios.xlsx.")
        return None

    # Normaliza
    usuarios_df["email"] = usuarios_df["email"].astype(str).str.strip().str.lower()
    usuarios_df["senha"] = usuarios_df["senha"].astype(str).str.strip()

    email = str(email).strip().lower()
    senha = str(senha).strip()

    match = usuarios_df[
        (usuarios_df["email"] == email) &
        (usuarios_df["senha"] == senha)
    ]

    if not match.empty:
        return match.iloc[0]["representante"]

    return None

# ---------------------- LOGIN ----------------------

usuarios_df = carregar_usuarios()
vendas_df = carregar_vendas()
planos_df = carregar_planos()

st.title("📒 Diário de Bordo - MVP")
st.markdown("Ferramenta simples para representantes comerciais.")

if "rep_name" not in st.session_state:
    with st.form("login_form"):
        st.subheader("Login do Representante")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        rep_name = authenticate(email, senha, usuarios_df)
        if rep_name is None:
            st.error("❌ Email ou senha inválidos. Verifique usuarios.xlsx.")
        else:
            st.session_state["rep_name"] = rep_name
            st.success(f"✅ Login realizado! Bem-vindo, {rep_name}.")
            st.rerun()
else:
    rep = st.session_state["rep_name"]
    st.sidebar.success(f"Logado como: {rep}")
    st.sidebar.button("Sair", on_click=lambda: st.session_state.pop("rep_name"))

    # ---------------------- DADOS DO REPRESENTANTE ----------------------
    vendas_rep = vendas_df[vendas_df["representante"] == rep].copy()
    planos_rep = planos_df[planos_df["representante"] == rep].copy()

    if vendas_rep.empty:
        st.warning("Nenhuma venda encontrada para você em vendas.xlsx.")
    else:
        total_vendido = vendas_rep["valor_vendido"].sum()
        total_pecas = vendas_rep["qtd_pecas"].sum()
        total_clientes = vendas_rep["cliente"].nunique()

        st.header(f"Bem-vindo, {rep} 👋")
        st.metric("💰 Total Vendido", f"R$ {total_vendido:,.2f}")
        st.metric("🧦 Peças Vendidas", f"{total_pecas:,}")
        st.metric("👥 Clientes Atendidos", f"{total_clientes}")

        st.markdown("---")
        st.subheader("📊 Desempenho por cidade")
        fig = px.bar(vendas_rep, x="cidade", y="valor_vendido", color="marca", title="Vendas por Cidade e Marca")
        st.plotly_chart(fig, use_container_width=True)

        # ---------------------- KANBAN SIMPLES ----------------------
        st.markdown("---")
        st.subheader("🗂️ Ações e Pendências")

        if planos_rep.empty:
            st.info("Nenhuma ação registrada. Você pode criar novas ações abaixo.")
        else:
            for i, row in planos_rep.iterrows():
                st.markdown(f"**{row['cliente']}** — {row.get('acao_sugerida','(sem ação)')}")
                novo_status = st.selectbox(
                    "Status",
                    ["A Fazer", "Em andamento", "Concluído"],
                    index=["A Fazer", "Em andamento", "Concluído"].index(row.get("status_acao","A Fazer")),
                    key=f"status_{i}"
                )
                planos_df.loc[i, "status_acao"] = novo_status
                comentario = st.text_area("Comentário", value=row.get("comentarios",""), key=f"coment_{i}")
                planos_df.loc[i, "comentarios"] = comentario
                st.markdown("---")

            if st.button("💾 Salvar Alterações"):
                salvar_planos(planos_df)
                st.success("Alterações salvas com sucesso!")

        # ---------------------- CRIAR NOVA AÇÃO ----------------------
        with st.expander("➕ Adicionar nova ação"):
            cliente = st.text_input("Cliente")
            acao = st.text_input("Ação sugerida")
            if st.button("Adicionar"):
                novo = pd.DataFrame([{
                    "representante": rep,
                    "cliente": cliente,
                    "acao_sugerida": acao,
                    "status_acao": "A Fazer",
                    "comentarios": ""
                }])
                planos_df = pd.concat([planos_df, novo], ignore_index=True)
                salvar_planos(planos_df)
                st.success("Ação adicionada!")
                st.rerun()

    # ---------------------- RANKING ----------------------
    st.markdown("---")
    st.subheader("🏆 Ranking de Vendas")
    ranking = vendas_df.groupby("representante")["valor_vendido"].sum().reset_index()
    ranking = ranking.sort_values("valor_vendido", ascending=False).reset_index(drop=True)
    ranking["Posição"] = ranking.index + 1
    st.table(ranking)






