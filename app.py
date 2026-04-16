import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin v1.5", layout="wide", page_icon="📊")

# Design CSS Reforçado para Mobile
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FF8C00; color: white; font-weight: bold; height: 3.5em; border: none; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #FF8C00; }
    div[data-testid="stExpander"] { border: none; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE LOGIN
def check_password():
    def password_entered():
        if st.session_state["password_input"] == "BARRIGA2024":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.title("🔐 Acesso Administrativo")
        st.text_input("Senha:", type="password", on_change=password_entered, key="password_input")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("Senha Incorreta")
        return False
    return True

if check_password():
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        df = conn.read(worksheet="Vendas", ttl=0)
        if not df.empty:
            df['Data_Formatada'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        return df

    # --- INICIALIZAÇÃO DE ESTADO PARA DATA/HORA (Correção de Bug) ---
    hora_padrao = datetime.now() - timedelta(hours=3)
    if "data_venda_v15" not in st.session_state:
        st.session_state["data_venda_v15"] = hora_padrao.date()
    if "hora_venda_v15" not in st.session_state:
        st.session_state["hora_venda_v15"] = hora_padrao.time()

    # --- SIDEBAR ---
    st.sidebar.header("🎯 Parâmetros do Mês")
    meta_faturamento = st.sidebar.number_input("Meta Mensal (R$)", value=5000)
    custos_fixos = st.sidebar.number_input("Custos Fixos (Luz/Internet/MEI)", value=300)
    
    st.sidebar.divider()
    preco_carne = st.sidebar.number_input("Preço Carne KG", value=34.90)
    preco_pao = st.sidebar.number_input("Preço Pão (4 unid)", value=5.90) / 4
    cmv_base = (preco_carne * 0.12) + preco_pao + 5.30

    # --- ABAS ---
    tab1, tab2, tab3 = st.tabs(["📝 PDV (Vendas)", "📈 Gestão e BI", "📜 Histórico"])

    # --- TAB 1: PDV (Com Correção de Hora) ---
    with tab1:
        with st.expander("✨ Registrar Novo Pedido", expanded=True):
            c1, c2 = st.columns(2)
            # Usando as chaves de estado para manter o valor mesmo após refresh
            data_sel = c1.date_input("Data da Venda", key="data_venda_v15")
            hora_sel = c2.time_input("Hora da Venda", key="hora_venda_v15")
            
            canal = st.radio("Origem", ["WhatsApp", "iFood
