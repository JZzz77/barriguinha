import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Configuração da página para Mobile
st.set_page_config(page_title="Barriguinha Control", layout="centered")

st.title("🍔 Barriguinha Control v1.1")

# 1. Conexão com Google Sheets (ttl=0 para não usar cache antigo)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 garante que ele busque o dado MAIS RECENTE da planilha sempre
    return conn.read(worksheet="Vendas", ttl=0)

# 2. Sidebar - Atualização de Preços de Insumos
st.sidebar.header("⚙️ Configuração de Insumos")
preco_carne_kg = st.sidebar.number_input("Preço KG Carne (R$)", value=34.90)
preco_pao_un = st.sidebar.number_input("Preço Unid. Pão (R$)", value=1.47)
outros_custos = st.sidebar.number_input("Outros (Queijo/Embalagem/etc)", value=5.30)

cmv_base = (preco_carne_kg * 0.12) + preco_pao_un + outros_custos

# 3. Interface Principal (Tabs)
tab1, tab2, tab3 = st.tabs(["📝 Registrar", "📊 BI & Gráficos", "📜 Histórico"])

with tab1:
    st.subheader("Novo Pedido")
    
    # Ajuste de Horário para Brasília (UTC-3)

    
    col1, col2 = st.columns(2)
    with col1:
        canal = st.selectbox("Canal de Venda", ["WhatsApp", "iFood"])
    with col2:
        produto = st.selectbox("Produto", [
            "Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", 
            "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", 
            "Combo Barriguinha", "Combo Barrigona", "Combo Pança"
        ])
# --- AJUSTE DE MEMÓRIA PARA DATA E HORA ---
    # Define o horário padrão de Brasília apenas se a "memória" estiver vazia
    hora_padrao = datetime.now() - timedelta(hours=3)

    if 'data_memoria' not in st.session_state:
        st.session_state.data_memoria = hora_padrao.date()
    if 'hora_memoria' not in st.session_state:
        st.session_state.hora_memoria = hora_padrao.time()

    col_data, col_hora = st.columns(2)
    with col_data:
        data_venda = st.date_input("Data da Venda", value=st.session_state.data_memoria, key="data_input")
        # Atualiza a memória quando você muda a data
        st.session_state.data_memoria = data_venda
        
    with col_hora:
        hora_venda = st.time_input("Hora da Venda", value=st.session_state.hora_memoria, key="hora_input")
        # Atualiza a memória quando você muda a hora
        st.session_state.hora_memoria = hora_venda
    # ------------------------------------------
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
        taxa = 0.26 if canal == "iFood" else 0.0
        lucro = (valor_venda * (1 - taxa)) - cmv_base
        
        # Criar o novo registro
        novo_pedido = pd.DataFrame([{
            "Data": data_venda.strftime("%d/%m/%Y"),
            "Hora": hora_venda.strftime("%H:%M"),
            "Produto": produto,
            "Canal": canal,
            "Valor_Bruto": valor_venda,
            "Lucro_Liquido": round(lucro, 2)
        }])
        
        # 1. Carregar o que já existe (FORÇANDO ATUALIZAÇÃO)
        df_antigo = load_data()
        
        # 2. Juntar o novo embaixo do antigo
        df_atualizado = pd.concat([df_antigo, novo_pedido], ignore_index=True)
        
        # 3. Salvar tudo de volta
        conn.update(worksheet="Vendas", data=df_atualizado)
        
        st.success("Pedido registrado! Puxe a página para baixo para atualizar os gráficos.")
        st.balloons()

with tab2:
    st.subheader("Análise de Performance")
    data = load_data()
    
    if not data.empty:
        # Gráfico de Horário (agrupado)
        data['Hora_H'] = data['Hora'].str[:2] + "h"
        fig_hora = px.bar(data.groupby('Hora_H').size().reset_index(name='Pedidos'), 
                          x='Hora_H', y='Pedidos', title="Pedidos por Hora", 
                          color_discrete_sequence=['#FF8C00'])
        st.plotly_chart(fig_hora, use_container_width=True)
        
        lucro_total = data["Lucro_Liquido"].sum()
        st.metric("Lucro Líquido Total", f"R$ {lucro_total:.2f}")
        
        fig_canal = px.pie(data, names="Canal", title="WhatsApp vs iFood", hole=0.3)
        st.plotly_chart(fig_canal, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para gerar gráficos.")

with tab3:
    st.subheader("Logs de Vendas")
    # Mostra os últimos pedidos primeiro
    history = load_data()
    if not history.empty:
        st.dataframe(history.iloc[::-1], use_container_width=True)
