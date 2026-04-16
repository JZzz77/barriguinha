import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Control v1.7", layout="wide", page_icon="🍔")

# Estilização para garantir visibilidade no modo claro e escuro
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

    # --- SIDEBAR: CUSTOS DETALHADOS ---
    st.sidebar.header("🛒 Preço dos Insumos")
    
    # Valores de referência baseados em mercado/histórico
    p_carne = st.sidebar.number_input("Carne KG (Ref: R$ 34.90)", value=34.90)
    p_pao = st.sidebar.number_input("Pão Unit. (Ref: R$ 1.47)", value=1.47)
    p_queijo = st.sidebar.number_input("Queijo (2 fatias - Ref: R$ 2.10)", value=2.10)
    p_bacon = st.sidebar.number_input("Bacon (30g - Ref: R$ 1.35)", value=1.35)
    p_salada = st.sidebar.number_input("Alface/Tomate (Ref: R$ 0.80)", value=0.80)
    p_cebola = st.sidebar.number_input("Cebola (Ref: R$ 0.20)", value=0.20)
    p_fixo = st.sidebar.number_input("Embalagem/Molho (Ref: R$ 2.50)", value=2.50)

    # --- LÓGICA DE CMV POR LANCHE ---
    # Função que calcula o custo exato baseado no que vai no lanche
    def calcular_custo_lanche(nome_lanche):
        custo = p_pao + p_fixo
        
        if "Smash" in nome_lanche:
            custo += (p_carne * 0.09) + p_queijo # 90g carne
        elif "Artesanal" in nome_lanche:
            custo += (p_carne * 0.12) + p_queijo + p_salada # 120g carne + salada
        elif "Supremo" in nome_lanche or "Bruto" in nome_lanche or "Combo" in nome_lanche:
            custo += (p_carne * 0.12) + p_queijo + p_bacon + p_salada + p_cebola # Completo
        
        # Adiciona batata/bebida simbólico para combos
        if "Combo" in nome_lanche:
            custo += 4.50 
        return custo

    # --- ABAS ---
    tab1, tab2, tab3 = st.tabs(["📝 PDV", "📈 Dashboard", "📜 Histórico"])

    with tab1:
        st.subheader("Novo Pedido")
        # Mantendo o estado estável da hora
        hora_padrao = datetime.now() - timedelta(hours=3)
        if "d_v" not in st.session_state: st.session_state["d_v"] = hora_padrao.date()
        if "h_v" not in st.session_state: st.session_state["h_v"] = hora_padrao.time()

        c1, c2 = st.columns(2)
        data_sel = c1.date_input("Data", key="d_v")
        hora_sel = c2.time_input("Hora", key="h_v")
        
        canal = st.radio("Canal", ["WhatsApp", "iFood"], horizontal=True)
        lista_lanches = ["Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", "Combo Barriguinha", "Combo Barrigona", "Combo Pança"]
        produto = st.selectbox("Lanche", lista_lanches)

        precos = {
            "iFood": {"Smash de Responsa": 19.9, "Artesanal de Lei": 29.9, "Supremo Barriguinha": 32.9, "Bruto de Respeito": 42.9, "Combo Tanquinho": 39.9, "Combo Pochete": 46.9, "Combo Barriguinha": 49.9, "Combo Barrigona": 59.9, "Combo Pança": 119.9},
            "WhatsApp": {"Smash de Responsa": 17.9, "Artesanal de Lei": 26.9, "Supremo Barriguinha": 29.9, "Bruto de Respeito": 38.9, "Combo Tanquinho": 32.9, "Combo Pochete": 39.9, "Combo Barriguinha": 44.9, "Combo Barrigona": 52.9, "Combo Pança": 99.9}
        }
        
        v_venda = precos[canal][produto]
        st.metric("Valor", f"R$ {v_venda:.2f}")

        if st.button("🚀 REGISTRAR"):
            taxa = 0.26 if canal == "iFood" else 0.0
            custo_total = calcular_custo_lanche(produto)
            lucro = (v_venda * (1 - taxa)) - custo_total
            
            novo = pd.DataFrame([{"Data": data_sel.strftime("%d/%m/%Y"), "Hora": hora_sel.strftime("%H:%M"), "Produto": produto, "Canal": canal, "Valor_Bruto": v_venda, "Lucro_Liquido": round(lucro, 2)}])
            df_atual = load_data()
            df_final = pd.concat([df_atual.drop(columns=['Data_Formatada'], errors='ignore'), novo], ignore_index=True)
            conn.update(worksheet="Vendas", data=df_final)
            st.success("Venda salva!")
            st.balloons()

    with tab2:
        df = load_data()
        if not df.empty:
            c_f1, c_f2 = st.columns(2)
            d_ini = c_f1.date_input("Início", df['Data_Formatada'].min().date())
            d_fim = c_f2.date_input("Fim", datetime.now().date())
            df_f = df[(df['Data_Formatada'].dt.date >= d_ini) & (df['Data_Formatada'].dt.date <= d_fim)]

            m1, m2, m3 = st.columns(3)
            m1.metric("Faturamento", f"R$ {df_f['Valor_Bruto'].sum():.2f}")
            m2.metric("Lucro Líquido", f"R$ {df_f['Lucro_Liquido'].sum():.2f}")
            m3.metric("Ticket Médio", f"R$ {(df_f['Valor_Bruto'].mean() if not df_f.empty else 0):.2f}")

            st.divider()
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                # Evolução por dia
                v_dia = df_f.groupby('Data_Formatada')['Valor_Bruto'].sum().reset_index()
                st.plotly_chart(px.line(v_dia, x='Data_Formatada', y='Valor_Bruto', title="Faturamento Diário", markers=True, color_discrete_sequence=['#FF8C00']), use_container_width=True)
            with col_g2:
                # Ranking respeitando o filtro de data
                rank = df_f.groupby('Produto').size().reset_index(name='Qtd').sort_values('Qtd', ascending=True)
                st.plotly_chart(px.bar(rank, x='Qtd', y='Produto', orientation='h', title="Ranking de Saída (Filtro Ativo)", color_discrete_sequence=['#FF8C00']), use_container_width=True)
            
            # Gráfico de Canais (Pizza)
            st.plotly_chart(px.pie(df_f, names='Canal', title="Origem dos Pedidos (iFood vs Whats)", hole=0.4, color_discrete_sequence=['#FF8C00', '#32CD32']), use_container_width=True)

    with tab3:
        st.subheader("Gerenciar Histórico")
        df_h = load_data()
        if not df_h.empty:
            st.write("Marque a caixa 'Deletar' e clique no botão para excluir:")
            df_h['Deletar'] = False
            # Reorganiza para facilitar visualização
            cols = ['Deletar', 'Data', 'Hora', 'Produto', 'Canal', 'Valor_Bruto', 'Lucro_Liquido']
            edited_df = st.data_editor(df_h[cols].iloc[::-1], hide_index=True, use_container_width=True)
            
            if st.button("🗑️ EXCLUIR SELECIONADOS"):
                indices_manter = edited_df[edited_df['Deletar'] == False].index
                df_final_del = df_h.loc[indices_manter].drop(columns=['Data_Formatada', 'Deletar'], errors='ignore')
                conn.update(worksheet="Vendas", data=df_final_del)
                st.rerun()
