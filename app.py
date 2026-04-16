import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin", layout="wide", page_icon="📊")

# Design CSS Profissional
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FF8C00; color: white; font-weight: bold; border: none; height: 3.5em; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE LOGIN
def check_password():
    def password_entered():
        if st.session_state["password"] == "BARRIGA2024":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else: st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Barriguinha Admin Login")
        st.text_input("Senha de Acesso:", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        df = conn.read(worksheet="Vendas", ttl=0)
        if not df.empty:
            df['Data_Formatada'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        return df

    # --- SIDEBAR: CONFIGURAÇÕES DE NEGÓCIO ---
    st.sidebar.header("🎯 Metas e Custos")
    meta_mensal = st.sidebar.number_input("Meta de Faturamento (R$)", value=5000)
    custos_fixos = st.sidebar.number_input("Custos Fixos Mensais (Luz/MEI/etc)", value=300)
    
    st.sidebar.divider()
    st.sidebar.header("🥩 Insumos Atuais")
    preco_carne = st.sidebar.number_input("Carne KG", value=34.90)
    preco_pao = st.sidebar.number_input("Pão Unid.", value=1.47)
    cmv_base = (preco_carne * 0.12) + preco_pao + 5.30 # 5.30 = queijo/emb/maio

    if st.sidebar.button("Sair"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- TELA PRINCIPAL ---
    st.title("🍔 Barriguinha Control v1.4")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 PDV", "📈 Dashboard", "📋 Histórico", "⚙️ Configuração"])

    # --- TAB 1: PONTO DE VENDA (PDV) ---
    with tab1:
        with st.expander("✨ Registrar Novo Pedido", expanded=True):
            col_data, col_hora = st.columns(2)
            hora_padrao = datetime.now() - timedelta(hours=3)
            data_venda = col_data.date_input("Data", hora_padrao.date())
            hora_venda = col_hora.time_input("Hora", hora_padrao.time())
            
            canal = st.radio("Canal de Venda", ["WhatsApp", "iFood"], horizontal=True)
            produto = st.selectbox("Lanche/Combo", ["Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", "Combo Barriguinha", "Combo Barrigona", "Combo Pança"])

            precos = {"iFood": {"Smash de Responsa": 19.9, "Artesanal de Lei": 29.9, "Supremo Barriguinha": 32.9, "Bruto de Respeito": 42.9, "Combo Tanquinho": 39.9, "Combo Pochete": 46.9, "Combo Barriguinha": 49.9, "Combo Barrigona": 59.9, "Combo Pança": 119.9},
                      "WhatsApp": {"Smash de Responsa": 17.9, "Artesanal de Lei": 26.9, "Supremo Barriguinha": 29.9, "Bruto de Respeito": 38.9, "Combo Tanquinho": 32.9, "Combo Pochete": 39.9, "Combo Barriguinha": 44.9, "Combo Barrigona": 52.9, "Combo Pança": 99.9}}
            
            valor_venda = precos[canal][produto]
            st.metric("Total a Cobrar", f"R$ {valor_venda:.2f}")

            if st.button("🚀 FINALIZAR PEDIDO"):
                taxa = 0.26 if canal == "iFood" else 0.0
                lucro = (valor_venda * (1 - taxa)) - cmv_base
                novo = pd.DataFrame([{"Data": data_venda.strftime("%d/%m/%Y"), "Hora": hora_venda.strftime("%H:%M"), "Produto": produto, "Canal": canal, "Valor_Bruto": valor_venda, "Lucro_Liquido": round(lucro, 2)}])
                conn.update(worksheet="Vendas", data=pd.concat([load_data().drop(columns=['Data_Formatada'], errors='ignore'), novo], ignore_index=True))
                st.success("Pedido Salvo com Sucesso!")
                st.balloons()

    # --- TAB 2: DASHBOARD ADMINISTRATIVO ---
    with tab2:
        df = load_data()
        if not df.empty:
            # Filtros de Tempo
            col_f1, col_f2 = st.columns(2)
            data_inicio = col_f1.date_input("Início", df['Data_Formatada'].min())
            data_fim = col_f2.date_input("Fim", df['Data_Formatada'].max())
            mask = (df['Data_Formatada'].dt.date >= data_inicio) & (df['Data_Formatada'].dt.date <= data_fim)
            df_filtered = df.loc[mask]

            # MÉTRICAS PRINCIPAIS
            m1, m2, m3, m4 = st.columns(4)
            faturamento = df_filtered['Valor_Bruto'].sum()
            lucro_op = df_filtered['Lucro_Liquido'].sum()
            ticket_medio = faturamento / len(df_filtered) if len(df_filtered) > 0 else 0
            
            m1.metric("Faturamento Bruto", f"R$ {faturamento:.2f}")
            m2.metric("Lucro Operacional", f"R$ {lucro_op:.2f}")
            m3.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
            m4.metric("Pedidos", len(df_filtered))

            # PROGRESSO DA META
            progresso = min(faturamento / meta_mensal, 1.0)
            st.write(f"**Progresso da Meta Mensal (R$ {meta_mensal}):**")
            st.progress(progresso)

            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                # Faturamento por Dia
                vendas_dia = df_filtered.groupby('Data_Formatada')['Valor_Bruto'].sum().reset_index()
                fig_dia = px.line(vendas_dia, x='Data_Formatada', y='Valor_Bruto', title="Evolução Diária", markers=True, color_discrete_sequence=['#FF8C00'])
                st.plotly_chart(fig_dia, use_container_width=True)

            with col_graf2:
                # Produtos mais vendidos
                prod_rank = df_filtered.groupby('Produto').size().reset_index(name='Qtd').sort_values('Qtd', ascending=True)
                fig_prod = px.bar(prod_rank, x='Qtd', y='Produto', orientation='h', title="Ranking de Produtos", color_discrete_sequence=['#FF8C00'])
                st.plotly_chart(fig_prod, use_container_width=True)

            # Cálculo de Lucro Real (Descontando Fixo Proporcional)
            lucro_real = lucro_op - custos_fixos
            st.warning(f"💰 **Lucro Real Estimado (Lucro Op. - Custos Fixos): R$ {lucro_real:.2f}**")
        else:
            st.info("Aguardando primeiros dados para gerar inteligência...")

    # --- TAB 3: HISTÓRICO ---
    with tab3:
        st.subheader("Livro de Registro")
        df_hist = load_data()
        if not df_hist.empty:
            st.dataframe(df_hist.drop(columns=['Data_Formatada']).iloc[::-1], use_container_width=True)
            if st.button("🗑️ Excluir Último Pedido (CUIDADO)"):
                df_hist = df_hist.drop(df_hist.index[-1])
                conn.update(worksheet="Vendas", data=df_hist.drop(columns=['Data_Formatada'], errors='ignore'))
                st.warning("Último pedido removido. Atualize a página.")
    
    # --- TAB 4: CONFIGURAÇÕES ---
    with tab4:
        st.write("Versão 1.4 - Desenvolvido para Barriguinha Burguer")
        st.write("Dica: Use a aba 'Dashboard' para ver o Ticket Médio. Se estiver abaixo de R$ 35,00, tente oferecer combos!")
