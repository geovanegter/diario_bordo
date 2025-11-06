import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

# ------------------------------------------------------------
# CONFIGURAÇÃO INICIAL DO APP
# ------------------------------------------------------------
st.set_page_config(page_title="Diário de Bordo", layout="wide")

# CSS para estilo visual
st.markdown("""
    <style>
    .css-18e3th9 { padding-top: 0 !important; }
    .block-container { padding-top: 1rem; }

    .nav-button {
        width: 100%;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #DDD;
        background: #f7f7f7;
        color: #333;
        font-size: 16px;
        cursor: pointer;
        margin-bottom: 8px;
        transition: 0.2s;
    }
    .nav-button:hover {
        background: #e8e8e8;
    }
    .card {
        background: white;
        padding: 22px;
        border-radius: 12px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.08);
        text-align: center;
    }
    .muted {
        font-size: 13px;
        color: #888;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------------------------------------

def carregar_planilhas():
    usuarios = pd.read_excel("dados/usuarios.xlsx")
    vendas = pd.read_excel("dados/vendas.xlsx")
    metas_colecao = pd.read_excel("dados/metas_colecao.xlsx")
    metas_semana = pd.read_excel("dados/metas_semana.xlsx")
    return usuarios, vendas, metas_colecao, metas_semana


def autenticar(email, senha, usuarios):
    usuario = usuarios[(usuarios["email"] == email) & (usuarios["senha"] == senha)]

    if not usuario.empty:
        return True, usuario.iloc[0]["representante"]
    return False, None


def obter_localizacao():
    loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition((pos)=>pos.coords)")
    return loc


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.pagina = "dashboard"

if not st.session_state.autenticado:

    st.title("🔐 Acesso ao Diário de Bordo")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuarios, _, _, _ = carregar_planilhas()
        sucesso, representante = autenticar(email, senha, usuarios)

        if sucesso:
            st.session_state.autenticado = True
            st.session_state.representante = representante
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")

    st.stop()


# ------------------------------------------------------------
# ÁREA APÓS LOGIN
# ------------------------------------------------------------

usuarios, vendas, metas_colecao, metas_semana = carregar_planilhas()

rep = st.session_state.representante

st.sidebar.title(f"👋 Bem-vindo, {rep}")
st.sidebar.write("---")

# MENU
paginas = ["Dashboard", "Clientes", "Ranking", "Dossiê do Cliente"]

for p in paginas:
    if st.sidebar.button(p, key=p, use_container_width=True):
        st.session_state.pagina = p

st.write(f"📍 Localização atual (se permitido pelo navegador):")
loc = obter_localizacao()
if loc:
    st.write(f"Lat: **{loc.get('latitude')}**, Long: **{loc.get('longitude')}**")
else:
    st.write("🔒 Localização não autorizada")


# FILTRO para o representante logado
vendas_rep = vendas[vendas["representante"] == rep]

colecao_atual = metas_colecao["colecao"].unique()[0]  # sempre 1 coleção ativa

meta_row = metas_colecao[metas_colecao["representante"] == rep]
meta_vendas = meta_row["meta_vendas"].iloc[0]
meta_clientes = meta_row["meta_clientes"].iloc[0]

total_vendido = vendas_rep["valor_vendido"].sum()
clientes_atendidos = vendas_rep["cliente"].nunique()

pct_meta = total_vendido / meta_vendas if meta_vendas > 0 else 0


# ------------------------------------------------------------
# PÁGINA: DASHBOARD
# ------------------------------------------------------------
if st.session_state.pagina == "Dashboard":

    st.subheader(f"📊 Progresso da Coleção: **{colecao_atual}**")

    st.progress(pct_meta)

    st.write(f"Você atingiu **{pct_meta:.0%}** da meta da coleção.")

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"<div class='card'><h3>💰 Total Vendido</h3><p>R$ {total_vendido:,.2f}</p></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><h3>🧑‍🤝‍🧑 Clientes</h3><p>{clientes_atendidos}</p></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='card'><h3>🎯 Meta</h3><p>R$ {meta_vendas:,.2f}</p></div>", unsafe_allow_html=True)

    # 🎯 Semana atual (leva meta semanal)
    semana = metas_semana.iloc[0]
    semana_inicio = semana["semana_inicio"].strftime("%d/%m")
    semana_fim = semana["semana_fim"].strftime("%d/%m")
    meta_semana = meta_vendas * semana["percentual_meta"]

    vendas_semana = vendas_rep[vendas_rep["prazo"] >= semana["semana_inicio"]]["valor_vendido"].sum()

    colA, colB = st.columns(2)
    colA.markdown(f"<div class='card'><h3>💵 Vendido na semana</h3><p>R$ {vendas_semana:,.2f}</p><p class='muted'>{semana_inicio} → {semana_fim}</p></div>", unsafe_allow_html=True)
    colB.markdown(f"<div class='card'><h3>📅 Meta semanal</h3><p>R$ {meta_semana:,.2f}</p></div>", unsafe_allow_html=True)


# ------------------------------------------------------------
# PÁGINA: CLIENTES
# ------------------------------------------------------------
elif st.session_state.pagina == "Clientes":
    st.subheader("🧑‍🤝‍🧑 Clientes atendidos")
    st.dataframe(vendas_rep[["cliente", "cidade", "colecao"]].drop_duplicates())


# ------------------------------------------------------------
# PÁGINA: RANKING
# ------------------------------------------------------------
elif st.session_state.pagina == "Ranking":
    st.subheader("🏆 Ranking de vendas por cliente")
    ranking = vendas_rep.groupby("cliente")["valor_vendido"].sum().sort_values(ascending=False)
    st.dataframe(ranking)


# ------------------------------------------------------------
# PÁGINA: DOSSIÊ DO CLIENTE
# ------------------------------------------------------------
elif st.session_state.pagina == "Dossiê do Cliente":
    st.subheader("📄 Dossiê do Cliente")
    cliente = st.selectbox("Selecione um cliente", vendas_rep["cliente"].unique())

    if cliente:
        historico = vendas_rep[vendas_rep["cliente"] == cliente]
        st.dataframe(historico)





