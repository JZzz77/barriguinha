import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin v2.2", layout="wide", page_icon="🍔")

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
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.title("🔐 Acesso Administrativo")
        st.text_input("Senha:", type="password", on_change=password_entered, key="password_input")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Senha Incorreta! Tente novamente.")
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

    # --- BANCO DE DADOS DINÂMICO (Atualizado com 80g e Dobradinha) ---
    if "menu_df" not in st.session_state:
        dados_iniciais = [
            {"Produto": "Smash de Responsa", "Preço Whats": 17.9, "Preço iFood": 19.9, "Carne (g)": 80, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Dobradinha de Responsa", "Preço Whats": 24.9, "Preço iFood": 27.9, "Carne (g)": 160, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Artesanal de Lei", "Preço Whats": 26.9, "Preço iFood": 29.9, "Carne (g)": 120, "Queijo": True, "Bacon": False, "Salada": True, "Cebola": False, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Supremo Barriguinha", "Preço Whats": 29.9, "Preço iFood": 32.9, "Carne (g)": 120, "Queijo": True, "Bacon": True, "Salada": True, "Cebola": True, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Bruto de Respeito", "Preço Whats": 38.9, "Preço iFood": 42.9, "Carne (g)": 240, "Queijo": True, "Bacon": True, "Salada": True, "Cebola": True, "Combo": False, "Refri": False, "Batata": False},
            {"Produto": "Combo Tanquinho (Smash)", "Preço Whats": 27.9, "Preço iFood": 32.9, "Carne (g)": 80, "Queijo": True, "Bacon": False, "Salada": False, "Cebola": False, "Combo": True, "Refri": False, "Batata": False},
            {"Produto": "Refri Lata", "Preço Whats": 5.0, "Preço iFood": 7.0, "Carne (g)": 0, "Queijo": False, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": True, "Batata": False},
            {"Produto": "Batata Frita (100g)", "Preço Whats": 8.0, "Preço iFood": 10.0, "Carne (g)": 0, "Queijo": False, "Bacon": False, "Salada": False, "Cebola": False, "Combo": False, "Refri": False, "Batata": True}
        ]
        st.session_state["menu_df"] = pd.DataFrame(dados_iniciais)

    # --- SIDEBAR: PARÂMETROS E INSUMOS ---
    st.sidebar.header("🎯 Metas e Custos Fixos")
    meta_mensal = st.sidebar.number_input("Meta Mensal (R$)", value=5000.0)
    custos_fixos = st.sidebar.number_input("Custos Fixos (Luz/MEI/etc)", value=300.0)
    
    st.sidebar.divider()
    st.sidebar.header("🛒 Insumos Variáveis")
    p_carne = st.sidebar.number_input("Carne KG", value=34.90)
    p_pao = st.sidebar.number_input("Pão Unit.", value=1.47)
    p_queijo = st.sidebar.number_input("Queijo (Porção)", value=2.10)
    p_bacon = st.sidebar.number_input("Bacon (Porção)", value=1.35)
    p_salada = st.sidebar.number_input("Alface/Tomate", value=0.80)
    p_cebola = st.sidebar.number_input("Cebola", value=0.20)
    p_fixo = st.sidebar.number_input("Embalagem/Molho", value=2.50)
    
    st.sidebar.divider()
    st.sidebar.header("🥤 Acompanhamentos")
    p_refri = st.sidebar.number_input("Custo Refri", value=2.50)
    p_batata = st.sidebar.number_input("Custo Batata 100g", value=1.80)

    def calcular_custo_dinamico(nome_produto):
        menu = st.session_state["menu_df"]
        produto_info = menu[menu["Produto"] == nome_produto]
        if produto_info.empty: return 0
        
        prod = produto_info.iloc[0]
        if prod.get("Refri", False): return p_refri
        if prod.get("Batata", False): return p_batata + (p_fixo * 0.3)
        
        custo = p_pao + p_fixo
        custo += (p_carne * (prod["Carne (g)"] / 1000.0))
        # Se for dobradinha, assume o dobro de queijo para margem de segurança
        if prod["Queijo"]: custo += (p_queijo * 2) if prod["Carne (g)"] >= 160 else p_queijo
        if prod["Bacon"]: custo += p_bacon
        if prod["Salada"]: custo += p_salada
        if prod["Cebola"]: custo += p_cebola
        if prod["Combo"]: custo += (p_batata + p_refri) 
        
        return custo

    tab1, tab2, tab3 = st.tabs(["📝 PDV & Cardápio", "📈 Dashboard", "📜 Histórico"])

    with tab1:
        with st.expander("✨ Registrar Novo Pedido", expanded=True):
            hora_padrao = datetime.now() - timedelta(hours=3)
            if "d_v" not in st.session_state: st.session_state["d_v"] = hora_padrao.date()
            if "h_v" not in st.session_state: st.session_state["h_v"] = hora_padrao.time()

            c1, c2 = st.columns(2)
            data_sel = c1.date_input("Data", key="d_v")
            hora_sel = c2.time_input("Hora", key="h_v")
            
            canal = st.radio("Canal", ["WhatsApp", "iFood"], horizontal=True)
            lista_produtos = st.session_state["menu_df"]["Produto"].tolist()
            produtos_selecionados = st.multiselect("Monte o Pedido:", lista_produtos, default=[lista_produtos[0]])

            if produtos_selecionados:
                v_venda_total = 0
                custo_total = 0
                
                for p in produtos_selecionados:
                    prod_info = st.session_state["menu_df"][st.session_state["menu_df"]["Produto"] == p].iloc[0]
                    v_venda_total += prod_info["Preço iFood"] if canal == "iFood" else prod_info["Preço Whats"]
                    custo_total += calcular_custo_dinamico(p)
                
                st.metric("Total a Cobrar", f"R$ {v_venda_total:.2f}")

                if st.button("🚀 REGISTRAR VENDA"):
                    taxa = 0.26 if canal == "iFood" else 0.0
                    lucro = (v_venda_total * (1 - taxa)) - custo_total
                    nome_pedido = " + ".join(produtos_selecionados)
                    
                    novo = pd.DataFrame([{"Data": data_sel.strftime("%d/%m/%Y"), "Hora": hora_sel.strftime("%H:%M"), "Produto": nome_pedido, "Canal": canal, "Valor_Bruto": v_venda_total, "Lucro_Liquido": round(lucro, 2)}])
                    conn.update(worksheet="Vendas", data=pd.concat([load_data().drop(columns=['Data_Formatada'], errors='ignore'), novo], ignore_index=True))
                    st.success(f"Salvo! Custo: R$ {custo_total:.2f} | Lucro: R$ {lucro:.2f}")
                    st.balloons()
            else:
                st.warning("Selecione um item.")

        with st.expander("🍔 Editor de Cardápio (Ajuste os Combos Aqui)", expanded=False):
            st.write("Atualize os valores dos seus Combos seguindo a regra dos 10% de desconto!")
            menu_editado = st.data_editor(st.session_state["menu_df"], num_rows="dynamic", use_container_width=True)
            st.session_state["menu_df"] = menu_editado

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
            ticket_medio_lucro = lucro_op / len(df_f) if len(df_f) > 0 else 0
            falta_pagar = custos_fixos - lucro_op

            m1.metric("Faturamento", f"R$ {faturamento_total:.2f}")
            m2.metric("Lucro Op.", f"R$ {lucro_op:.2f}")
            
            if falta_pagar > 0:
                l_faltantes = int(falta_pagar / ticket_medio_lucro) if ticket_medio_lucro > 0 else 0
                m3.metric("Falta p/ Contas", f"R$ {falta_pagar:.2f}", delta=f"{l_faltantes} lanches", delta_color="inverse")
            else:
                m3.metric("Lucro Real", f"R$ {abs(falta_pagar):.2f}", delta="No Bolso!", delta_color="normal")

            st.write(f"**Progresso (Meta: R$ {meta_mensal:.2f}):**")
            st.progress(min(faturamento_total / meta_mensal, 1.0) if meta_mensal > 0 else 1.0)

            df_f['Acumulado'] = df_f['Valor_Bruto'].cumsum()
            fig_meta = go.Figure()
            fig_meta.add_trace(go.Scatter(x=df_f['Data_Formatada'], y=df_f['Acumulado'], mode='lines+markers', name='Faturamento', line=dict(color='#FF8C00', width=4)))
            fig_meta.add_hline(y=meta_mensal, line_dash="dash", line_color="red", annotation_text=f"Meta: R$ {meta_mensal}")
            st.plotly_chart(fig_meta, use_container_width=True)

            c_g1, c_g2 = st.columns(2)
            with c_g1: st.plotly_chart(px.bar(df_f.groupby('Produto').size().reset_index(name='Qtd').sort_values('Qtd'), x='Qtd', y='Produto', orientation='h', title="Mais Vendidos", color_discrete_sequence=['#FF8C00']), use_container_width=True)
            with c_g2: st.plotly_chart(px.pie(df_f, names='Canal', title="iFood vs Whats", hole=0.4, color_discrete_sequence=['#FF8C00', '#32CD32']), use_container_width=True)

    with tab3:
        st.subheader("Histórico")
        df_h = load_data()
        if not df_h.empty:
            df_h['Deletar'] = False
            edited_df = st.data_editor(df_h[['Deletar', 'Data', 'Hora', 'Produto', 'Canal', 'Valor_Bruto', 'Lucro_Liquido']].iloc[::-1], hide_index=True, use_container_width=True)
            if st.button("🗑️ EXCLUIR SELECIONADOS"):
                conn.update(worksheet="Vendas", data=df_h.loc[edited_df[edited_df['Deletar'] == False].index].drop(columns=['Data_Formatada', 'Deletar'], errors='ignore'))
                st.rerun()
