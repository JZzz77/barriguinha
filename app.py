import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin v2.4", layout="wide", page_icon="🍔")

# Design CSS Adaptável
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FF8C00; color: white !important; font-weight: bold; height: 3.5em; border: none; }
    [data-testid="stMetricValue"] { color: #FF8C00 !important; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #FF8C00; }
    div[data-testid="stExpander"] { border: none; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE LOGIN
def check_password():
    def password_entered():
        if st.session_state["password_input"] == "BARRIGA2024":
            st.session_state["password_correct"] = True
        else: st.session_state["password_correct"] = False
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
                if 'Telefone_Cliente' in df.columns:
                    df['Telefone_Cliente'] = df['Telefone_Cliente'].astype(str)
            return df
        except: return pd.DataFrame()

    # --- BANCO DE DADOS DO CARDÁPIO ---
    if "menu_df" not in st.session_state:
        dados_iniciais = [
            {"Produto": "Smash de Responsa", "Preço Whats": 17.9, "Preço iFood": 19.9, "Carne (g)": 80, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Dobradinha Smash", "Preço Whats": 22.9, "Preço iFood": 27.9, "Carne (g)": 160, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Combo Tanquinho (Smash)", "Preço Whats": 27.9, "Preço iFood": 32.9, "Carne (g)": 80, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": True, "Refri": False, "Batata": False},
            {"Produto": "Refri Lata", "Preço Whats": 5.0, "Preço iFood": 7.0, "Carne (g)": 0, "Queijo": False, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": True, "Batata": False},
            {"Produto": "Batata Frita (100g)", "Preço Whats": 8.0, "Preço iFood": 10.0, "Carne (g)": 0, "Queijo": False, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": True}
        ]
        st.session_state["menu_df"] = pd.DataFrame(dados_iniciais)

    # --- SIDEBAR: CUSTOS TOTAIS ---
    st.sidebar.header("🎯 Metas e Custos")
    meta_mensal = st.sidebar.number_input("Meta Mensal (R$)", value=5000.0)
    custos_fixos = st.sidebar.number_input("Custos Fixos (Luz/etc)", value=300.0)
    
    st.sidebar.divider()
    st.sidebar.header("🥩 Insumos Carne/Pão")
    p_carne = st.sidebar.number_input("Carne KG", value=34.90)
    p_pao = st.sidebar.number_input("Pão Unit.", value=1.47)
    p_queijo = st.sidebar.number_input("Queijo (Porção)", value=2.10)
    p_fixo = st.sidebar.number_input("Embalagem/Molho", value=1.50)
    
    st.sidebar.divider()
    st.sidebar.header("🥤 Bebida e Batata")
    p_refri = st.sidebar.number_input("Custo Refri Lata", value=2.50)
    p_batata = st.sidebar.number_input("Custo Batata 100g", value=1.80)

    def calcular_custo_dinamico(nome_produto):
        menu = st.session_state["menu_df"]
        produto_info = menu[menu["Produto"] == nome_produto]
        if produto_info.empty: return 0
        prod = produto_info.iloc[0]
        if prod.get("Refri", False): return p_refri
        if prod.get("Batata", False): return p_batata + 0.50 # + mini-emb
        custo = p_pao + p_fixo + (p_carne * (prod["Carne (g)"] / 1000.0))
        if prod["Queijo"]: custo += (p_queijo * 2) if prod["Carne (g)"] >= 160 else p_queijo
        if prod["Combo"]: custo += (p_batata + p_refri)
        return custo

    tab1, tab2, tab3, tab4 = st.tabs(["📝 PDV", "📈 Dashboard", "💎 VIPs", "📜 Histórico"])

    with tab1:
        with st.expander("✨ Registrar Novo Pedido", expanded=True):
            c1, c2 = st.columns(2)
            tel_cliente = c1.text_input("WhatsApp do Cliente (Apenas Números):")
            canal = c2.radio("Canal de Venda", ["WhatsApp", "iFood"], horizontal=True)
            
            lista_produtos = st.session_state["menu_df"]["Produto"].tolist()
            selecionados = st.multiselect("Itens do Pedido:", lista_produtos)

            if selecionados and tel_cliente:
                v_total = 0
                c_total = 0
                for p in selecionados:
                    p_info = st.session_state["menu_df"][st.session_state["menu_df"]["Produto"] == p].iloc[0]
                    v_total += p_info["Preço iFood"] if canal == "iFood" else p_info["Preço Whats"]
                    c_total += calcular_custo_dinamico(p)
                
                st.metric("Total do Pedido", f"R$ {v_total:.2f}")
                if st.button("🚀 FINALIZAR"):
                    taxa = 0.26 if canal == "iFood" else 0.0
                    lucro = (v_total * (1 - taxa)) - c_total
                    novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y"), "Hora": datetime.now().strftime("%H:%M"), "Telefone_Cliente": tel_cliente, "Produto": " + ".join(selecionados), "Canal": canal, "Valor_Bruto": v_total, "Lucro_Liquido": round(lucro, 2)}])
                    conn.update(worksheet="Vendas", data=pd.concat([load_data().drop(columns=['Data_Formatada'], errors='ignore'), novo], ignore_index=True))
                    st.success("Venda registrada!")
                    st.balloons()
            else: st.warning("Informe o telefone e selecione os lanches/bebidas.")

    with tab2:
        df = load_data()
        if not df.empty:
            m1, m2, m3 = st.columns(3)
            fat = df['Valor_Bruto'].sum()
            lucro = df['Lucro_Liquido'].sum()
            m1.metric("Faturamento", f"R$ {fat:.2f}")
            m2.metric("Lucro Op.", f"R$ {lucro:.2f}")
            m3.metric("No Bolso (Pós Fixo)", f"R$ {(lucro - custos_fixos):.2f}")
            st.plotly_chart(px.line(df.groupby('Data_Formatada')['Valor_Bruto'].sum().reset_index(), x='Data_Formatada', y='Valor_Bruto', title="Evolução Diária"), use_container_width=True)

    with tab3:
        st.subheader("💎 Carteira de Clientes VIP (Pareto)")
        df_v = load_data()
        if not df_v.empty and 'Telefone_Cliente' in df_v.columns:
            clientes = df_v.groupby('Telefone_Cliente').agg({
                'Valor_Bruto': 'sum',
                'Data_Formatada': 'max',
                'Produto': 'count'
            }).rename(columns={'Produto': 'Qtd Compras', 'Data_Formatada': 'Última Vez'}).sort_values('Valor_Bruto', ascending=False)
            
            clientes['Dias Inativo'] = (datetime.now() - clientes['Última Vez']).dt.days
            corte = clientes['Valor_Bruto'].quantile(0.8)
            clientes['Status'] = clientes['Valor_Bruto'].apply(lambda x: '💎 VIP' if x >= corte else '🍔 Cliente')
            st.dataframe(clientes, use_container_width=True)

    with tab4:
        df_h = load_data()
        if not df_h.empty:
            df_h['Excluir'] = False
            edited = st.data_editor(df_h[['Excluir', 'Data', 'Hora', 'Telefone_Cliente', 'Produto', 'Valor_Bruto']].iloc[::-1], hide_index=True, use_container_width=True)
            if st.button("🗑️ APAGAR"):
                conn.update(worksheet="Vendas", data=df_h.loc[edited[edited['Excluir'] == False].index].drop(columns=['Data_Formatada', 'Excluir'], errors='ignore'))
                st.rerun()
