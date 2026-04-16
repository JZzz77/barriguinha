import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin v1.6", layout="wide", page_icon="📊")

# Design CSS Adaptável (Modo Claro/Escuro)
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
                # Criar uma coluna de ID baseada no index para facilitar exclusão
                df['ID'] = df.index
            return df
        except:
            return pd.DataFrame()

    # --- ESTADO DE DATA/HORA ---
    hora_padrao = datetime.now() - timedelta(hours=3)
    if "data_venda_v16" not in st.session_state:
        st.session_state["data_venda_v16"] = hora_padrao.date()
    if "hora_venda_v16" not in st.session_state:
        st.session_state["hora_venda_v16"] = hora_padrao.time()

    # --- SIDEBAR ---
    st.sidebar.header("🎯 Parâmetros")
    custos_fixos = st.sidebar.number_input("Custos Fixos Mensais", value=300)
    preco_carne = st.sidebar.number_input("Carne KG", value=34.90)
    preco_pao = st.sidebar.number_input("Pão (unid)", value=1.47)
    cmv_base = (preco_carne * 0.12) + preco_pao + 5.30

    tab1, tab2, tab3 = st.tabs(["📝 PDV", "📈 Dashboard BI", "📜 Histórico & Gestão"])

    # --- TAB 1: PDV ---
    with tab1:
        with st.expander("✨ Novo Pedido", expanded=True):
            c1, c2 = st.columns(2)
            data_sel = c1.date_input("Data", key="data_venda_v16")
            hora_sel = c2.time_input("Hora", key="hora_venda_v16")
            
            canal = st.radio("Canal", ["WhatsApp", "iFood"], horizontal=True)
            produto = st.selectbox("Lanche", ["Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", "Combo Barriguinha", "Combo Barrigona", "Combo Pança"])

            precos = {
                "iFood": {"Smash de Responsa": 19.9, "Artesanal de Lei": 29.9, "Supremo Barriguinha": 32.9, "Bruto de Respeito": 42.9, "Combo Tanquinho": 39.9, "Combo Pochete": 46.9, "Combo Barriguinha": 49.9, "Combo Barrigona": 59.9, "Combo Pança": 119.9},
                "WhatsApp": {"Smash de Responsa": 17.9, "Artesanal de Lei": 26.9, "Supremo Barriguinha": 29.9, "Bruto de Respeito": 38.9, "Combo Tanquinho": 32.9, "Combo Pochete": 39.9, "Combo Barriguinha": 44.9, "Combo Barrigona": 52.9, "Combo Pança": 99.9}
            }
            
            valor_v = precos[canal][produto]
            st.metric("Valor do Pedido", f"R$ {valor_v:.2f}")

            if st.button("🚀 SALVAR PEDIDO"):
                taxa = 0.26 if canal == "iFood" else 0.0
                lucro_un = (valor_v * (1 - taxa)) - cmv_base
                novo = pd.DataFrame([{"Data": data_sel.strftime("%d/%m/%Y"), "Hora": hora_sel.strftime("%H:%M"), "Produto": produto, "Canal": canal, "Valor_Bruto": valor_v, "Lucro_Liquido": round(lucro_un, 2)}])
                
                df_atual = load_data()
                if not df_atual.empty:
                    df_final = pd.concat([df_atual.drop(columns=['Data_Formatada', 'ID'], errors='ignore'), novo], ignore_index=True)
                else:
                    df_final = novo
                
                conn.update(worksheet="Vendas", data=df_final)
                st.success("Venda salva!")
                st.balloons()

    # --- TAB 2: DASHBOARD BI ---
    with tab2:
        df = load_data()
        if not df.empty:
            c_f1, c_f2 = st.columns(2)
            hoje = datetime.now() - timedelta(hours=3)
            d_ini = c_f1.date_input("Início", hoje.date() - timedelta(days=7))
            d_fim = c_f2.date_input("Fim", hoje.date())
            
            df_f = df[(df['Data_Formatada'].dt.date >= d_ini) & (df['Data_Formatada'].dt.date <= d_fim)]

            m1, m2, m3 = st.columns(3)
            fat = df_f['Valor_Bruto'].sum()
            lucro = df_f['Lucro_Liquido'].sum()
            m1.metric("Faturamento", f"R$ {fat:.2f}")
            m2.metric("Lucro Op.", f"R$ {lucro:.2f}")
            
            pago = lucro - custos_fixos
            m3.metric("Sobrou no Bolso", f"R$ {pago:.2f}", delta="Pós Custos Fixos")

            st.divider()
            
            # Gráficos de Vendas
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                v_dia = df_f.groupby('Data_Formatada')['Valor_Bruto'].sum().reset_index()
                st.plotly_chart(px.line(v_dia, x='Data_Formatada', y='Valor_Bruto', title="Evolução Diária (Macro)", markers=True, color_discrete_sequence=['#FF8C00']), use_container_width=True)
            
            with col_g2:
                # Ranking de lanches RESPEITANDO O FILTRO
                rank = df_f.groupby('Produto').size().reset_index(name='Qtd').sort_values('Qtd', ascending=True)
                st.plotly_chart(px.bar(rank, x='Qtd', y='Produto', orientation='h', title="Mais Vendidos no Período", color_discrete_sequence=['#FF8C00']), use_container_width=True)

            col_g3, col_g4 = st.columns(2)
            with col_g3:
                # Pedidos por Hora (Micro)
                df_f['Hora_H'] = df_f['Hora'].str[:2] + "h"
                h_rank = df_f.groupby('Hora_H').size().reset_index(name='Qts')
                st.plotly_chart(px.bar(h_rank, x='Hora_H', y='Qts', title="Picos de Horário", color_discrete_sequence=['#FFA500']), use_container_width=True)
            
            with col_g4:
                # VOLTA DO GRÁFICO DE PIZZA
                fig_pizza = px.pie(df_f, names='Canal', title="WhatsApp vs iFood", hole=0.4, color_discrete_sequence=['#FF8C00', '#32CD32'])
                st.plotly_chart(fig_pizza, use_container_width=True)

    # --- TAB 3: HISTÓRICO & GESTÃO (Exclusão Inteligente) ---
    with tab3:
        st.subheader("Gerenciar Histórico")
        df_edit = load_data()
        
        if not df_edit.empty:
            st.write("Selecione os pedidos que deseja remover e clique no botão abaixo:")
            
            # Criar editor de dados com checkbox de seleção
            df_edit['Excluir'] = False
            # Reorganizar colunas para ficar visualmente fácil
            cols = ['Excluir', 'Data', 'Hora', 'Produto', 'Canal', 'Valor_Bruto', 'Lucro_Liquido']
            edited_df = st.data_editor(df_edit[cols].iloc[::-1], hide_index=True, use_container_width=True)
            
            c_del1, c_del2 = st.columns(2)
            
            if c_del1.button("🗑️ APAGAR SELECIONADOS"):
                # Filtra as linhas que NÃO foram marcadas para excluir
                indices_para_manter = edited_df[edited_df['Excluir'] == False].index
                # Como o editor inverteu a ordem com iloc[::-1], precisamos mapear de volta ou usar a lógica original
                df_final_delete = df_edit.loc[indices_para_manter].drop(columns=['Data_Formatada', 'ID', 'Excluir'], errors='ignore')
                conn.update(worksheet="Vendas", data=df_final_delete)
                st.success("Pedidos removidos!")
                st.rerun()

            if c_del2.button("🔙 APAGAR ÚLTIMO (RÁPIDO)"):
                df_rapido = df_edit.drop(df_edit.index[-1]).drop(columns=['Data_Formatada', 'ID', 'Excluir'], errors='ignore')
                conn.update(worksheet="Vendas", data=df_rapido)
                st.rerun()
