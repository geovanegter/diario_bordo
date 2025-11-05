import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Diário de Bordo RC", layout="wide")

# =======================
# FUNÇÃO DE AUTENTICAÇÃO
# =======================
def authenticate(email, senha, usuarios_df):
    usuarios_df.columns = usuarios_df.columns.str.lower().str.strip()

    # remove espaços invisíveis das células
    usuarios_df = usuarios_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    st.sidebar.write("DEBUG:", usuarios_df)  # <- remove depois

    user = usuarios_df[
        (usuarios_df["email"].str.lower() == email.strip().lower()) &
        (usuarios_df["senha"] == senha.strip())
    ]

    return not user.empty



# =======================
# CARREGAR PLANILHAS
# =======================
def load_planilha(path, colunas_esperadas=None):
    file_path = Path(path)

    if not file_path.exists():
        # Se o arquivo não existir, cria um DF vazio com colunas mínimas
        return pd.DataFrame(columns=colunas_esperadas or [])

    df = pd.read_excel(file_path)
    df.columns = df.columns.str.lower().str.strip()

    if colunas_esperadas:
        for col in colunas_esperadas:
            if col not in df.columns:
                df[col] = None  # adiciona coluna faltante

    return df


# ==========================
# CARREGAR USUÁRIOS
# ==========================
usuarios_df = load_planilha(
    "dados/usuarios.xlsx",
    colunas_esperadas=["email", "senha", "representante"]
)

# ==========================
# TELA DE LOGIN
# ==========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Diário de Bordo — Login")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if authenticate(email, senha, usuarios_df):
            st.session_state.logged_in = True
            st.session_state.usuario = email

            rep = usuarios_df[usuarios_df["email"] == email]["representante"].iloc[0]
            st.session_state.representante = rep

            st.rerun()
        else:
            st.error("❌ E-mail ou senha incorretos.")

    st.stop()  # Impede que carregue o resto da página antes de logar


# ==========================
# PUXA REPRESENTANTE LOGADO
# ==========================
rep = st.session_state.representante

st.sidebar.write(f"👤 Logado como: **{rep}**")
if st.sidebar.button("Sair"):
    st.session_state.logged_in = False
    st.rerun()


# ==========================
# CARREGA VENDAS & PLANOS
# ==========================
vendas_df = load_planilha(
    "dados/vendas.xlsx",
    colunas_esperadas=[
        "representante","cliente","cidade","colecao","marca","bairro","cep",
        "qtd_pecas","valor_vendido","desconto","prazo"
    ]
)

planos_df = load_planilha(
    "dados/planos_acoes.xlsx",
    colunas_esperadas=[
        "representante","cliente","cidade","acao_sugerida","status_acao","comentarios"
    ]
)

# Filtra vendas por representante logado
vendas_rep = vendas_df[vendas_df["representante"] == rep].copy()


# ==========================
# TELA PRINCIPAL — DASHBOARD
# ==========================
st.title("📊 Diário de Bordo — Representante Comercial")

# KPIs básicos
col1, col2, col3 = st.columns(3)

meta = st.sidebar.number_input("Meta da semana (R$)", value=100000.0)

total_vendido = vendas_rep["valor_vendido"].sum()
perc_meta = (total_vendido / meta * 100) if meta > 0 else 0

col1.metric("Total vendido (semana)", f"R$ {total_vendido:,.2f}")
col2.metric("Meta da semana", f"R$ {meta:,.2f}")
col3.metric("Atingimento", f"{perc_meta:.1f}%")

# ==========================
# TOP CLIENTES NÃO ATENDIDOS
# ==========================
clientes_atendidos = set(vendas_rep["cliente"].unique())

todos_clientes = vendas_df["cliente"].unique()
nao_atendidos = [c for c in todos_clientes if c not in clientes_atendidos]

if nao_atendidos:
    st.subheader("⚠️ Clientes não atendidos")
    st.table(pd.DataFrame({"cliente": nao_atendidos[:5]}))
else:
    st.success("✅ Você atendeu todos os clientes!")

# ==========================
# KANBAN (Ações)
# ==========================
st.subheader("🗂️ Planos de ação")

planos_rep = planos_df[planos_df["representante"] == rep].copy()

col_a, col_b, col_c = st.columns(3)

col_a.write("🟡 **A Fazer**")
col_b.write("🔵 **Em andamento**")
col_c.write("🟢 **Concluído**")

for _, row in planos_rep.iterrows():
    card = f"""
    **{row['cliente']}**  
    📍 {row.get('cidade', '')}  
    ✏️ {row.get('acao_sugerida', '')}
    """
    if row["status_acao"] == "A Fazer":
        col_a.info(card)
    elif row["status_acao"] == "Em Andamento":
        col_b.warning(card)
    else:
        col_c.success(card)









