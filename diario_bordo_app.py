# diario_bordo_app.py (cole inteiro, substitui o arquivo atual)
import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- CONFIG ----------
st.set_page_config(page_title="Diário de Bordo (debug login)", layout="wide")
DEBUG = True  # se quiser remover prints de debug, coloque False

# ---------- SESSION SAFE INIT ----------
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_email" not in st.session_state:
    st.session_state.usuario_email = None
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"

# ---------- PATHS ----------
DATA_DIR = Path("dados")
USERS_PATH = DATA_DIR / "usuarios.xlsx"
VENDAS_PATH = DATA_DIR / "vendas.xlsx"
METAS_COLECAO_PATH = DATA_DIR / "metas_colecao.xlsx"
META_SEMANAL_PATH = DATA_DIR / "meta_semanal.xlsx"

# ---------- UTIL: load excel with helpful errors ----------
def try_read_excel(path: Path):
    if not path.exists():
        st.error(f"Arquivo não encontrado: {path}  ← coloque o arquivo ou ajuste o path.")
        return None
    try:
        df = pd.read_excel(path)
        return df
    except Exception as e:
        st.error(f"Erro lendo {path.name}: {e}")
        return None

# ---------- CARREGA ARQUIVOS (mas só para debug/login) ----------
usuarios_df = try_read_excel(USERS_PATH)
# other files loaded after login to avoid noise
# vendas_df = try_read_excel(VENDAS_PATH)

# If users file missing, stop now
if usuarios_df is None:
    st.stop()

# ---------- NORMALIZA COLUNAS (strip + lower) ----------
orig_cols = list(usuarios_df.columns)
usuarios_df.columns = usuarios_df.columns.str.strip()
usuarios_df_columns_norm = [c.lower().strip() for c in usuarios_df.columns]
# create mapping from normalized -> original
col_map = {c.lower().strip(): orig for c, orig in zip(usuarios_df.columns, orig_cols)}

# ---------- DETECTA COLUNAS DE EMAIL, SENHA, NOME ----------
# Possíveis variantes para email, senha, nome
email_keys = ["email", "e-mail", "usuario", "user", "login"]
senha_keys = ["senha", "password", "pass"]
nome_keys  = ["nome", "representante", "name", "fullname"]

def find_column(possible_keys, columns):
    for k in possible_keys:
        if k in columns:
            return k
    # try contains
    for c in columns:
        for k in possible_keys:
            if k in c:
                return c
    return None

norm_cols = usuarios_df_columns_norm  # already lower/stripped

email_col_norm = find_column(email_keys, norm_cols)
senha_col_norm = find_column(senha_keys, norm_cols)
nome_col_norm  = find_column(nome_keys, norm_cols)

# If any not found, show explicit error
missing = []
if email_col_norm is None:
    missing.append("email")
if senha_col_norm is None:
    missing.append("senha")
if nome_col_norm is None:
    # nome is optional (we can use email as display), but warn
    pass

if missing:
    st.error(f"Colunas obrigatórias não encontradas em {USERS_PATH.name}: {', '.join(missing)}.")
    st.write("Colunas detectadas na planilha:", usuarios_df.columns.tolist())
    st.stop()

# Map normalized col names back to actual dataframe column labels
# find the actual original column string that normalized to email_col_norm
def original_col_from_norm(norm_name):
    for c in usuarios_df.columns:
        if c.lower().strip() == norm_name:
            return c
    # fallback
    for c in usuarios_df.columns:
        if norm_name in c.lower():
            return c
    return None

email_col = original_col_from_norm(email_col_norm)
senha_col = original_col_from_norm(senha_col_norm)
nome_col  = original_col_from_norm(nome_col_norm) if nome_col_norm else None

# ---------- DEBUG: mostra o que foi detectado ----------
if DEBUG:
    st.markdown("### DEBUG — informações do arquivo de usuários")
    st.write("Caminho:", USERS_PATH)
    st.write("Colunas originais:", orig_cols)
    st.write("Colunas normalizadas:", norm_cols)
    st.write("Coluna email detectada:", email_col)
    st.write("Coluna senha detectada:", senha_col)
    st.write("Coluna nome detectada:", nome_col)
    st.markdown("---")

# ---------- FORMULÁRIO DE LOGIN ----------
st.title("🔐 Diário de Bordo — Login")

with st.form("login_form"):
    email_input = st.text_input("E-mail").strip()
    senha_input = st.text_input("Senha", type="password").strip()
    submit = st.form_submit_button("Entrar")

if submit:
    # normaliza df values for comparison
    try:
        usuarios_df[email_col] = usuarios_df[email_col].astype(str).str.strip()
    except Exception:
        usuarios_df[email_col] = usuarios_df[email_col].astype(str)

    try:
        usuarios_df[senha_col] = usuarios_df[senha_col].astype(str).str.strip()
    except Exception:
        usuarios_df[senha_col] = usuarios_df[senha_col].astype(str)

    # lowercase email for comparison
    email_comp = email_input.lower()
    usuarios_df["_email_lower_for_compare"] = usuarios_df[email_col].astype(str).str.strip().str.lower()

    # filtragem
    matched = usuarios_df[
        (usuarios_df["_email_lower_for_compare"] == email_comp) &
        (usuarios_df[senha_col] == senha_input)
    ]

    # DEBUG: mostrar o que foi comparado
    if DEBUG:
        st.write("🔎 comparando com a tabela (apenas 20 primeiras linhas):")
        st.dataframe(usuarios_df[[email_col, senha_col, "_email_lower_for_compare"]].head(20))

    if not matched.empty:
        # sucesso
        nome_display = None
        if nome_col:
            nome_display = str(matched.iloc[0][nome_col])
        else:
            nome_display = matched.iloc[0][email_col]
        st.session_state.logado = True
        st.session_state.usuario_email = matched.iloc[0][email_col]
        st.session_state.usuario_nome = nome_display
        st.success("Login OK — redirecionando...")
        st.rerun()
    else:
        st.error("❌ Usuário ou senha incorretos. Veja o debug acima para entender o que foi carregado.")

# If not logged, stop here.
if not st.session_state.logado:
    st.stop()

# ---------- PÓS LOGIN: carrega demais planilhas com normalização segura ----------
# load vendas and metas with safe read
vendas_df = try_read_excel(VENDAS_PATH)
metas_colecao_df = try_read_excel(METAS_COLECAO_PATH)
meta_semanal_df = try_read_excel(META_SEMANAL_PATH)

# if any missing, show and stop
if vendas_df is None or metas_colecao_df is None or meta_semanal_df is None:
    st.stop()

# normalize vendas columns
vendas_df.columns = vendas_df.columns.str.strip()
# support both "valor" or "valor_vendido"
if "valor_vendido" not in vendas_df.columns and "valor" in vendas_df.columns:
    vendas_df = vendas_df.rename(columns={"valor": "valor_vendido"})

# determine which column identifies the sales owner: 'representante' or 'nome'
owner_col = None
for tryc in ("representante", "nome", "vendedor"):
    if tryc in vendas_df.columns:
        owner_col = tryc
        break
if owner_col is None:
    st.error("Arquivo de vendas não tem coluna 'representante' ou 'nome' ou 'vendedor'. Colunas encontradas: " + ", ".join(vendas_df.columns.tolist()))
    st.stop()

# ---------- APP PRINCIPAL (simples) ----------
st.sidebar.title(f"👋 {st.session_state.usuario_nome}")
if st.sidebar.button("Logout"):
    # clear session keys we used
    st.session_state.logado = False
    st.session_state.usuario_email = None
    st.session_state.usuario_nome = None
    st.rerun()

st.title("📊 Dashboard (MVP)")

# Filtra vendas do usuário logado
user_name = st.session_state.usuario_nome
vendas_rep = vendas_df[vendas_df[owner_col].astype(str).str.strip() == str(user_name).strip()]

st.write(f"Total de registros de vendas carregados: **{len(vendas_df)}**")
st.write(f"Registros deste usuário ({user_name}): **{len(vendas_rep)}**")

# Mostra primeiras linhas do vendas_rep para conferir
st.subheader("Amostra das vendas filtradas (se vazio, é aqui o problema)")
st.dataframe(vendas_rep.head(50))

# Aqui continua o seu app: calcula metas, progresso etc.
# Exemplo simples:
total_vendido = 0.0
if "valor_vendido" in vendas_rep.columns:
    total_vendido = pd.to_numeric(vendas_rep["valor_vendido"], errors="coerce").fillna(0).sum()

st.metric("💰 Total vendido (sua base)", f"R$ {total_vendido:,.2f}")

st.success("Se o login funcionou e você vê suas vendas acima, está tudo certo.")
st.info("Quando quiser eu removo o DEBUG e deixo limpo.")





