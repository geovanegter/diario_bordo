import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="📘 Diário de Bordo Comercial", layout="wide")

# ---------------------------------------------------------
# 🌈 ESTILO GLOBAL (tema moderno + hover)
# ---------------------------------------------------------
st.markdown("""
<style>

/* Tipografia */
html, body, [class*="css"] {
    font-family: "Inter", sans-serif !important;
    background-color: #F5F6FA !important;
}

/* Oculta menu padrão */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #E4E6EB;
    padding-top: 30px;
}

/* Botões do menu */
.sidebar-button {
    background-color: transparent;
    padding: 12px 16px;
    width: 100%;
    border-radius: 10px;
    cursor: pointer;
    color: #333;
    font-weight: 500;
    text-align: left;
    margin-bottom: 6px;
    transition: all .25s ease-in-out;
    border: none;
}

.sidebar-button:hover {
    background-color: #e5e7ff;
    transform: translateX(4px);
    color: #3f51b5;
}

.selected {
    background-color: #3f51b5 !important;
    color: white !important;
}

/* Botões principais (Salvar etc.) */
button[kind="primary"] {
    background-color: #3f51b5 !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    transition: all .25s ease-in-out;
}
button[kind="primary"]:hover {
    transform: translateY(-2px);
    background-color: #2d3b9f !important;
}

/* Cards */
.card {
    background: white;
    padding: 20px 25px;
    border-radius: 15px;
    border: 1px solid #E5E6EB;
    box-shadow: 0px 6px 16px rgba(0,0,0,0.06);
    transition: all .25s ease-in-out;
}
.card:hover {
    transform: translateY(-3px);
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# CONTROLE DE ESTADO
# -----------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "user" not in st.session_state:
    st.session_state["user"] = None


# ---------------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------------
@st.cache_data
def carregar_planilhas():
    planilhas = {}

    planilhas["usuarios"] = pd.read_excel("dados/usuarios.xlsx")
    planilhas["vendas"] = pd.read_excel("dados/vendas.xlsx")
    planilhas["colecoes"] = pd.read_excel("dados/colecoes.xlsx")
    planilhas["metas"] = pd.read_excel("dados/metas_colecao.xlsx")
    planilhas["planos"] = pd.read_excel("dados/planos_acoes.xlsx")

    return planilhas


def autenticar(email, senha):
    usuarios = dfs["usuarios"]
    user = usuarios[
        (usuarios["email"].str.lower() == email.lower()) &
        (usuarios["senha"] == senha)
    ]
    return user.iloc[0].to_dict() if len(user) == 1 else None


def cor_status(status):
    cores = {"Concluído": "#28a745", "Em andamento": "#ffc107", "Pendente": "#dc3545"}
    return cores.get(status, "#6c757d")


def coluna(df, nome):
    """Evita erro se coluna não existir"""
    return df[nome] if nome in df.columns else pd.Series([0] * len(df))


# ---------------------------------------------------------
# CARREGAR PLANILHAS
# ---------------------------------------------------------
dfs = carregar_planilhas()


# ---------------------------------------------------------
# SESSÃO / LOGIN
# ---------------------------------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = None
    st.session_state.pagina_atual = "Dashboard"

if not st.session_state.logado:
    st.title("🔐 Diário de Bordo — Login")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

        if entrar:
            user = autenticar(email, senha)
            if user:
                st.session_state.logado = True
                st.session_state.user = user
                st.success("✅ Login realizado!")
            else:
                st.error("❌ Usuário ou senha inválidos!")


# ---------------------------------------------------------
# APLICATIVO
# ---------------------------------------------------------
if st.session_state.logado:

    user = st.session_state.user
    representante = user.get("representante", "Não definido")

    # Sidebar navigation customizado
    st.sidebar.title(f"👋 Olá, {user.get('nome')}")

    paginas = ["Dashboard", "Registrar visita", "Plano de Ação", "Coleções / Metas"]

    for p in paginas:
        classe = "selected" if st.session_state.pagina_atual == p else ""
        if st.sidebar.button(p, key=p, use_container_width=True):
            st.session_state.pagina_atual = p

    pagina = st.session_state.pagina_atual


    # =====================================================
    # DASHBOARD
    # =====================================================
    if pagina == "Dashboard":
        st.title("📊 Dashboard Comercial")

        vendas = dfs["vendas"]
        metas = dfs["metas"]

        vendas_rep = vendas[vendas["representante"] == representante]
        metas_rep = metas[metas["representante"] == representante]

        total_vendido = coluna(vendas_rep, "valor_vendido").sum()
        meta_total = coluna(metas_rep, "meta").sum()
        progresso = total_vendido / meta_total if meta_total > 0 else 0

        hoje = datetime.now().date()
        ultimo_dia_mes = datetime(hoje.year, hoje.month + (1 if hoje.month < 12 else 0), 1) - timedelta(days=1)
        dias_restantes = (ultimo_dia_mes.date() - hoje).days + 1

        venda_dia = max((meta_total - total_vendido) / dias_restantes, 0)
        ticket = vendas_rep["valor_vendido"].mean() if not vendas_rep.empty else 800
        clientes_dia = venda_dia / ticket if ticket > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f"<div class='card'><h3>💰 Total Vendido</h3><h2>R$ {total_vendido:,.2f}</h2></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='card'><h3>🎯 Meta do mês</h3><h2>R$ {meta_total:,.2f}</h2></div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='card'><h3>📅 Venda diária necessária</h3><h2>R$ {venda_dia:,.2f}</h2></div>", unsafe_allow_html=True)

        st.write(" ")
        st.write(f"👥 Média de clientes/dia necessária: **{clientes_dia:.1f}**")


    # =====================================================
    # REGISTRAR VISITA (com localização)
    # =====================================================
    if pagina == "Registrar visita":
        st.title("📝 Registro de Visitas")

        colecoes = dfs["colecoes"]

        # pega localização do navegador
        st.components.v1.html("""
        <script>
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const coords = pos.coords.latitude + "," + pos.coords.longitude;
                window.parent.postMessage({location: coords}, "*");
            }
        );
        </script>
        """, height=0)

        msg = st.experimental_get_query_params()
        if "location" in msg:
            st.session_state.location = msg["location"][0]

        with st.form("form_visita"):

            cliente = st.text_input("Cliente")
            colecao = st.selectbox("Coleção", colecoes["colecao"].unique())
            valor = st.number_input("Valor do pedido (R$)", step=100.0)

            enviar = st.form_submit_button("💾 Salvar registro")

            if enviar:
                novo = pd.DataFrame([{
                    "data": datetime.now(),
                    "representante": representante,
                    "cliente": cliente,
                    "colecao": colecao,
                    "valor_vendido": valor,
                }])

                dfs["vendas"] = pd.concat([dfs["vendas"], novo], ignore_index=True)
                dfs["vendas"].to_excel("dados/vendas.xlsx", index=False)

                st.success("✅ Visita registrada!")


    # =====================================================
    # PLANOS DE AÇÃO
    # =====================================================
    if pagina == "Plano de Ação":
        st.title("🚀 Plano de Ação Comercial")

        planos = dfs["planos"]
        planos_rep = planos[planos["responsavel"] == representante]

        st.table(planos_rep)


    # =====================================================
    # METAS / COLEÇÕES
    # =====================================================
    if pagina == "Coleções / Metas":
        st.title("🏆 Metas por Coleção")

        metas_rep = metas[metas["representante"] == representante]

        for _, row in metas_rep.iterrows():
            colecao = row["colecao"]
            meta = row["meta"]

            vendido = vendas[(vendas["representante"] == representante) & 
                             (vendas["colecao"] == colecao)]["valor_vendido"].sum()

            progresso = vendido / meta if meta > 0 else 0

            st.write(f"### {colecao}")
            st.progress(progresso)
            st.write(f"Vendido: **R$ {vendido:,.2f}** de R$ {meta:,.2f}")


    # LOGOUT
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

