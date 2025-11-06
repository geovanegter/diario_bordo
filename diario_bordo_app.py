# ---------- BLOCO SEGURO DE AUTENTICAÇÃO ----------
import streamlit as st
import pandas as pd
from pathlib import Path

# inicializa session_state básico (evita AttributeError)
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"

DATA_DIR = Path("dados")
USERS_PATH = DATA_DIR / "usuarios.xlsx"

# Função para carregar e mostrar colunas para debug
def carregar_usuarios_debug(path):
    if not path.exists():
        st.error(f"Arquivo não encontrado: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_excel(path)
        # normaliza nomes de coluna: strip
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao ler {path.name}: {e}")
        return pd.DataFrame()

# Carrega usuarios (uma vez)
usuarios_df = carregar_usuarios_debug(USERS_PATH)

# Mostra colunas (remove comentário se quiser checar)
# st.write("Colunas em usuarios.xlsx:", usuarios_df.columns.tolist())

def autenticar(email, senha):
    """Retorna dict do usuário se encontrado, senão None."""
    if usuarios_df.empty:
        return None

    # normaliza colunas com segurança
    cols = [c.lower().strip() for c in usuarios_df.columns]
    # procura coluna email e senha nas variações comuns
    email_col = next((c for c in usuarios_df.columns if c.lower().strip() in ("email","e-mail","usuario","user","login")), None)
    senha_col = next((c for c in usuarios_df.columns if c.lower().strip() in ("senha","password","pass")), None)
    rep_col = next((c for c in usuarios_df.columns if c.lower().strip() in ("representante","rep","nome")), None)

    if email_col is None or senha_col is None:
        st.error("Colunas de autenticação não encontradas em usuarios.xlsx. Esperado: 'email' e 'senha'.")
        return None

    # compara de forma segura
    try:
        df = usuarios_df.copy()
        df[email_col] = df[email_col].astype(str).str.strip()
        df[senha_col] = df[senha_col].astype(str).str.strip()
    except Exception:
        df = usuarios_df.copy()

    filtro = (df[email_col].str.lower() == str(email).strip().lower()) & (df[senha_col] == str(senha).strip())
    matched = df[filtro]

    if len(matched) == 1:
        row = matched.iloc[0].to_dict()
        # garante campo representante
        if rep_col:
            row_rep = matched.iloc[0].get(rep_col)
            row["representante"] = row_rep if pd.notna(row_rep) else row.get(email_col)
        else:
            row["representante"] = row.get(email_col)
        # padroniza keys para o app
        return {
            "email": row.get(email_col),
            "representante": row.get("representante"),
            **{k: row.get(k) for k in usuarios_df.columns if k not in (email_col, senha_col)}
        }
    return None

# Tela de login segura (substitui blocos anteriores)
if not st.session_state.logado:
    st.markdown("<h2 style='text-align:center;'>🔐 Diário de Bordo — Login</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        email_input = st.text_input("E-mail")
        senha_input = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        user = autenticar(email_input, senha_input)
        if user:
            st.session_state.logado = True
            st.session_state.user = user
            # Define pagina padrão
            st.session_state.pagina = "Dashboard"
            st.rerun()  # NOTA: usar st.rerun(), não experimental_rerun
        else:
            st.error("E-mail ou senha inválidos. Verifique planilha usuarios.xlsx e tente novamente.")
    st.stop()
# ---------- FIM BLOCO AUTENTICAÇÃO ----------


# ======= SE CHEGOU AQUI, ESTÁ LOGADO =======
st.sidebar.title(f"👋 Olá, {st.session_state['nome']}")
if st.sidebar.button("Sair"):
    st.session_state["autenticado"] = False
    st.experimental_rerun()

st.title("📘 Diário de Bordo - Resumo Semanal")

# ======= LEITURA DE DADOS =======
try:
    dados = pd.read_excel("dados/diario_bordo.xlsx")
except FileNotFoundError:
    st.error("Arquivo 'diario_bordo.xlsx' não encontrado na pasta /dados")
    st.stop()

try:
    metas = pd.read_excel("dados/metas_colecao.xlsx")
except FileNotFoundError:
    st.error("Arquivo 'metas_colecao.xlsx' não encontrado na pasta /dados")
    st.stop()

# ======= FILTROS =======
usuario = st.session_state["usuario"]
dados_usuario = dados[dados["usuario"] == usuario]

if dados_usuario.empty:
    st.warning("Nenhum registro encontrado para este usuário.")
    st.stop()

# Selecionar semana
semanas = sorted(dados_usuario["semana"].unique(), reverse=True)
semana_selecionada = st.selectbox("Selecione a semana:", semanas)

week_row = dados_usuario[dados_usuario["semana"] == semana_selecionada]

# ======= VARIÁVEIS CORRIGIDAS =======
semana_inicio = (
    week_row["semana_inicio"].iloc[0]
    if "semana_inicio" in week_row.columns and not week_row.empty
    else "-"
)
semana_fim = (
    week_row["semana_fim"].iloc[0]
    if "semana_fim" in week_row.columns and not week_row.empty
    else "-"
)

# ======= CÁLCULOS =======
vendas_na_semana = week_row["vendas"].sum()
meta_semana = metas.loc[metas["usuario"] == usuario, "meta_semanal"].sum()
progresso = (vendas_na_semana / meta_semana * 100) if meta_semana > 0 else 0

# ======= EXIBIÇÃO =======
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div class='card' style='flex:1;'>
            <h4>💵 Vendido esta semana</h4>
            <p style='font-size:22px;margin:0;'>R$ {vendas_na_semana:,.2f}</p>
            <p class='muted'>Período: {semana_inicio} → {semana_fim}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class='card' style='flex:1;'>
            <h4>🎯 Meta semanal</h4>
            <p style='font-size:22px;margin:0;'>R$ {meta_semana:,.2f}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class='card' style='flex:1;'>
            <h4>📊 Progresso</h4>
            <p style='font-size:22px;margin:0;'>{progresso:.1f}%</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.progress(min(progresso / 100, 1.0))

st.markdown("---")
st.subheader("📈 Detalhes da Semana")
st.dataframe(week_row)

# ======= CSS =======
st.markdown(
    """
    <style>
    .card {
        background: #f9f9f9;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    .muted {
        color: #666;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


