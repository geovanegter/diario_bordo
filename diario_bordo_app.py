import streamlit as st
import pandas as pd
from streamlit_js_eval import streamlit_js_eval
import requests

st.set_page_config(
    page_title="Diário de Bordo",
    layout="wide",
)

# ------------------------------------------------------------
# TEMA GLOBAL (CSS)
# ------------------------------------------------------------
st.markdown("""
<style>
body {
    font-family: 'Inter', sans-serif;
}
header, .css-18e3th9, .css-1d391kg { visibility: hidden; } /* remove header padrão */
.block-container {
    padding-top: 1rem;
}
button[kind="primary"] {
    border-radius: 8px;
    padding: 10px 18px;
    transition: 0.2s;
}
button[kind="primary"]:hover {
    opacity: 0.7;
}
.card {
    background: #ffffff;
    padding: 22px 26px;
    border-radius: 14px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.06);
    border: 1px solid #eaeaea;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# FUNÇÃO: pegar localização via JS + API Nominatim
# ------------------------------------------------------------
def obter_localizacao():
    coords = streamlit_js_eval(js_expressions="await new Promise(resolve => navigator.geolocation.getCurrentPosition(pos => resolve([pos.coords.latitude, pos.coords.longitude])));")
    if not coords:
        return None

    lat, lon = coords
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    try:
        r = requests.get(url, headers={"User-Agent": "diario-bordo"})
        dados = r.json()
        cidade = dados.get("address", {}).get("city") or dados.get("address", {}).get("town")
        estado = dados.get("address", {}).get("state")
        return f"{cidade} / {estado}"
    except:
        return None


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------
usuarios_df = pd.read_excel("dados/usuarios.xlsx")  # colunas: email, senha, representante

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.markdown("<h2 style='text-align:center;'>🔐 Diário de Bordo</h2>", unsafe_allow_html=True)

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuario = email.strip()
        senha = senha.strip()

        user_row = usuarios_df[
            (usuarios_df["usuario"] == usuario) &
            (usuarios_df["senha"] == senha)
        ]

        if not user_row.empty:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.session_state.nome = user_row["nome"].values[0]
            st.session_state.localizacao = None
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()


# ------------------------------------------------------------
# APÓS LOGIN — CARREGAR PLANILHAS
# ------------------------------------------------------------
vendas_df = pd.read_excel("dados/vendas.xlsx")
metas_df = pd.read_excel("dados/metas.xlsx")

usuario_nome = st.session_state.nome

# Pegar localização (executa só na primeira vez)
if st.session_state.localizacao is None:
    st.session_state.localizacao = obter_localizacao()


# ------------------------------------------------------------
# HEADER CARD A (VISUAL)
# ------------------------------------------------------------
st.markdown(f"""
<div class="card">
    <h2 style="margin-bottom:8px;">👋 Bem-vindo, {usuario_nome}!</h2>
    <p style="font-size: 16px; color: #666;">
        Você está em: <strong>{st.session_state.localizacao or "Obtendo localização..."}</strong>
    </p>
</div>
<br>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# FILTRA VENDAS DO REPRESENTANTE
# ------------------------------------------------------------
vendas_rep = vendas_df[vendas_df["representante"].str.lower() == usuario_nome.lower()]

total_vendido = vendas_rep["valor_vendido"].sum()

meta_row = metas_df[metas_df["representante"].str.lower() == usuario_nome.lower()]

meta_vendas = meta_row["meta_vendas"].sum() if "meta_vendas" in meta_row else 0
meta_clientes = meta_row["meta_clientes"].sum() if "meta_clientes" in meta_row else 0

falta_vender = max(meta_vendas - total_vendido, 0)
clientes_atendidos = vendas_rep["cliente"].nunique()
faltam_clientes = max(meta_clientes - clientes_atendidos, 0)


# ------------------------------------------------------------
# LAYOUT PRINCIPAL
# ------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Meta do mês (R$)", f"R$ {meta_vendas:,.2f}")

with col2:
    st.metric("Total vendido", f"R$ {total_vendido:,.2f}")

with col3:
    st.metric("Falta vender", f"R$ {falta_vender:,.2f}")

st.divider()

col4, col5 = st.columns(2)

with col4:
    st.metric("Clientes atendidos", clientes_atendidos)

with col5:
    st.metric("Faltam atender", faltam_clientes)


# Tabela de vendas
st.subheader("📄 Últimas vendas")
st.dataframe(vendas_rep, use_container_width=True)

