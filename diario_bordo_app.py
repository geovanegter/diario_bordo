import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="📘 Diário de Bordo Comercial", layout="wide")

# -------------------------------
# Funções
# -------------------------------
@st.cache_data
def carregar_planilhas():
    planilhas = {}
    try:
        planilhas["usuarios"] = pd.read_excel("dados/usuarios.xlsx")
    except:
        st.error("Planilha 'usuarios.xlsx' não encontrada!")
        planilhas["usuarios"] = pd.DataFrame()

    try:
        planilhas["vendas"] = pd.read_excel("dados/vendas.xlsx")
    except:
        st.warning("Planilha 'vendas.xlsx' não encontrada, será criada ao registrar vendas.")
        planilhas["vendas"] = pd.DataFrame(columns=["data","representante","cliente","colecao","valor"])

    try:
        planilhas["colecoes"] = pd.read_excel("dados/colecoes.xlsx")
    except:
        st.warning("Planilha 'colecoes.xlsx' não encontrada!")
        planilhas["colecoes"] = pd.DataFrame(columns=["colecao"])

    try:
        planilhas["metas"] = pd.read_excel("dados/metas_colecao.xlsx")
    except:
        st.warning("Planilha 'metas_colecao.xlsx' não encontrada!")
        planilhas["metas"] = pd.DataFrame(columns=["representante","colecao","meta"])

    try:
        planilhas["planos"] = pd.read_excel("dados/planos_acoes.xlsx")
    except:
        st.warning("Planilha 'planos_acoes.xlsx' não encontrada!")
        planilhas["planos"] = pd.DataFrame(columns=["responsavel","acao","status"])

    return planilhas

def autenticar(email, senha):
    usuarios = dfs["usuarios"]

    if usuarios.empty:
        return None

    usuarios["email"] = usuarios["email"].astype(str)
    usuarios["senha"] = usuarios["senha"].astype(str)

    user = usuarios[
        (usuarios["email"].str.lower() == email.lower()) &
        (usuarios["senha"] == senha)
    ]

    if len(user) == 1:
        return user.iloc[0].to_dict()
    return None

def coluna_valor_existe(df, coluna):
    if coluna in df.columns:
        return df[coluna]
    else:
        return pd.Series([0]*len(df))

# Função para colorir status
def cor_status(status):
    cores = {"Concluído":"#28a745", "Em andamento":"#ffc107", "Pendente":"#dc3545"}
    return cores.get(status, "#6c757d")

# -------------------------------
# Carrega planilhas
# -------------------------------
dfs = carregar_planilhas()

# -------------------------------
# Sessão inicial
# -------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = None
    st.session_state.pagina_atual = "Dashboard"

# -------------------------------
# LOGIN
# -------------------------------
if not st.session_state.logado:
    st.title("🔐 Diário de Bordo — Login")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviar = st.form_submit_button("Entrar")

        if enviar:
            user = autenticar(email, senha)

            if user is not None:
                st.session_state.logado = True
                st.session_state.user = user
                st.success("✅ Login realizado! Use os botões ao lado para navegar.")
            else:
                st.error("❌ Usuário ou senha inválidos!")

# -------------------------------
# TELA PRINCIPAL (apenas se logado)
# -------------------------------
if st.session_state.logado:
    user = st.session_state.user
    representante = user.get("representante", "Não definido")
    nome_usuario = user.get("nome", "Usuário")

    # -------------------------------
    # Sidebar com menu ativo
    # -------------------------------
    st.sidebar.title(f"👋 Olá, {nome_usuario}")
    st.sidebar.write(f"Representante: **{representante}**")

    paginas = ["Dashboard", "Registrar visita", "Plano de Ação", "Coleções / Metas"]
    st.sidebar.write("## Menu")
    for p in paginas:
        if st.sidebar.button(f"{'👉 ' if st.session_state.get('pagina_atual')==p else ''}{p}"):
            st.session_state["pagina_atual"] = p

    pagina = st.session_state.get("pagina_atual", "Dashboard")

    # -------------------------------
    # DASHBOARD MODERNO
    # -------------------------------
    if pagina == "Dashboard":
        st.title("📊 Dashboard Comercial")
        vendas = dfs["vendas"]
        metas = dfs["metas"]

        vendas_rep = vendas[vendas.get("representante", "") == representante]
        metas_rep = metas[metas.get("representante", "") == representante]

        total_vendido = coluna_valor_existe(vendas_rep, "valor").sum()
        meta_total = coluna_valor_existe(metas_rep, "meta").sum()
        progresso = total_vendido / meta_total if meta_total > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Vendido", f"R$ {total_vendido:,.2f}".replace(",", "."))
        col2.metric("🎯 Meta Período", f"R$ {meta_total:,.2f}".replace(",", "."))
        col3.progress(progresso)

        # Gráfico simples de vendas por coleção
        vendas_por_colecao = vendas_rep.groupby("colecao")["valor"].sum()
        if not vendas_por_colecao.empty:
            st.subheader("📈 Vendas por Coleção")
            st.bar_chart(vendas_por_colecao)

    # -------------------------------
    # REGISTRAR VISITA
    # -------------------------------
    elif pagina == "Registrar visita":
        st.title("📝 Registro de Visitas")
        vendas = dfs["vendas"]
        colecoes = dfs["colecoes"]

        with st.form("form_visita"):
            col1, col2 = st.columns(2)
            cliente = col1.text_input("Cliente")
            colecao = col2.selectbox("Coleção", colecoes["colecao"].unique())
            valor = st.number_input("Valor do pedido (R$)", step=100.0)
            enviado = st.form_submit_button("💾 Salvar registro")

            if enviado:
                novo = pd.DataFrame([{
                    "data": datetime.now(),
                    "representante": representante,
                    "cliente": cliente,
                    "colecao": colecao,
                    "valor": valor,
                }])
                dfs["vendas"] = pd.concat([dfs["vendas"], novo], ignore_index=True)
                dfs["vendas"].to_excel("dados/vendas.xlsx", index=False)
                st.success("✅ Visita registrada!")

    # -------------------------------
    # PLANOS DE AÇÃO
    # -------------------------------
    elif pagina == "Plano de Ação":
        st.title("🚀 Plano de Ação Comercial")
        planos = dfs["planos"]
        planos_rep = planos[planos.get("responsavel", "") == representante]

        if planos_rep.empty:
            st.info("Nenhum plano de ação para este representante.")
        else:
            # tabela com cores no status
            def style_status(val):
                color = cor_status(val)
                return f'background-color: {color}; color: white; font-weight: bold'

            st.dataframe(planos_rep.style.applymap(style_status, subset=["status"]))

    # -------------------------------
    # COLEÇÕES / METAS
    # -------------------------------
    elif pagina == "Coleções / Metas":
        st.title("🏆 Metas por Coleção")
        metas = dfs["metas"]
        vendas = dfs["vendas"]

        metas_rep = metas[metas.get("representante", "") == representante]

        for _, row in metas_rep.iterrows():
            colecao = row.get("colecao", "Não definido")
            meta = row.get("meta", 0)

            vendido = coluna_valor_existe(
                vendas[
                    (vendas.get("representante", "") == representante) &
                    (vendas.get("colecao", "") == colecao)
                ],
                "valor"
            ).sum()

            progresso = vendido / meta if meta > 0 else 0
            st.subheader(f"📦 {colecao}")
            st.progress(progresso)
            st.write(f"Vendido: **R$ {vendido:,.2f}** de R$ {meta:,.2f}".replace(",", "."))

    # -------------------------------
    # LOGOUT
    # -------------------------------
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.logado = False
        st.session_state.pagina_atual = "Dashboard"
        st.success("✅ Logout realizado! Atualize a página para logar novamente.")
