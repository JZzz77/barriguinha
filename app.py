import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin v1.8", layout="wide", page_icon="📊")

# Design CSS para garantir visibilidade em qualquer modo
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
    p_cebola = st.sidebar.number_input("Cebola", value=0.20)
    p_fixo = st.sidebar.number_input("Embalagem/Molho", value=2.50)

    # Lógica de cálculo de custo por categoria de lanche
    def calcular_custo_lanche(nome_lanche):
        custo = p_pao + p_fixo
        if "Smash" in nome_lanche: 
            custo += (p_carne * 0.09) + p_queijo
        elif "Artesanal" in nome_lanche: 
            custo += (p_carne * 0.12) + p_queijo + p_salada
        elif any(x in nome_lanche for x in ["Supremo", "Bruto", "Combo"]):
            custo += (p_carne * 0.12) + p_queijo + p_bacon + p_salada + p_cebola
        if "Combo" in nome_lanche: 
            custo += 4.50 
        return custo

    # --- ABAS ---
    tab1, tab2, tab3 = st.tabs(["📝 PDV", "📈 Dashboard", "📜 Histórico"])

    with tab1:
        st.subheader("Novo Pedido")
        hora_padrao = datetime.now() - timedelta(hours=3)
        
        # Correção definitiva para manter data e hora
        if "d_v" not in st.session_state: st.session_state["d_v"] = hora_padrao.date()
        if "h_v" not in st.session_state: st.session_state["h_v"] = hora_padrao.time()

        c1, c2 = st.columns(2)
        data_sel = c1.date_input("Data", key="d_v")
        hora_sel = c2.time_input("Hora", key="h_v")
        
        canal = st.radio("Canal", ["WhatsApp", "iFood"], horizontal=True)
        produto = st.selectbox("Lanche", ["Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", "Combo Barriguinha", "Combo Barrigona", "Combo Pança"])

        precos = {
            "iFood": {"Smash de Responsa": 19.9, "Artesanal de Lei": 29.9, "Supremo Barriguinha": 32.9, "Bruto de Respeito": 42.9, "Combo Tanquinho": 39.9, "Combo Pochete": 46.9, "Combo Barriguinha": 49.9, "Combo Barrigona": 59.9, "Combo Pança": 119.9},
            "WhatsApp": {"Smash de Responsa": 17.9, "Artesanal de Lei": 26.9, "Supremo Barriguinha": 29.9, "Bruto de Respeito": 38.9, "Combo Tanquinho": 32.9, "Combo Pochete": 39.9, "Combo Barriguinha": 44.9, "Combo Barrigona": 52.9, "Combo Pança": 99.9}
        }
        
        v_venda = precos[canal][produto]
        st.metric("Valor", f"R$ {v_venda:.2f}")

        if st.button("🚀 REGISTRAR VENDA"):
            taxa = 0.26 if canal == "iFood" else 0.0
            custo_total = calcular_custo_lanche(produto)
            lucro_final = (v_venda * (1 - taxa)) - custo_total
            
            novo = pd.DataFrame([{"Data": data_sel.strftime("%d/%m/%Y"), "Hora": hora_sel.strftime("%H:%M"), "Produto": produto, "Canal": canal, "Valor_Bruto": v_venda, "Lucro_Liquido": round(lucro_final, 2)}])
            df_atual = load_data()
            df_final = pd.concat([df_atual.drop(columns=['Data_Formatada'], errors='ignore'), novo], ignore_index=True)
            conn.update(worksheet="Vendas", data=df_final)
            st.success("Venda salva!")
            st.balloons()

    with tab2:
        df = load_data()
        if not df.empty:
            hoje = datetime.now().date()
            inicio_mes = hoje.replace(day=1)
            
            c_f1, c_f2 = st.columns(2)
            d_ini = c_f1.date_input("Início", inicio_mes)
            d_fim = c_f2.date_input("Fim", hoje)
            df_f = df[(df['Data_Formatada'].dt.date >= d_ini) & (df['Data_Formatada'].dt.date <= d_fim)].sort_values('Data_Formatada')

            m1, m2, m3 = st.columns(3)
            faturamento_total = df_f['Valor_Bruto'].sum()
            lucro_op = df_f['Lucro_Liquido'].sum()
            
            m1.metric("Faturamento Período", f"R$ {faturamento_total:.2f}")
            m2.metric("Lucro Operacional", f"R$ {lucro_op:.2f}")
            m3.metric("Lucro Real (Pós Fixo)", f"R$ {(lucro_op - custos_fixos):.2f}")

            st.divider()

            # --- GRÁFICO: EVOLUÇÃO ACUMULADA VS META ---
            st.subheader("🎯 Evolução Acumulada vs Meta")
            df_f['Acumulado'] = df_f['Valor_Bruto'].cumsum()
            
            fig_meta = go.Figure()
            fig_meta.add_trace(go.Scatter(x=df_f['Data_Formatada'], y=df_f['Acumulado'], mode='lines+markers', name='Faturamento Real', line=dict(color='#FF8C00', width=4)))
            fig_meta.add_hline(y=meta_mensal, line_dash="dash", line_color="red", annotation_text=f"Meta: R$ {meta_mensal}")
            
            fig_meta.update_layout(xaxis_title="Dias", yaxis_title="R$ Acumulado", height=400)
            st.plotly_chart(fig_meta, use_container_width=True)

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                rank = df_f.groupby('Produto').size().reset_index(name='Qtd').sort_values('Qtd', ascending=True)
                st.plotly_chart(px.bar(rank, x='Qtd', y='Produto', orientation='h', title="Ranking de Saída", color_discrete_sequence=['#FF8C00']), use_container_width=True)
            with col_g2:
                st.plotly_chart(px.pie(df_f, names='Canal', title="iFood vs Whats", hole=0.4, color_discrete_sequence=['#FF8C00', '#32CD32']), use_container_width=True)

    with tab3:
        st.subheader("Gerenciar Histórico")
        df_h = load_data()
        if not df_h.empty:
            df_h['Deletar'] = False
            cols = ['Deletar', 'Data', 'Hora', 'Produto', 'Canal', 'Valor_Bruto', 'Lucro_Liquido']
            edited_df = st.data_editor(df_h[cols].iloc[::-1], hide_index=True, use_container_width=True)
            
            if st.button("🗑️ EXCLUIR SELECIONADOS"):
                indices_manter = edited_df[edited_df['Deletar'] == False].index
                df_final_del = df_h.loc[indices_manter].drop(columns=['Data_Formatada', 'Deletar'], errors='ignore')
                conn.update(worksheet="Vendas", data=df_final_del)
                st.rerun()
