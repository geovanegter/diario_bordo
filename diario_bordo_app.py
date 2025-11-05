# Diário de Bordo MVP
# Código principal do projeto (arquivo único: diario_bordo_app.py)
# ------------------------------------------------------------------
# Instruções
# - Nome da planilha de vendas: `vendas.xlsx` (na pasta `dados/` ou no mesmo diretório).
# - A planilha `vendas.xlsx` deve conter pelo menos as colunas:
#   representante, email, senha, cliente, cidade, colecao, marca, bairro, cep,
#   qtd_pecas, valor_vendido, desconto, prazo
# - Arquivo de planos de ação: `planos_acoes.xlsx` (será criado automaticamente na pasta `dados/` se não existir).
# - Rode localmente com: streamlit run diario_bordo_app.py
# ------------------------------------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
import plotly.express as px

# ---------------------- Configuração ----------------------
st.set_page_config(page_title="Diário de Bordo", layout="wide")
DATA_DIR = Path("dados")
DATA_DIR.mkdir(exist_ok=True)
VENDAS_FILE = DATA_DIR / "vendas.xlsx"
PLANOS_FILE = DATA_DIR / "planos_acoes.xlsx"

# ---------------------- Helpers ----------------------

def ensure_templates_exist():
    """Se os arquivos não existirem, cria templates mínimos para o MVP."""
    if not VENDAS_FILE.exists():
        sample = pd.DataFrame([
            {"representante":"João Silva","email":"joao@example.com","senha":"1234","cliente":"Cliente A","cidade":"Cidade X","colecao":"Colecao 1","marca":"Marca A","bairro":"Bairro 1","cep":"00000-000","qtd_pecas":10,"valor_vendido":5000.0,"desconto":0.0,"prazo":"30/11/2025"},
            {"representante":"Maria Souza","email":"maria@example.com","senha":"abcd","cliente":"Cliente B","cidade":"Cidade Y","colecao":"Colecao 2","marca":"Marca B","bairro":"Bairro 2","cep":"11111-111","qtd_pecas":3,"valor_vendido":1200.0,"desconto":5.0,"prazo":"15/12/2025"},
        ])
        sample.to_excel(VENDAS_FILE, index=False)

    if not PLANOS_FILE.exists():
        planos = pd.DataFrame(columns=["representante","cliente","cidade","colecao","marca","bairro","cep","qtd_pecas","valor_vendido","desconto","prazo","acao_sugerida","status_acao","comentarios"])
        planos.to_excel(PLANOS_FILE, index=False)


def load_data():
    vendas = pd.read_excel(VENDAS_FILE, engine="openpyxl")
    # normalizar nomes de colunas para evitar acentos/variantes
    vendas.columns = [c.strip() for c in vendas.columns]
    try:
        planos = pd.read_excel(PLANOS_FILE, engine="openpyxl")
    except Exception:
        planos = pd.DataFrame(columns=["representante","cliente","cidade","colecao","marca","bairro","cep","qtd_pecas","valor_vendido","desconto","prazo","acao_sugerida","status_acao","comentarios"])
    return vendas, planos


def save_planos(planos_df):
    planos_df.to_excel(PLANOS_FILE, index=False)


# ---------------------- Autenticação simples (MVP) ----------------------

def authenticate(email, senha, vendas_df):
    """Procura o email+senha na tabela de vendas e retorna nome do representante (primeiro match)."""
    df = vendas_df.copy()
    if 'email' not in df.columns or 'senha' not in df.columns or 'representante' not in df.columns:
        return None
    mask = (df['email'].astype(str) == str(email)) & (df['senha'].astype(str) == str(senha))
    if mask.any():
        return df.loc[mask, 'representante'].iloc[0]
    return None


# ---------------------- UI: Login ----------------------

ensure_templates_exist()

st.title("Diário de Bordo - App MVP")
st.markdown("Uma ferramenta simples para representantes comerciais — versão MVP.")

vendas_df, planos_df = load_data()

# Login box
with st.form("login_form"):
    st.subheader("Login do Representante")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    submitted = st.form_submit_button("Entrar")

if submitted:
    rep_name = authenticate(email, senha, vendas_df)
    if rep_name is None:
        st.error("Email ou senha inválidos — verifique a planilha vendas.xlsx e tente novamente.")
    else:
        st.success(f"Olá, {rep_name}! Carregando seu painel...")
        st.session_state['rep_name'] = rep_name

# Se já autenticado, mostrar app
if 'rep_name' in st.session_state:
    rep = st.session_state['rep_name']

    # Recarregar dados filtrando pelo representante
    vendas_df, planos_df = load_data()
    df_rep = vendas_df[vendas_df['representante'] == rep].copy()
    planos_rep = planos_df[planos_df['representante'] == rep].copy()

    # Top bar: saudação e resumo rápido
    st.header(f"Olá, {rep}")
    # Definir metas (no MVP, fixas — depois podem vir da planilha)
    meta_reais = st.sidebar.number_input("Meta da semana (R$)", value=100000.0)
    meta_clientes = st.sidebar.number_input("Meta de clientes (unidades)", value=50)
    semana_num = st.sidebar.number_input("Semana nº", value=5, min_value=1)

    # Cálculos
    total_vendido = df_rep['valor_vendido'].sum() if not df_rep.empty else 0.0
    total_pecas = df_rep['qtd_pecas'].sum() if not df_rep.empty else 0
    total_clientes = df_rep['cliente'].nunique() if not df_rep.empty else 0

    pct_cota = (total_vendido / meta_reais) * 100 if meta_reais > 0 else 0
    pct_dias = 0  # placeholder: se tivermos dados por dia podemos calcular

    col1, col2, col3, col4 = st.columns([3,2,2,2])
    with col1:
        st.subheader(f"Esta é a {semana_num}ª semana de vendas")
        st.markdown(f"**Você atingiu {pct_cota:.1f}% da meta**")
        st.progress(min(pct_cota/100.0, 1.0))
    with col2:
        st.metric("R$ Vendidos", f"R$ {total_vendido:,.2f}")
    with col3:
        st.metric("Peças vendidas", f"{int(total_pecas)}")
    with col4:
        st.metric("Clientes atendidos", f"{int(total_clientes)}")

    st.markdown("---")

    # Objetivos da semana (barra de atingimento cliente)
    st.subheader("Objetivos da semana")
    st.write(f"Meta: R$ {meta_reais:.0f} — Clientes: {int(meta_clientes)}")
    st.progress(min(total_clientes / max(meta_clientes,1), 1.0))

    # Alerts: top 5 clientes não atendidos e top 5 cidades
    st.subheader("Alertas e prioridades")
    not_done = planos_rep[planos_rep['status_acao'] != 'Concluído'] if not planos_rep.empty else pd.DataFrame()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top 5 — Clientes prioritários não atendidos**")
        if not not_done.empty:
            top_clients = not_done.sort_values(by='valor_vendido', ascending=False).head(5)
            st.table(top_clients[['cliente','cidade','valor_vendido','acao_sugerida']].fillna(''))
        else:
            st.write("Nenhuma ação pendente — bom trabalho!")
    with c2:
        st.markdown("**Top 5 — Cidades com maior potencial não atendidas**")
        if not not_done.empty:
            cities = not_done.groupby('cidade').agg({'cliente':'count','valor_vendido':'sum'}).reset_index()
            cities = cities.sort_values(by='valor_vendido', ascending=False).head(5)
            st.table(cities.fillna(''))
        else:
            st.write("Sem cidades pendentes.")

    st.markdown("---")

    # Kanban (simplificado): mostrar e editar status
    st.subheader("Kanban — suas ações")
    if planos_rep.empty:
        st.info("Nenhuma ação registrada para você. Peça ao gestor para carregar a planilha com as ações sugeridas.")
    else:
        # Apresentar cards por status
        statuses = ["A Fazer","Em andamento","Concluído"]
        cols = st.columns(3)
        status_cols = dict(zip(statuses, cols))

        # ensure index unique keys
        for idx, row in planos_rep.reset_index().iterrows():
            card_html = f"**{row['cliente']}** — {row.get('acao_sugerida','')}"

{row.get('cidade','')} • {row.get('qtd_pecas',0)} peças • R$ {row.get('valor_vendido',0):,.2f}"
            st.markdown("""<div style='border:1px solid #ddd;padding:8px;border-radius:6px;margin-bottom:8px'>""", unsafe_allow_html=True)
            st.markdown(card_html)
            new_status = st.selectbox("Mover para", options=statuses, index=statuses.index(row['status_acao']) if row['status_acao'] in statuses else 0, key=f"status_{idx}")
            planos_df.loc[(planos_df['cliente']==row['cliente']) & (planos_df['representante']==rep),'status_acao'] = new_status
            comment_key = f"coment_{idx}"
            comment = st.text_area("Comentário", value=row.get('comentarios','') if 'comentarios' in row else '', key=comment_key)
            planos_df.loc[(planos_df['cliente']==row['cliente']) & (planos_df['representante']==rep),'comentarios'] = comment
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Salvar alterações no Kanban"):
            save_planos(planos_df)
            st.success("Planos atualizados com sucesso!")

    st.markdown("---")

    # Ranking
    st.subheader("Ranking")
    ranking = vendas_df.groupby('representante').agg(total_vendido=('valor_vendido','sum')).reset_index()
    ranking = ranking.sort_values(by='total_vendido', ascending=False).reset_index(drop=True)
    ranking['posição'] = ranking.index + 1
    pos_row = ranking[ranking['representante']==rep]
    if not pos_row.empty:
        pos = int(pos_row['posição'].values[0])
        st.write(f"Você está na posição **{pos}º** do ranking (R$ {pos_row['total_vendido'].values[0]:,.2f})")
    else:
        st.write("Ainda não há dados suficientes para o ranking.")

    # Footer: informações adicionais
    st.markdown("---")
    st.caption("MVP — Diário de Bordo. Dados carregados a partir de vendas.xlsx e planos_acoes.xlsx na pasta dados/.")

else:
    st.info("Por favor, faça login com seu email e senha.")



