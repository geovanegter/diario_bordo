import streamlit as st
import pandas as pd
import datetime

# ---------------------------
# CONFIGURAÇÃO DO APP
# ---------------------------
st.set_page_config(page_title="Diário de Bordo", layout="wide")

# ---------------------------
# FUNÇÃO PARA CARREGAR PLANILHAS
# ---------------------------
@st.cache_data
def carregar_planilhas():
    usuarios_df = pd.read_excel("dados/usuarios.xlsx")
    vendas_df = pd.read_excel("dados/vendas.xlsx")
    metas_df = pd.read_excel("dados/metas.xlsx")
    metas_semanais_df = pd.read_excel("dados/meta_semanal.xlsx")
    return usuarios_df, vendas_df, metas_df, metas_semanais_df

usuarios_df, vendas_df, metas_df, metas_semanais_df = carregar_planilhas()

# ---------------------------
# INICIALIZA SESSION
# ---------------------------
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Dashboard"

# ======================================================
# 🔐 TELA DE LOGIN
# ======================================================
if not st.session_state["logado"]:

    st.title("🔐 Acesso ao Diário de Bordo")

    email_input = st.text_input("Email").strip()
    senha_input = st.text_input("Senha", type="password").strip()

    # 🔍 DEBUG TEMPORÁRIO PARA DESCOBRIR O ERRO
    st.write("### 🔍 DEBUG (remover depois)")
    st.write("Usuários carregados da planilha:")
    st.dataframe(usuarios_df)
    st.write("Email digitado:", email_input)
    st.write("Senha digitada:", senha_input)

    # Normalização para evitar erro de espaços e maiúsculas
    usuarios_df["email"] = usuarios_df["email"].astype(str).str.strip().str.lower()
    usuarios_df["senha"] = usuarios_df["senha"].astype(str).str.strip()

    email_normalizado = email_input.lower()

    usuario = usuarios_df[
        (usuarios_df["email"] == email_normalizado) &
        (usuarios_df["senha"] == senha_input)
    ]

    if st.button("Entrar"):
        if not usuario.empty:
            st.session_state["logado"] = True
            st.session_state["usuario"] = usuario.iloc[0]["email"]
            st.session_state["representante"] = usuario.iloc[0]["representante"]
            st.experimental_rerun()
        else:
            st.error("❌ Usuário ou senha incorretos. Confira a planilha `usuarios.xlsx`.")

    st.stop()  # impede o restante do app de carregar

# ======================================================
# ✅ ÁREA LOGADA
# ======================================================

st.sidebar.title(f"👋 Olá, {st.session_state['representante']}")
paginas = ["Dashboard", "Clientes", "Ranking", "Dossiê Cliente"]
pagina = st.sidebar.radio("Navegação", paginas)

# ---------------------------
# CARREGAMENTOS
# ---------------------------
representante = st.session_state['representante']
vendas_rep = vendas_df[vendas_df["representante"] == representante]

# ---------------------------
# DASHBOARD
# ---------------------------
if pagina == "Dashboard":
    st.title("📊 Dashboard de Vendas")

    meta = metas_df[metas_df["representante"] == representante]

    if not meta.empty:
        meta_valor = float(meta.iloc[0]["meta_vendas"])
        meta_clientes = int(meta.iloc[0]["meta_clientes"])
    else:
        meta_valor = 0
        meta_clientes = 0

    total_vendido = vendas_rep["valor_vendido"].sum()
    porcentagem_meta = (total_vendido / meta_valor) * 100 if meta_valor > 0 else 0

    # Barra de progresso
    st.subheader(f"🏁 Você atingiu **{porcentagem_meta:.1f}%** da meta da coleção")
    st.progress(min(porcentagem_meta / 100, 1.0))

    # Cálculo semanal
    hoje = datetime.date.today()
    semana_atual = metas_semanais_df[
        (metas_semanais_df["representante"] == representante)
        & (pd.to_datetime(metas_semanais_df["semana_inicio"]).dt.date <= hoje)
        & (pd.to_datetime(metas_semanais_df["semana_fim"]).dt.date >= hoje)
    ]

    if not semana_atual.empty:
        semana_meta_valor = semana_atual.iloc[0]["meta_semanal"]
        ticket_medio_planejado = meta_valor / meta_clientes if meta_clientes > 0 else 0
        clientes_necessarios = semana_meta_valor / ticket_medio_planejado if ticket_medio_planejado > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Meta de vendas da semana", f"R$ {semana_meta_valor:,.2f}")
        col2.metric("Ticket médio previsto", f"R$ {ticket_medio_planejado:,.2f}")
        col3.metric("Clientes necessários na semana", f"{clientes_necessarios:.1f}")
    else:
        st.warning("Nenhuma meta semanal configurada para esta data.")

# ---------------------------
# CLIENTES
# ---------------------------
elif pagina == "Clientes":
    st.title("👥 Clientes")
    st.dataframe(vendas_rep[["cliente", "cidade", "valor_vendido"]].sort_values("cliente"))

# ---------------------------
# RANKING DE VENDAS
# ---------------------------
elif pagina == "Ranking":
    st.title("🏆 Ranking de Clientes")

    ranking = vendas_rep.groupby("cliente")["valor_vendido"].sum().reset_index()
    ranking = ranking.sort_values("valor_vendido", ascending=False)
    st.dataframe(ranking)

# ---------------------------
# DOSSIÊ CLIENTE
# ---------------------------
elif pagina == "Dossiê Cliente":
    st.title("📂 Dossiê do Cliente")
    cliente_sel = st.selectbox("Selecione o cliente", vendas_rep["cliente"].unique())
    st.dataframe(vendas_rep[vendas_rep["cliente"] == cliente_sel])
