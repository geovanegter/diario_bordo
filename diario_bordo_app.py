import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="Diário de Bordo Comercial",
    layout="wide",
)

# -----------------------------------------
# CSS GLOBAL (tema moderno / hover)
# -----------------------------------------
st.markdown("""
    <style>
        * {
            font-family: 'Inter', sans-serif !important;
        }

        /* sidebar */
        section[data-testid="stSidebar"] {
            background: #F7F7F7;
            padding-top: 30px;
        }

        .menu-btn {
            padding: 12px 18px;
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            font-weight: 500;
            color: #444;
            transition: all 0.15s ease;
            background: #ffffff;
            border: 1px solid #e6e6e6;
            text-align: left;
        }

        .menu-btn:hover {
            border-color: #007bff;
            color: #007bff;
        }

        .menu-active {
            background: #007bff;
            color: white !important;
            border-color: #007bff;
        }

    </style>
""", unsafe_allow_html=True)

# -----------------------------------------
# SESSION STATE (autenticação)
# -----------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Dashboard"

# -----------------------------------------
# CARREGAR DADOS
# -----------------------------------------
def carregar_planilha(nome):
    try:
        return pd.read_excel(Path("./dados") / nome)
    except:
        return pd.DataFrame()

usuarios_df = carregar_planilha("usuarios.xlsx")
vendas_df = carregar_planilha("vendas.xlsx")
metas_df = carregar_planilha("metas_colecao.xlsx")

# -----------------------------------------
# TELA DE LOGIN
# -----------------------------------------
if not st.session_state.authenticated:

    st.markdown("<h2 style='text-align:center; margin-top: 80px;'>🚀 Diário de Bordo Comercial</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Acesse com seu usuário e senha</p>", unsafe_allow_html=True)

    with st.form("login", clear_on_submit=False):
        email = st.text_input("E-mail:")
        senha = st.text_input("Senha:", type="password")
        logar = st.form_submit_button("Entrar")

    if logar:

        # Normaliza colunas (remove espaços e garante lowercase)
        usuarios_df.columns = usuarios_df.columns.str.strip().str.lower()

        user_row = usuarios_df[
            (usuarios_df["email"].str.lower() == email.lower()) &
            (usuarios_df["senha"].astype(str) == senha)
        ]

        if not user_row.empty:
            st.session_state.authenticated = True
            st.session_state.user = user_row.to_dict(orient="records")[0]
            st.rerun()
        else:
            st.error("❌ Usuário ou senha inválidos")

    st.stop()


# -----------------------------------------
# USUÁRIO LOGADO
# -----------------------------------------
usuario_logado = st.session_state.user.get("usuario")
representante = st.session_state.user.get("representante")

# -----------------------------------------
# FUNÇÃO PARA MENU
# -----------------------------------------
def menu_item(nome):
    active_class = "menu-active" if st.session_state.pagina_atual == nome else ""
    if st.sidebar.button(nome, key=nome, use_container_width=True):
        st.session_state.pagina_atual = nome
    st.sidebar.markdown(f"""
        <style>
            [key="{nome}"] button {{
                border-radius: 8px !important;
            }}
            .stButton > button.{active_class} {{
                background: #007bff !important;
                color: white !important;
            }}
        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------
# SIDEBAR (MENU)
# -----------------------------------------
st.sidebar.markdown(f"👤 Logado como: **{usuario_logado}** — {representante}")
st.sidebar.write("---")

menu_item("Dashboard")
menu_item("Registrar Visita")
menu_item("Plano de Ação")
menu_item("Metas")

st.sidebar.write("---")
if st.sidebar.button("🚪 Sair"):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

# =========================================
#  PAGINAS
# =========================================

# --------------- DASHBOARD ----------------
if st.session_state.pagina_atual == "Dashboard":

    vendas_rep = vendas_df[vendas_df["representante"] == representante]

    total_vendido = vendas_rep["valor_vendido"].sum()
    total_clientes = vendas_rep["cliente"].nunique()

    meta_row = metas_df[metas_df["representante"] == representante]
    meta_valor = meta_row["meta_vendas"].sum() if not meta_row.empty else 0
    meta_clientes = meta_row["meta_clientes"].sum() if not meta_row.empty else 0

    hoje = datetime.now().day
    dias_no_mes = 30
    dias_restantes = dias_no_mes - hoje

    falta_vender = max(meta_valor - total_vendido, 0)
    vender_por_dia = falta_vender / dias_restantes if dias_restantes > 0 else falta_vender

    falta_clientes = max(meta_clientes - total_clientes, 0)
    clientes_por_dia = falta_clientes / dias_restantes if dias_restantes > 0 else falta_clientes

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Total vendido", f"R$ {total_vendido:,.2f}")
    col2.metric("🎯 Meta do mês", f"R$ {meta_vendas:,.2f}")
    col3.metric("📅 Vender por dia", f"R$ {vender_por_dia:,.2f}")
    col4.metric("👥 Clientes por dia", f"{clientes_por_dia:.1f}")

# --------------- REGISTRAR VISITA ----------------
elif st.session_state.pagina_atual == "Registrar Visita":

    st.markdown("### 📝 Registrar visita")

    with st.form("visita"):
        cliente = st.text_input("Cliente:")
        cidade = st.text_input("Cidade:")
        colecao = st.text_input("Coleção visitada:")
        valor = st.number_input("Valor vendido", min_value=0.0)
        registrar = st.form_submit_button("Salvar")

    if registrar:
        novo = pd.DataFrame([{
            "data": datetime.now(),
            "representante": representante,
            "cliente": cliente,
            "cidade": cidade,
            "colecao": colecao,
            "valor_vendido": valor
        }])
        vendas_df = pd.concat([vendas_df, novo], ignore_index=True)
        vendas_df.to_excel("./dados/vendas.xlsx", index=False)
        st.success("✅ Visita registrada com sucesso!")

# --------------- PLANO DE AÇÃO ----------------
elif st.session_state.pagina_atual == "Plano de Ação":
    st.markdown("### 🧠 Plano de Ação")
    st.info("Em breve… módulo para registro de ações, follow-ups e prioridades.")

# --------------- METAS ----------------
elif st.session_state.pagina_atual == "Metas":
    st.markdown("### 🎯 Metas e Coleções")
    st.dataframe(metas_df[metas_df["representante"] == representante])






