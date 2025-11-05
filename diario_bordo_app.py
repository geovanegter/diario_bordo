# ------------------------------------------------------------
# Diário de Bordo MVP - App Streamlit
# ------------------------------------------------------------
# Requisitos:
# - /dados/usuarios.xlsx   (colunas: representante, email, senha)
# - /dados/vendas.xlsx     (colunas: representante, cliente, cidade, colecao,
#                           marca, bairro, cep, qtd_pecas, valor_vendido, desconto, prazo)
# - O sistema cria /dados/planos_acoes.xlsx automaticamente no 1º acesso
# ------------------------------------------------------------

import streamlit as st
import pandas as pd
from pathlib import Path

# ================= CONFIGURAÇÃO =================
st.set_page_config(page_title="Diário de Bordo", layout="wide")

DATA_DIR = Path("dados")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "usuarios.xlsx"
VENDAS_FILE = DATA_DIR / "vendas.xlsx"
PLANOS_FILE = DATA_DIR / "planos_acoes.xlsx"


# ================ ARQUIVOS (GARANTE EXISTIR) =================
def ensure_files_exist():
    if not USERS_FILE.exists():
        users = pd.DataFrame([
            {"representante": "SP01", "email": "sp01@rc.com", "senha": "1234"},
            {"representante": "PR03", "email": "pr03@rc.com", "senha": "5678"},
        ])
        users.to_excel(USERS_FILE, index=False)

    if not PLANOS_FILE.exists():
        planos = pd.DataFrame(columns=[
            "representante", "cliente", "cidade", "colecao", "marca", "bairro", "cep",
            "qtd_pecas", "valor_vendido", "desconto", "prazo",
            "acao_sugerida", "status_acao", "comentarios"
        ])
        planos.to_excel(PLANOS_FILE, index=False)


# ================ LOAD DATA =================
def load_users():
    df = pd.read_excel(USERS_FILE, engine="openpyxl")
    df.columns = [c.lower().strip() for c in df.columns]
    return df

def load_vendas():
    df = pd.read_excel(VENDAS_FILE, engine="openpyxl")
    df.columns = [c.lower().strip() for c in df.columns]
    return df

def load_planos():
    try:
        df = pd.read_excel(PLANOS_FILE, engine="openpyxl")
    except:
        df = pd.DataFrame()
    df.columns = [c.lower().strip() for c in df.columns]
    return df


def save_planos(df):
    df.to_excel(PLANOS_FILE, index=False)


# ================ AUTENTICAÇÃO =================
def authenticate(email, senha, users_df):
    mask = (users_df["email"] == email) & (users_df["senha"] == senha)
    if mask.any():
        return users_df.loc[mask, "representante"].iloc[0]
    return None


# ============================================================
# APP
# ============================================================
ensure_files_exist()

st.title("📋 Diário de Bordo — MVP")
st.caption("Primeira versão: login, dashboard e Kanban")

usuarios = load_users()
vendas = load_vendas()
planos = load_planos()


# ================ LOGIN =================
if "rep_name" not in st.session_state:
    with st.form("login_form"):
        st.subheader("Login")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submit_login = st.form_submit_button("Entrar")

    if submit_login:
        rep_name = authenticate(email, senha, usuarios)
        if rep_name:
            st.session_state["rep_name"] = rep_name
            st.rerun()
        else:
            st.error("Email ou senha incorretos.")
    st.stop()  # impede de carregar o painel sem login


# ================ PAINEL PRINCIPAL =================
rep = st.session_state["rep_name"]

st.header(f"👋 Olá, {rep}!")

df_rep = vendas[vendas["representante"] == rep]

meta_reais = st.sidebar.number_input("Meta da semana (R$)", value=100000.0)
meta_clientes = st.sidebar.number_input("Meta de clientes atendidos", value=50)
semana_num = st.sidebar.number_input("Semana nº", min_value=1, value=5)

total_vendido = df_rep["valor_vendido"].sum()
total_clientes = df_rep["cliente"].nunique()

pct_meta = (total_vendido / meta_reais) * 100 if meta_reais > 0 else 0

col1, col2, col3 = st.columns([3,2,2])
with col1:
    st.subheader(f"📆 Semana {semana_num}")
    st.markdown(f"**Você atingiu {pct_meta:.1f}% da meta**")
    st.progress(min(pct_meta/100, 1))
with col2:
    st.metric("R$ vendidos", f"R$ {total_vendido:,.2f}")
with col3:
    st.metric("Clientes atendidos", total_clientes)

st.divider()

# ================ ALERTAS =================
st.subheader("🔔 Alertas e prioridades")

planos_rep = planos[planos["representante"] == rep]

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Top 5 clientes com oportunidades (não concluído)**")
    if not planos_rep.empty:
        top = planos_rep[planos_rep["status_acao"] != "Concluído"].sort_values(
            by="valor_vendido", ascending=False
        ).head(5)[["cliente", "cidade", "valor_vendido", "acao_sugerida"]]
        st.table(top.fillna(""))
    else:
        st.write("Nenhum cliente pendente.")

with c2:
    st.markdown("**Top 5 cidades com maior potencial**")
    if not planos_rep.empty:
        cities = planos_rep.groupby("cidade").agg({"valor_vendido":"sum"}).head(5)
        st.table(cities)
    else:
        st.write("Sem ações pendentes.")


st.divider()


# ================ KANBAN =================
st.subheader("🗂️ Kanban de ações")

if planos_rep.empty:
    st.info("Nenhuma ação cadastrada ainda.")
else:
    statuses = ["A Fazer", "Em andamento", "Concluído"]

    # organiza o layout em colunas
    col_a, col_b, col_c = st.columns(3)
    col_dict = {"A Fazer": col_a, "Em andamento": col_b, "Concluído": col_c}

    for idx, row in planos_rep.reset_index().iterrows():
        with col_dict.get(row["status_acao"], col_a):
            st.markdown(f"""
            **{row['cliente']}**  
            {row.get('cidade','')} • {row.get('colecao','')}
            """)
            new_status = st.selectbox(
                "Status",
                statuses,
                index=statuses.index(row["status_acao"]),
                key=f"status_{idx}"
            )
            planos.loc[(planos["representante"] == rep) & (planos["cliente"] == row["cliente"]), "status_acao"] = new_status

            new_comment = st.text_area(
                "Comentários",
                value=row.get("comentarios", ""),
                key=f"comment_{idx}"
            )
            planos.loc[(planos["representante"] == rep) & (planos["cliente"] == row["cliente"]), "comentarios"] = new_comment

if st.button("Salvar atualizações"):
    save_planos(planos)
    st.success("Kanban atualizado com sucesso!")

st.divider()

st.caption("Versão MVP • Dados carregados de Excel • Em desenvolvimento 🚀")






