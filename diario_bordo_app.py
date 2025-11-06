import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

# ────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES INICIAIS
# ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="📒 Diário de Bordo", layout="wide")

# Inicializa session_state
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if "nome" not in st.session_state:
    st.session_state["nome"] = ""

if "email" not in st.session_state:
    st.session_state["email"] = ""

# ────────────────────────────────────────────────────────────────
# FUNÇÃO DE CARREGAMENTO DE PLANILHAS
# ────────────────────────────────────────────────────────────────
def carregar_planilha(nome_arquivo):
    caminho = os.path.join("dados", nome_arquivo)
    if not os.path.exists(caminho):
        st.error(f"❌ Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    return pd.read_excel(caminho)

# Carregar dados
df_usuarios = carregar_planilha("usuarios.xlsx")
df_diario = carregar_planilha("vendas.xlsx")
df_metas = carregar_planilha("metas_colecao.xlsx")

# ────────────────────────────────────────────────────────────────
# LOGIN
# ────────────────────────────────────────────────────────────────

def tela_login():
    st.title("🔐 Acesso ao Diário de Bordo")

    email = st.text_input("E-mail:")
    senha = st.text_input("Senha:", type="password")

    if st.button("Entrar", use_container_width=True):
        usuario = df_usuarios[
            (df_usuarios["email"] == email) &
            (df_usuarios["senha"] == senha)
        ]

        if not usuario.empty:
            st.session_state["autenticado"] = True
            st.session_state["nome"] = usuario.iloc[0]["nome"]
            st.session_state["email"] = email

            st.success("✅ Login realizado com sucesso!")
            st.experimental_rerun()
        else:
            st.error("❌ Usuário ou senha inválidos.")

# Se o usuário não estiver autenticado, mostra a tela de login
if not st.session_state["autenticado"]:
    tela_login()
    st.stop()

# ────────────────────────────────────────────────────────────────
# SIDEBAR
# ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title(f"👋 Olá, {st.session_state.get('nome', 'Usuário')}")
    if st.button("Logout"):
        st.session_state["autenticado"] = False
        st.experimental_rerun()

# ────────────────────────────────────────────────────────────────
# DASHBOARD PRINCIPAL
# ────────────────────────────────────────────────────────────────
st.title("📊 Painel do Representante")

# Filtro pelo usuário logado
df_usuario = df_diario[df_diario["email"] == st.session_state["email"]]

# Resumo da semana
hoje = datetime.now(pytz.timezone("America/Sao_Paulo"))
semana_atual = hoje.isocalendar().week

df_semana = df_usuario[df_usuario["semana"] == semana_atual]

vendas_na_semana = df_semana["vendas"].sum() if not df_semana.empty else 0

week_row = df_semana.iloc[0] if not df_semana.empty else None

semana_inicio = week_row.get("semana_inicio", "-") if week_row is not None else "-"
semana_fim = week_row.get("semana_fim", "-") if week_row is not None else "-"

# Cards KPI
st.markdown(
    f"""
<div style="display:flex;gap:20px;">
    <div class='card' style='flex:1;'>
        <h4>💵 Vendido na semana</h4>
        <p style='font-size:22px;margin:0;'>R$ {vendas_na_semana:,.2f}</p>
        <p class='muted'>Período: {semana_inicio} → {semana_fim}</p>
    </div>

    <div class='card' style='flex:1;'>
        <h4>📋 Registros</h4>
        <p style='font-size:22px;margin:0;'>{len(df_usuario)}</p>
    </div>
</div>
""",
    unsafe_allow_html=True
)


# ────────────────────────────────────────────────────────────────
# FORMULÁRIO DO DIÁRIO DE BORDO
# ────────────────────────────────────────────────────────────────

st.subheader("✏️ Novo registro")

with st.form("novo_diario"):
    data = st.date_input("Data da visita")
    cliente = st.text_input("Cliente")
    venda = st.number_input("Valor da venda (R$)", format="%.2f")
    observacao = st.text_area("Observação")

    salvar = st.form_submit_button("Salvar")

if salvar:
    nova_linha = pd.DataFrame([{
        "email": st.session_state["email"],
        "nome": st.session_state["nome"],
        "data": data,
        "cliente": cliente,
        "vendas": venda,
        "observacao": observacao,
        "semana": data.isocalendar()[1]
    }])

    df_diario = pd.concat([df_diario, nova_linha], ignore_index=True)
    df_diario.to_excel(os.path.join("dados", "diario_bordo.xlsx"), index=False)

    st.success("✅ Registro salvo com sucesso!")
    st.experimental_rerun()

# ────────────────────────────────────────────────────────────────
# LISTAGEM DE REGISTROS DA SEMANA
# ────────────────────────────────────────────────────────────────

st.subheader("🗂️ Registros da semana")

st.dataframe(df_semana)



