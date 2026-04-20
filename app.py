import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin v2.5", layout="wide", page_icon="🍔")

# Design CSS (Estabilidade e Contraste)
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
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Senha Incorreta!")
        return False
    return True

if check_password():
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        try:
            df = conn.read(worksheet="Vendas", ttl=0)
            if not df.empty:
                df['Data_Formatada'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
                # Força o telefone a ser string limpa para evitar o .0
                if 'Telefone_Cliente' in df.columns:
                    df['Telefone_Cliente'] = df['Telefone_Cliente'].astype(str).str.replace('.0', '', regex=False)
            return df
        except: return pd.DataFrame()

    # --- BANCO DE DADOS DO CARDÁPIO ---
    if "menu_df" not in st.session_state:
        dados_iniciais = [
            {"Produto": "Smash de Responsa", "Preço Whats": 17.9, "Preço iFood": 19.9, "Carne (g)": 80, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Dobradinha Smash", "Preço Whats": 22.9, "Preço iFood": 27.9, "Carne (g)": 160, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Artesanal de Lei", "Preço Whats": 26.9, "Preço iFood": 29.9, "Carne (g)": 120, "Queijo": True, "Bacon": False, "Salada": True, "Cebola": False, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Supremo Barriguinha", "Preço Whats": 29.9, "Preço iFood": 32.9, "Carne (g)": 120, "Queijo": True, "Bacon": True, "Salada": True, "Cebola": True, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Bruto de Respeito", "Preço Whats": 34.9, "Preço iFood": 39.9, "Carne (g)": 240, "Queijo": True, "Bacon": True, "Salada": True, "Cebola": True, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Combo Tanquinho (Smash)", "Preço Whats": 27.9, "Preço iFood": 32.9, "Carne (g)": 80, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": True, "Refri": False, "Batata": False},
            {"Produto": "Refri Lata", "Preço Whats": 5.0, "Preço iFood": 7.0, "Carne (g)": 0, "Queijo": False, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": True, "Batata": False},
            {"Produto": "Batata Frita (100g)", "Preço Whats": 8.0, "Preço iFood": 10.0, "Carne (g)": 0, "Queijo": False, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": True}
        ]
        st.session_state["menu_df"] = pd.DataFrame(dados_iniciais)

    # --- SIDEBAR: PARÂMETROS E CUSTOS ---
    st.sidebar.header("🎯 Metas e Custos")
    meta_mensal = st.sidebar.number_input("Meta Mensal (R$)", value=5000.0)
    custos_fixos = st.sidebar.number_input("Custos Fixos (Luz/etc)", value=300.0)
    
    st.sidebar.divider()
    st.sidebar.header("🥩 Insumos")
    p_carne = st.sidebar.number_input("Carne KG", value=34.90)
    p_pao = st.sidebar.number_input("Pão Unit.", value=1.47)
    p_queijo = st.sidebar.number_input("Queijo (Porção)", value=2.10)
    p_bacon = st.sidebar.number_input("Bacon (Porção)", value=1.35)
    p_salada = st.sidebar.number_input("Alface/Tomate", value=0.80)
    p_cebola = st.sidebar.number_input("Cebola", value=0.20)
    p_fixo = st.sidebar.number_input("Embalagem/Molho", value=1.50)
    
    st.sidebar.divider()
    st.sidebar.header("🥤 Acompanhamentos")
    p_refri = st.sidebar.number_input("Custo Refri", value=2.50)
    p_batata = st.sidebar.number_input("Custo Batata", value=1.80)

    def calcular_custo_dinamico(nome_produto):
        menu = st.session_state["menu_df"]
        produto_info = menu[menu["Produto"] == nome_produto]
        if produto_info.empty: return 0
        prod = produto_info.iloc[0]
        if prod.get("Refri", False): return p_refri
        if prod.get("Batata", False): return p_batata + 0.50
        custo = p_pao + p_fixo + (p_carne * (prod["Carne (g)"] / 1000.0))
        if prod["Queijo"]: custo += (p_queijo * 2) if prod["Carne (g)"] >= 160 else p_queijo
        if prod["Bacon"]: custo += p_bacon
        if prod["Salada"]: custo += p_salada
        if prod["Cebola"]: custo += p_cebola
        if prod["Combo"]: custo += (p_batata + p_refri)
        return custo

    tab1, tab2, tab3, tab4 = st.tabs(["📝 PDV & Cardápio", "📈 Dashboard", "💎 VIPs", "📜 Histórico"])

    with tab1:
        with st.expander("✨ Registrar Novo Pedido", expanded=True):
            hora_padrao = datetime.now() - timedelta(hours=3)
            if "d_v" not in st.session_state: st.session_state["d_v"] = hora_padrao.date()
            if "h_v" not in st.session_state: st.session_state["h_v"] = hora_padrao.time()

            c1, c2 = st.columns(2)
            data_sel = c1.date_input("Data do Pedido", key="d_v")
            hora_sel = c2.time_input("Hora do Pedido", key="h_v")
            
            canal = st.radio("Canal de Venda", ["WhatsApp", "iFood"], horizontal=True)
            
            # Lógica Automática iFood
            if canal == "iFood":
                tel_cliente = st.text_input("WhatsApp do Cliente:", value="99999999999", disabled=True)
            else:
                tel_cliente = st.text_input("WhatsApp do Cliente (DDD + Número):", max_chars=11, help="Apenas números, max 11 dígitos.")
            
            lista_produtos = st.session_state["menu_df"]["Produto"].tolist()
            selecionados = st.multiselect("Itens do Pedido:", lista_produtos)

            if selecionados and tel_cliente:
                v_total = 0
                c_total = 0
                for p in selecionados:
                    p_info = st.session_state["menu_df"][st.session_state["menu_df"]["Produto"] == p].iloc[0]
                    v_total += p_info["Preço iFood"] if canal == "iFood" else p_info["Preço Whats"]
                    c_total += calcular_custo_dinamico(p)
                
                st.metric("Total a Cobrar", f"R$ {v_total:.2f}")
                if st.button("🚀 FINALIZAR E SALVAR"):
                    taxa = 0.26 if canal == "iFood" else 0.0
                    lucro = (v_total * (1 - taxa)) - c_total
                    novo = pd.DataFrame([{"Data": data_sel.strftime("%d/%m/%Y"), "Hora": hora_sel.strftime("%H:%M"), "Telefone_Cliente": str(tel_cliente), "Produto": " + ".join(selecionados), "Canal": canal, "Valor_Bruto": v_total, "Lucro_Liquido": round(lucro, 2)}])
                    conn.update(worksheet="Vendas", data=pd.concat([load_data().drop(columns=['Data_Formatada'], errors='ignore'), novo], ignore_index=True))
                    st.success("Venda registrada com sucesso!")
                    st.balloons()
            else: st.warning("Informe o telefone e os itens.")

        with st.expander("🍔 Editor de Cardápio e Receitas", expanded=False):
            menu_editado = st.data_editor(st.session_state["menu_df"], num_rows="dynamic", use_container_width=True)
            st.session_state["menu_df"] = menu_editado

    with tab2:
        df = load_data()
        if not df.empty:
            hoje = datetime.now().date()
            d_ini = st.date_input("Início", hoje - timedelta(days=7))
            d_fim = st.date_input("Fim", hoje)
            df_f = df[(df['Data_Formatada'].dt.date >= d_ini) & (df['Data_Formatada'].dt.date <= d_fim)].sort_values('Data_Formatada')

            m1, m2, m3 = st.columns(3)
            fat = df_f['Valor_Bruto'].sum()
            lucro_op = df_f['Lucro_Liquido'].sum()
            ticket_medio_lucro = lucro_op / len(df_f) if len(df_f) > 0 else 0
            falta_pagar = custos_fixos - lucro_op

            m1.metric("Faturamento", f"R$ {fat:.2f}")
            m2.metric("Lucro Op.", f"R$ {lucro_op:.2f}")
            if falta_pagar > 0:
                l_faltantes = int(falta_pagar / ticket_medio_lucro) if ticket_medio_lucro > 0 else 0
                m3.metric("Falta p/ Contas", f"R$ {falta_pagar:.2f}", delta=f"{l_faltantes} lanches", delta_color="inverse")
                st.warning(f"💡 Você ainda precisa lucrar **R$ {falta_pagar:.2f}** para pagar os custos fixos.")
            else:
                m3.metric("Lucro Real", f"R$ {abs(falta_pagar):.2f}", delta="PAGO!", delta_color="normal")
                st.success(f"🚀 Você já cobriu os custos fixos!")

            st.write(f"**Progresso Meta Mensal (R$ {meta_mensal:.2f}):**")
            st.progress(min(fat / meta_mensal, 1.0) if meta_mensal > 0 else 1.0)

            st.subheader("📈 Evolução Acumulada")
            df_f['Acumulado'] = df_f['Valor_Bruto'].cumsum()
            fig_meta = go.Figure()
            fig_meta.add_trace(go.Scatter(x=df_f['Data_Formatada'], y=df_f['Acumulado'], mode='lines+markers', name='Real', line=dict(color='#FF8C00', width=4)))
            fig_meta.add_hline(y=meta_mensal, line_dash="dash", line_color="red")
            st.plotly_chart(fig_meta, use_container_width=True)

            c_g1, c_g2 = st.columns(2)
            with c_g1:
                rank = df_f.groupby('Produto').size().reset_index(name='Qtd').sort_values('Qtd')
                st.plotly_chart(px.bar(rank, x='Qtd', y='Produto', orientation='h', title="Mais Vendidos", color_discrete_sequence=['#FF8C00']), use_container_width=True)
            with c_g2:
                st.plotly_chart(px.pie(df_f, names='Canal', title="iFood vs Whats", hole=0.4, color_discrete_sequence=['#FF8C00', '#32CD32']), use_container_width=True)

    with tab3:
        st.subheader("💎 Carteira VIP")
        df_v = load_data()
        if not df_v.empty and 'Telefone_Cliente' in df_v.columns:
            clientes = df_v.groupby('Telefone_Cliente').agg({'Valor_Bruto': 'sum', 'Data_Formatada': 'max', 'Produto': 'count'}).rename(columns={'Produto': 'Compras', 'Data_Formatada': 'Última'}).sort_values('Valor_Bruto', ascending=False)
            clientes['Dias Inativo'] = (datetime.now() - clientes['Última']).dt.days
            st.dataframe(clientes, use_container_width=True)

    with tab4:
        df_h = load_data()
        if not df_h.empty:
            df_h['🗑️'] = False
            ed = st.data_editor(df_h[['🗑️', 'Data', 'Hora', 'Telefone_Cliente', 'Produto', 'Valor_Bruto', 'Lucro_Liquido']].iloc[::-1], hide_index=True, use_container_width=True)
            if st.button("EXCLUIR SELECIONADOS"):
                conn.update(worksheet="Vendas", data=df_h.loc[ed[ed['🗑️'] == False].index].drop(columns=['Data_Formatada', '🗑️'], errors='ignore'))
                st.rerun()
