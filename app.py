import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN (CSS)
st.set_page_config(page_title="Barriguinha Control", layout="centered", page_icon="🍔")

# CSS para deixar com cara de App Profissional
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #FF8C00;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #e67e00;
        color: white;
    }
    [data-testid="stMetricValue"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        color: #FF8C00;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÃO DE LOGIN
def check_password():
    """Retorna True se o usuário inseriu a senha correta."""
    def password_entered():
        if st.session_state["password"] == "BARRIGA2024": # <--- COLOQUE SUA SENHA AQUI
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # remove a senha da memória por segurança
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Tela de Login Inicial
        st.title("🔒 Acesso Restrito")
        st.text_input("Digite a senha do Barriguinha:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Senha incorreta
        st.title("🔒 Acesso Restrito")
        st.text_input("Senha incorreta. Tente novamente:", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha errada!")
        return False
    else:
        # Senha correta
        return True

# 3. SE O LOGIN FOR SUCESSO, MOSTRA O APP
if check_password():
    
    # --- INÍCIO DO SEU APP ---
    st.title("🍔 Barriguinha Control v1.2")

    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        return conn.read(worksheet="Vendas", ttl=0)

    # SIDEBAR
    st.sidebar.header("⚙️ Configuração")
    preco_carne_kg = st.sidebar.number_input("Preço KG Carne (R$)", value=34.90)
    preco_pao_un = st.sidebar.number_input("Preço Unid. Pão (R$)", value=1.47)
    outros_custos = st.sidebar.number_input("Outros Custos", value=5.30)
    
    if st.sidebar.button("Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()

    cmv_base = (preco_carne_kg * 0.12) + preco_pao_un + outros_custos

    tab1, tab2, tab3 = st.tabs(["📝 Registrar", "📊 BI & Gráficos", "📜 Histórico"])

    with tab1:
        st.subheader("Novo Pedido")
        
        hora_padrao = datetime.now() - timedelta(hours=3)
        if 'data_memoria' not in st.session_state:
            st.session_state.data_memoria = hora_padrao.date()
        if 'hora_memoria' not in st.session_state:
            st.session_state.hora_memoria = hora_padrao.time()

        col_data, col_hora = st.columns(2)
        with col_data:
            data_venda = st.date_input("Data", value=st.session_state.data_memoria, key="data_input")
            st.session_state.data_memoria = data_venda
        with col_hora:
            hora_venda = st.time_input("Hora", value=st.session_state.hora_memoria, key="hora_input")
            st.session_state.hora_memoria = hora_venda
        
        col1, col2 = st.columns(2)
        with col1:
            canal = st.selectbox("Canal", ["WhatsApp", "iFood"])
        with col2:
            produto = st.selectbox("Produto", ["Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", "Combo Barriguinha", "Combo Barrigona", "Combo Pança"])

        precos_ifood = {"Smash de Responsa": 19.90, "Artesanal de Lei": 29.90, "Supremo Barriguinha": 32.90, "Bruto de Respeito": 42.90, "Combo Tanquinho": 39.90, "Combo Pochete": 46.90, "Combo Barriguinha": 49.90, "Combo Barrigona": 59.90, "Combo Pança": 119.90}
        precos_whats = {"Smash de Responsa": 17.90, "Artesanal de Lei": 26.90, "Supremo Barriguinha": 29.90, "Bruto de Respeito": 38.90, "Combo Tanquinho": 32.90, "Combo Pochete": 39.90, "Combo Barriguinha": 44.90, "Combo Barrigona": 52.90, "Combo Pança": 99.90}

        valor_venda = precos_ifood[produto] if canal == "iFood" else precos_whats[produto]
        st.info(f"Valor: R$ {valor_venda:.2f}")

        if st.button("🚀 Registrar Venda"):
            taxa = 0.26 if canal == "iFood" else 0.0
            lucro = (valor_venda * (1 - taxa)) - cmv_base
            
            novo_pedido = pd.DataFrame([{
                "Data": data_venda.strftime("%d/%m/%Y"),
                "Hora": hora_venda.strftime("%H:%M"),
                "Produto": produto,
                "Canal": canal,
                "Valor_Bruto": valor_venda,
                "Lucro_Liquido": round(lucro, 2)
            }])
            
            df_atualizado = pd.concat([load_data(), novo_pedido], ignore_index=True)
            conn.update(worksheet="Vendas", data=df_atualizado)
            st.success("Registrado!")
            st.balloons()

    with tab2:
        st.subheader("Performance")
        data = load_data()
        if not data.empty:
            data['Hora_H'] = data['Hora'].str[:2] + "h"
            fig_hora = px.bar(data.groupby('Hora_H').size().reset_index(name='Pedidos'), x='Hora_H', y='Pedidos', color_discrete_sequence=['#FF8C00'])
            st.plotly_chart(fig_hora, use_container_width=True)
            st.metric("Lucro Líquido Total", f"R$ {data['Lucro_Liquido'].sum():.2f}")
        else:
            st.warning("Sem dados.")

    with tab3:
        st.subheader("Histórico")
        history = load_data()
        if not history.empty:
            st.dataframe(history.iloc[::-1], use_container_width=True)
