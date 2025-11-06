import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="📘 Diário de Bordo Comercial", layout="wide")

# -------------------------------
# Funções
# -------------------------------
@st.cache_data
def carregar_planilhas():
    planilhas = {}
    planilhas["usuarios"] = pd.read_excel("dados/usuarios.xlsx") if pd.io.common.file_exists("dados/usuarios.xlsx") else pd.DataFrame()
    planilhas["vendas"] = pd.read_excel("dados/vendas.xlsx") if pd.io.common.file_exists("dados/vendas.xlsx") else pd.DataFrame(columns=[
        "data","representante","cliente","colecao","marca","bairro","cep","qtd_pecas","valor_vendido","desconto","prazo"])
    planilhas["colecoes"] = pd.read_excel("dados/colecoes.xlsx") if pd.io.common.file_exists("dados/colecoes.xlsx") else pd.DataFrame(columns=["colecao"])
    planilhas["metas"] = pd.read_excel("dados/metas_colecao.xlsx") if pd.io.common.file_exists("dados/metas_colecao.xlsx") else pd.DataFrame(columns=["representante","colecao","meta"])
    planilhas["planos"] = pd.read_excel("dados/planos_acoes.xlsx") if pd.io.common.file_exists("dados/planos_acoes.xlsx") else pd.DataFrame(columns=["responsavel","acao","status"])
    return planilhas

def autenticar(email, senha):
    usuarios = dfs["usuarios"]
    if usuarios.empty: return None
    usuarios["email"] = usuarios["email"].astype(str)
    usuarios["senha"] = usuarios["senha"].astype(str)
    user = usuarios[(usuarios["email"].str.lower() == email.lower()) & (usuarios["senha"] == senha)]
    return user.iloc[0].to_dict() if len(user)==1 else None

def coluna_valor_existe(df, coluna):
    return df[coluna] if coluna in df.columns else pd.Series([0]*len(df))

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
            if user:
                st.session_state.logado = True
                st.session_state.user = user
                st.success("✅ Login realizado!")
            else:
                st.error("❌ Usuário ou senha inválidos!")

# -------------------------------
# TELA PRINCIPAL
# -------------------------------
if st.session_state.logado:
    user = st.session_state.user
    representante = user.get("representante","Não definido")
    nome_usuario = user.get("nome","Usuário")

    # Sidebar
    st.sidebar.title(f"👋 Olá, {nome_usuario}")
    st.sidebar.write(f"Representante: **{representante}**")
    paginas = ["Dashboard","Registrar visita","Plano de Ação","Coleções / Metas"]
    for p in paginas:
        if st.sidebar.button(f"{'👉 ' if st.session_state.get('pagina_atual')==p else ''}{p}"):
            st.session_state.pagina_atual = p

    pagina = st.session_state.get("pagina_atual","Dashboard")

    # -------------------------------
    # DASHBOARD MODERNO
    # -------------------------------
    if pagina == "Dashboard":
        st.title("📊 Dashboard Comercial")
        vendas = dfs["vendas"]
        metas = dfs["metas"]

        vendas_rep = vendas[vendas.get("representante","")==representante]
        metas_rep = metas[metas.get("representante","")==representante]

        total_vendido = coluna_valor_existe(vendas_rep,"valor_vendido").sum()
        meta_total = coluna_valor_existe(metas_rep,"meta").sum()
        progresso = total_vendido/meta_total if meta_total>0 else 0

        # Métricas principais
        col1,col2,col3 = st.columns(3)
        col1.metric("💰 Total Vendido",f"R$ {total_vendido:,.2f}".replace(",","."))
        col2.metric("🎯 Meta Total",f"R$ {meta_total:,.2f}".replace(",","."))
        col3.progress(progresso)

        # Cálculo venda diária necessária
        hoje = datetime.now().date()
        ultimo_dia_mes = datetime(hoje.year, hoje.month+1,1) - timedelta(days=1) if hoje.month<12 else datetime(hoje.year,12,31)
        dias_restantes = (ultimo_dia_mes.date() - hoje).days + 1
        venda_diaria_necessaria = (meta_total - total_vendido)/dias_restantes if dias_restantes>0 else 0

        # Estimativa de clientes por dia (supomos ticket médio)
        ticket_medio = vendas_rep["valor_vendido"].mean() if not vendas_rep.empty else 1000
        clientes_por_dia = venda_diaria_necessaria/ticket_medio if ticket_medio>0 else 0

        st.subheader("📅 Planejamento Diário")
        col1,col2 = st.columns(2)
        col1.metric("💵 Venda diária necessária",f"R$ {venda_diaria_necessaria:,.2f}".replace(",","."))
        col2.metric("👥 Clientes por dia",f"{clientes_por_dia:.1f}")

    # -------------------------------
    # REGISTRAR VISITA
    # -------------------------------
    elif pagina=="Registrar visita":
        st.title("📝 Registro de Visitas")
        colecoes = dfs["colecoes"]
        with st.form("form_visita"):
            col1,col2 = st.columns(2)
            cliente = col1.text_input("Cliente")
            colecao = col2.selectbox("Coleção",colecoes["colecao"].unique())
            valor = st.number_input("Valor do pedido (R$)",step=100.0)
            enviado = st.form_submit_button("💾 Salvar registro")
            if enviado:
                novo = pd.DataFrame([{
                    "data":datetime.now(),
                    "representante":representante,
                    "cliente":cliente,
                    "colecao":colecao,
                    "marca":"",
                    "bairro":"",
                    "cep":"",
                    "qtd_pecas":0,
                    "valor_vendido":valor,
                    "desconto":0,
                    "prazo":"",
                }])
                dfs["vendas"] = pd.concat([dfs["vendas"],novo],ignore_index=True)
                dfs["vendas"].to_excel("dados/vendas.xlsx",index=False)
                st.success("✅ Visita registrada!")

    # -------------------------------
    # PLANOS DE AÇÃO
    # -------------------------------
    elif pagina=="Plano de Ação":
        st.title("🚀 Plano de Ação Comercial")
        planos = dfs["planos"]
        planos_rep = planos[planos.get("responsavel","")==representante]
        if planos_rep.empty:
            st.info("Nenhum plano de ação para este representante.")
        else:
            def style_status(val):
                color = cor_status(val)
                return f'background-color: {color}; color:white; font-weight:bold'
            st.dataframe(planos_rep.style.applymap(style_status,subset=["status"]))

    # -------------------------------
    # COLEÇÕES / METAS
    # -------------------------------
    elif pagina=="Coleções / Metas":
        st.title("🏆 Metas por Coleção")
        metas_rep = metas[metas.get("representante","")==representante]
        for _,row in metas_rep.iterrows():
            colecao = row.get("colecao","Não definido")
            meta = row.get("meta",0)
            vendido = coluna_valor_existe(
                vendas[
                    (vendas.get("representante","")==representante)&
                    (vendas.get("colecao","")==colecao)
                ],
                "valor_vendido"
            ).sum()
            progresso = vendido/meta if meta>0 else 0
            st.subheader(f"📦 {colecao}")
            st.progress(progresso)
            st.write(f"Vendido: **R$ {vendido:,.2f}** de R$ {meta:,.2f}".replace(",","."))
            
    # -------------------------------
    # LOGOUT
    # -------------------------------
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.logado = False
        st.session_state.pagina_atual="Dashboard"
        st.success("✅ Logout realizado! Atualize a página para logar novamente.")
