import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Control", layout="centered", page_icon="🍔")

# Design CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #FF8C00; color: white; font-weight: bold; }
    [data-testid="stMetricValue"] { background-color: #f0f2f6; padding: 15px; border-radius: 10px; color: #FF8C00; }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE LOGIN
def check_password():
    def password_entered():
        if st.session_state["password"] == "BARRIGA2024":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Acesso Restrito")
        st.text_input("Senha:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha incorreta. Tente novamente:", type="password", on_change=password_entered, key="password")
        return False
    return True

if check_password():
    st.title("🍔 Barriguinha Control v1.3")
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        df = conn.read(worksheet="Vendas", ttl=0)
        if not df.empty:
            # Converte a coluna Data para o formato datetime do Python para o gráfico entender a ordem
            df['Data_Formatada'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        return df

    # SIDEBAR
    st.sidebar.header("⚙️ Configuração")
    preco_carne = st.sidebar.number_input("Carne KG", value=34.90)
    preco_pao = st.sidebar.number_input("Pão Unid.", value=1.47)
    cmv_base = (preco_carne * 0.12) + preco_pao + 5.30

    tab1, tab2, tab3 = st.tabs(["📝 Registrar", "📊 BI & Gráficos", "📜 Histórico"])

    with tab1:
        st.subheader("Novo Pedido")
        hora_padrao = datetime.now() - timedelta(hours=3)
        
        c1, c2 = st.columns(2)
        with c1: data_venda = st.date_input("Data", hora_padrao.date())
        with c2: hora_venda = st.time_input("Hora", hora_padrao.time())
        
        canal = st.selectbox("Canal", ["WhatsApp", "iFood"])
        produto = st.selectbox("Produto", ["Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", "Combo Barriguinha", "Combo Barrigona", "Combo Pança"])

        precos = {"iFood": {"Smash de Responsa": 19.9, "Artesanal de Lei": 29.9, "Supremo Barriguinha": 32.9, "Bruto de Respeito": 42.9, "Combo Tanquinho": 39.9, "Combo Pochete": 46.9, "Combo Barriguinha": 49.9, "Combo Barrigona": 59.9, "Combo Pança": 119.9},
                  "WhatsApp": {"Smash de Responsa": 17.9, "Artesanal de Lei": 26.9, "Supremo Barriguinha": 29.9, "Bruto de Respeito": 38.9, "Combo Tanquinho": 32.9, "Combo Pochete": 39.9, "Combo Barriguinha": 44.9, "Combo Barrigona": 52.9, "Combo Pança": 99.9}}

        valor_venda = precos[canal][produto]
        st.info(f"Valor: R$ {valor_venda:.2f}")

        if st.button("🚀 Registrar"):
            taxa = 0.26 if canal == "iFood" else 0.0
            lucro = (valor_venda * (1 - taxa)) - cmv_base
            novo = pd.DataFrame([{"Data": data_venda.strftime("%d/%m/%Y"), "Hora": hora_venda.strftime("%H:%M"), "Produto": produto, "Canal": canal, "Valor_Bruto": valor_venda, "Lucro_Liquido": round(lucro, 2)}])
            conn.update(worksheet="Vendas", data=pd.concat([load_data().drop(columns=['Data_Formatada'], errors='ignore'), novo], ignore_index=True))
            st.success("Registrado!")

    with tab2:
        st.subheader("Performance")
        data = load_data()
        if not data.empty:
            # GRÁFICO POR DIA (Novo)
            vendas_dia = data.groupby('Data_Formatada')['Valor_Bruto'].sum().reset_index()
            fig_dia = px.line(vendas_dia, x='Data_Formatada', y='Valor_Bruto', title="Faturamento Diário (R$)", markers=True)
            fig_dia.update_traces(line_color='#FF8C00')
            st.plotly_chart(fig_dia, use_container_width=True)

            # GRÁFICO POR HORA
            data['Hora_H'] = data['Hora'].str[:2] + "h"
            fig_hora = px.bar(data.groupby('Hora_H').size().reset_index(name='Pedidos'), x='Hora_H', y='Pedidos', title="Pedidos por Horário", color_discrete_sequence=['#FF8C00'])
            st.plotly_chart(fig_hora, use_container_width=True)
            
            st.metric("Lucro Líquido Total", f"R$ {data['Lucro_Liquido'].sum():.2f}")
        else:
            st.warning("Sem dados.")

    with tab3:
        st.subheader("Histórico")
        history = load_data()
        if not history.empty:
            st.dataframe(history.drop(columns=['Data_Formatada']).iloc[::-1], use_container_width=True)
