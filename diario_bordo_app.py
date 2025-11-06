import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

# ================================
# CONFIGURAÇÕES DO APP
# ================================
st.set_page_config(
    page_title="Diário de Bordo Comercial",
    layout="wide",
    page_icon="📘"
)

# ================================
# ESTILO (CSS)
# ================================
st.markdown("""
<style>

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

/* Header */
.header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 30px;
    background: white;
    border-bottom: 1px solid #E7E7E7;
    margin-bottom: 25px;
}
.avatar {
    width: 58px;
    height: 58px;
    border-radius: 50%;
    background: #d1d1d1;
}
.username {
    font-size: 20px;
    font-weight: 600;
}
.city {
    color: #666;
    font-size: 14px;
}

/* Botões de navegação */
.nav-container {
    display: flex;
    gap: 12px;
    margin-bottom: 25px;
}
.nav-btn {
    padding: 10px 18px;
    border-radius: 8px;
    background: #F7F7F7;
    border: 1px solid #DDD;
    cursor: pointer;
    transition: 0.2s;
}
.nav-btn:hover {
    background: #ececec;
}
.nav-btn-selected {
    background: #0066ff !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# ================================
# FUNÇÃO PARA CARREGAR PLANILHAS
# ================================
@st.cache_data
def carregar_planilhas():
    return {
        "usuarios": pd.read_excel("dados/usuarios.xlsx"),
        "vendas": pd.read_excel("dados/vendas.xlsx"),
        "metas": pd.read_excel("dados/metas_colecao.xlsx")
    }


dfs = carregar_planilhas()

# ================================
# AUTENTICAÇÃO
# ================================
def autenticar(email, senha):
    usuarios = dfs["usuarios"]

    # Garantir comparação evitando erro com tipos
    usuarios["email"] = usuarios["email"].astype(str)
    usuarios["senha"] = usuarios["senha"].astype(str)

    user = usuarios[
        (usuarios["email"].str.lower() == email.lower()) &
        (usuarios["senha"] == senha)
    ]

    if len(user) == 1:
        return user.iloc[0].to_dict()

    return None


# ================================
# LOGIN
# ================================
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = None
    st.session_state.pagina = "Dashboard"

if not st.session_state.logado:
    st.title("🔐 Acesso ao Diário de Bordo")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviar = st.form_submit_button("Entrar")

        if enviar:
            user = autenticar(email, senha)

            if user:
                st.session_state.logado = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("❌ Email ou senha inválidos!")
                st.stop()


# ==================================
# TELA PRINCIPAL
# ==================================
user = st.session_state.user
representante = user["representante"]

# === pegar localização com JS ===
coords = streamlit_js_eval(
    js_expression="navigator.geolocation.getCurrentPosition((pos)=>pos.coords.latitude + ',' + pos.coords.longitude);",
    key="getLocation"
)

cidade = "Localização não encontrada"
if coords:
    cidade = "📍 Usuário conectado"


# HEADER
st.markdown(f"""
<div class="header">
    <img src="https://ui-avatars.com/api/?name={representante}&background=random" class="avatar" />
    <div>
        <div class="username">{representante}</div>
        <div class="city">{cidade}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ================================
# Navegação com botões
# ================================
paginas = ["Dashboard", "Registrar Visita", "Metas"]

col1, col2, col3 = st.columns([1, 1, 1])
botoes = [col1, col2, col3]

for i, pagina in enumerate(paginas):
    if botoes[i].button(
        pagina,
        key=pagina,
    ):
        st.session_state.pagina = pagina
        st.rerun()

# Marcar botão selecionado
st.markdown("""
<script>
const selected = document.querySelector(`button[kind="primary"].st-emotion-cache-1wivap2`);
</script>
""", unsafe_allow_html=True)


# ================================
# CONTEÚDO DAS PÁGINAS
# ================================
pagina = st.session_state.pagina


# ---------------- DASHBOARD ----------------
if pagina == "Dashboard":

    vendas = dfs["vendas"]
    vendas_rep = vendas[vendas["representante"] == representante]

    total_vendido = vendas_rep["valor_vendido"].sum()

    metas = dfs["metas"]
    meta_do_rep = metas[metas["representante"] == representante]["meta_vendas"].sum()

    falta_vender = max(meta_do_rep - total_vendido, 0)

    st.subheader("📊 Progresso da Meta")
    st.metric("Total vendido", f"R$ {total_vendido:,.2f}")
    st.metric("Meta restante", f"R$ {falta_vender:,.2f}")


# ---------------- REGISTRAR VISITA ----------------
elif pagina == "Registrar Visita":

    vendas = dfs["vendas"]

    st.subheader("📝 Novo Registro de Visita")

    cliente = st.text_input("Cliente")
    colecao = st.text_input("Coleção")
    valor = st.number_input("Valor vendido (R$)", step=100.0)

    if st.button("Salvar registro"):
        novo = pd.DataFrame([{
            "data": datetime.now(),
            "representante": representante,
            "cliente": cliente,
            "colecao": colecao,
            "valor_vendido": valor,
        }])

        dfs["vendas"] = pd.concat([dfs["vendas"], novo], ignore_index=True)
        dfs["vendas"].to_excel("dados/vendas.xlsx", index=False)

        st.success("✅ Visita registrada com sucesso!")


# ---------------- METAS ----------------
elif pagina == "Metas":

    metas = dfs["metas"]
    metas_rep = metas[metas["representante"] == representante]

    st.subheader("🏆 Metas do representante")
    st.dataframe(metas_rep)


# BOTÃO DE LOGOUT
st.sidebar.button("Logout", on_click=lambda: [st.session_state.clear(), st.rerun()])
