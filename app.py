import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin v1.8", layout="wide", page_icon="📊")

# Design CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FF8C00; color: white !important; font-weight: bold; height: 3.5em; border: none; }
    [data-testid="stMetricValue"] { color: #FF8C00 !important; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #FF8C00; }
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
        return False
    return True

if check_password():
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        try:
            df = conn.read(worksheet="Vendas", ttl=0)
            if not df.empty:
                df['Data_Formatada'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
            return df
        except:
            return pd.DataFrame()

    # --- SIDEBAR: PARÂMETROS E INSUMOS ---
    st.sidebar.header("🎯 Metas e Custos Fixos")
    meta_mensal = st.sidebar.number_input("Meta de Faturamento (R$)", value=5000)
    custos_fixos = st.sidebar.number_input("Custos Fixos (Luz/MEI/etc)", value=300)
    
    st.sidebar.divider()
    st.sidebar.header("🛒 Preço dos Insumos")
    p_carne = st.sidebar.number_input("Carne KG", value=34.90)
    p_pao = st.sidebar.number_input("Pão Unit.", value=1.47)
    p_queijo = st.sidebar.number_input("Queijo (2 fat.)", value=2.10)
    p_bacon = st.sidebar.number_input("Bacon (30g)", value=1.35)
    p_salada = st.sidebar.number_input("Alface/Tomate", value=0.80)
    p_cebola = st.sidebar.number_input("
