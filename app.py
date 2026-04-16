import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# Configuração da página para Mobile
st.set_page_config(page_title="Barriguinha Control", layout="centered")

st.title("🍔 Barriguinha Control v1.0")

# 1. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para carregar dados
def load_data(worksheet):
    return conn.read(worksheet=worksheet)

# 2. Sidebar - Atualização de Preços de Insumos
st.sidebar.header("⚙️ Configuração de Insumos")
preco_carne_kg = st.sidebar.number_input("Preço KG Carne (R$)", value=34.90)
preco_pao_un = st.sidebar.number_input("Preço Unid. Pão (R$)", value=1.47)
outros_custos = st.sidebar.number_input("Outros (Queijo/Embalagem/etc)", value=5.30)

# Cálculo do CMV base (120g de carne)
cmv_base = (preco_carne_kg * 0.12) + preco_pao_un + outros_custos

# 3. Interface Principal (Tabs)
tab1, tab2, tab3 = st.tabs(["📝 Registrar", "📊 BI & Gráficos", "📜 Histórico"])

with tab1:
    st.subheader("Novo Pedido")
    
    col1, col2 = st.columns(2)
    with col1:
        canal = st.selectbox("Canal de Venda", ["WhatsApp", "iFood"])
    with col2:
        produto = st.selectbox("Produto", [
            "Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", 
            "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", 
            "Combo Barriguinha", "Combo Barrigona", "Combo Pança"
        ])

    # Dicionário de Preços (Baseado no que definimos antes)
    precos_ifood = {
        "Smash de Responsa": 19.90, "Artesanal de Lei": 29.90, "Supremo Barriguinha": 32.90,
        "Bruto de Respeito": 42.90, "Combo Tanquinho": 39.90, "Combo Pochete": 46.90,
        "Combo Barriguinha": 49.90, "Combo Barrigona": 59.90, "Combo Pança": 119.90
    }
    
    precos_whats = {
        "Smash de Responsa": 17.90, "Artesanal de Lei": 26.90, "Supremo Barriguinha": 29.90,
        "Bruto de Respeito": 38.90, "Combo Tanquinho": 32.90, "Combo Pochete": 39.90,
        "Combo Barriguinha": 44.90, "Combo Barrigona": 52.90, "Combo Pança": 99.90
    }

    valor_venda = precos_ifood[produto] if canal == "iFood" else precos_whats[produto]
    st.info(f"Valor da Venda: R$ {valor_venda:.2f}")

    if st.button("🚀 Finalizar e Registrar"):
        # Lógica de Taxas e Lucro
        taxa = 0.26 if canal == "iFood" else 0.0
        lucro = (valor_venda * (1 - taxa)) - cmv_base
        
        novo_pedido = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y"),
            "Hora": datetime.now().strftime("%H:%M"),
            "Produto": produto,
            "Canal": canal,
            "Valor_Bruto": valor_venda,
            "Lucro_Liquido": round(lucro, 2)
        }])
        
        # Enviar para o Google Sheets
        existing_data = load_data("Vendas")
        updated_df = pd.concat([existing_data, novo_pedido], ignore_index=True)
        conn.update(worksheet="Vendas", data=updated_df)
        st.success("Pedido registrado com sucesso!")

with tab2:
    st.subheader("Análise de Performance")
    data = load_data("Vendas")
    
    if not data.empty:
        # Gráfico de Vendas por Hora
        fig_hora = px.histogram(data, x="Hora", title="Volume de Pedidos por Horário", color_discrete_sequence=['#FF8C00'])
        st.plotly_chart(fig_hora, use_container_width=True)
        
        # Lucro Total Acumulado
        lucro_total = data["Lucro_Liquido"].sum()
        st.metric("Lucro Líquido Total", f"R$ {lucro_total:.2f}")
        
        # Vendas por Canal
        fig_canal = px.pie(data, names="Canal", title="WhatsApp vs iFood", hole=0.3)
        st.plotly_chart(fig_canal, use_container_width=True)

with tab3:
    st.subheader("Logs de Vendas")
    st.dataframe(load_data("Vendas").sort_index(ascending=False))