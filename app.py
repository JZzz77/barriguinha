import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Barriguinha Admin v1.5", layout="wide", page_icon="📊")

# Design CSS Reforçado para Mobile
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FF8C00; color: white; font-weight: bold; height: 3.5em; border: none; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #FF8C00; }
    div[data-testid="stExpander"] { border: none; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
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
            st.error("Senha Incorreta")
        return False
    return True

if check_password():
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        df = conn.read(worksheet="Vendas", ttl=0)
        if not df.empty:
            df['Data_Formatada'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        return df

    # --- INICIALIZAÇÃO DE ESTADO PARA DATA/HORA (Correção de Bug) ---
    hora_padrao = datetime.now() - timedelta(hours=3)
    if "data_venda_v15" not in st.session_state:
        st.session_state["data_venda_v15"] = hora_padrao.date()
    if "hora_venda_v15" not in st.session_state:
        st.session_state["hora_venda_v15"] = hora_padrao.time()

    # --- SIDEBAR ---
    st.sidebar.header("🎯 Parâmetros do Mês")
    meta_faturamento = st.sidebar.number_input("Meta Mensal (R$)", value=5000)
    custos_fixos = st.sidebar.number_input("Custos Fixos (Luz/Internet/MEI)", value=300)
    
    st.sidebar.divider()
    preco_carne = st.sidebar.number_input("Preço Carne KG", value=34.90)
    preco_pao = st.sidebar.number_input("Preço Pão (4 unid)", value=5.90) / 4
    cmv_base = (preco_carne * 0.12) + preco_pao + 5.30

    # --- ABAS ---
    tab1, tab2, tab3 = st.tabs(["📝 PDV (Vendas)", "📈 Gestão e BI", "📜 Histórico"])

    # --- TAB 1: PDV (Com Correção de Hora) ---
    with tab1:
        with st.expander("✨ Registrar Novo Pedido", expanded=True):
            c1, c2 = st.columns(2)
            # Usando as chaves de estado para manter o valor mesmo após refresh
            data_sel = c1.date_input("Data da Venda", key="data_venda_v15")
            hora_sel = c2.time_input("Hora da Venda", key="hora_venda_v15")
            
            canal = st.radio("Origem", ["WhatsApp", "iFood"], horizontal=True)
            produto = st.selectbox("O que saiu?", ["Smash de Responsa", "Artesanal de Lei", "Supremo Barriguinha", "Bruto de Respeito", "Combo Tanquinho", "Combo Pochete", "Combo Barriguinha", "Combo Barrigona", "Combo Pança"])

            precos = {
                "iFood": {"Smash de Responsa": 19.9, "Artesanal de Lei": 29.9, "Supremo Barriguinha": 32.9, "Bruto de Respeito": 42.9, "Combo Tanquinho": 39.9, "Combo Pochete": 46.9, "Combo Barriguinha": 49.9, "Combo Barrigona": 59.9, "Combo Pança": 119.9},
                "WhatsApp": {"Smash de Responsa": 17.9, "Artesanal de Lei": 26.9, "Supremo Barriguinha": 29.9, "Bruto de Respeito": 38.9, "Combo Tanquinho": 32.9, "Combo Pochete": 39.9, "Combo Barriguinha": 44.9, "Combo Barrigona": 52.9, "Combo Pança": 99.9}
            }
            
            valor_venda = precos[canal][produto]
            st.metric("Total Pedido", f"R$ {valor_venda:.2f}")

            if st.button("🚀 FINALIZAR E SALVAR"):
                taxa = 0.26 if canal == "iFood" else 0.0
                lucro_un = (valor_venda * (1 - taxa)) - cmv_base
                
                novo_p = pd.DataFrame([{
                    "Data": data_sel.strftime("%d/%m/%Y"),
                    "Hora": hora_sel.strftime("%H:%M"),
                    "Produto": produto,
                    "Canal": canal,
                    "Valor_Bruto": valor_venda,
                    "Lucro_Liquido": round(lucro_un, 2)
                }])
                
                df_antigo = load_data().drop(columns=['Data_Formatada'], errors='ignore')
                df_novo = pd.concat([df_antigo, novo_p], ignore_index=True)
                conn.update(worksheet="Vendas", data=df_novo)
                
                st.success("Venda registrada com sucesso!")
                st.balloons()

    # --- TAB 2: GESTÃO E BI (Visão de Dono) ---
    with tab2:
        df = load_data()
        if not df.empty:
            # Filtro de Período
            col_f1, col_f2 = st.columns(2)
            hoje = datetime.now() - timedelta(hours=3)
            inicio_mes = hoje.replace(day=1)
            d_ini = col_f1.date_input("De:", inicio_mes.date())
            d_fim = col_f2.date_input("Até:", hoje.date())
            
            df_f = df[(df['Data_Formatada'].dt.date >= d_ini) & (df['Data_Formatada'].dt.date <= d_fim)]

            # MÉTRICAS DE GESTÃO
            m1, m2, m3 = st.columns(3)
            fat_bruto = df_f['Valor_Bruto'].sum()
            lucro_op = df_f['Lucro_Liquido'].sum()
            
            m1.metric("Faturamento Período", f"R$ {fat_bruto:.2f}")
            m2.metric("Lucro Operacional (Bruto)", f"R$ {lucro_op:.2f}")
            
            # --- LÓGICA DE PONTO DE EQUILÍBRIO (BREAK-EVEN) ---
            ticket_medio_lucro = lucro_op / len(df_f) if len(df_f) > 0 else 0
            falta_pagar = custos_fixos - lucro_op
            
            if falta_pagar > 0:
                lanches_faltantes = int(falta_pagar / ticket_medio_lucro) if ticket_medio_lucro > 0 else 0
                m3.metric("Falta p/ Pagar Contas", f"R$ {falta_pagar:.2f}", delta=f"{lanches_faltantes} lanches", delta_color="inverse")
                st.warning(f"💡 Você ainda precisa lucrar **R$ {falta_pagar:.2f}** para cobrir seus custos fixos de R$ {custos_fixos:.2f}. Isso equivale a aproximadamente **{lanches_faltantes} pedidos**.")
            else:
                m3.metric("Status Mensal", "PAGO!", delta="Lucro Real Ativo", delta_color="normal")
                st.success(f"🚀 Parabéns! Você já cobriu os custos fixos e está no **Lucro Real de R$ {abs(falta_pagar):.2f}**.")

            st.divider()
            
            # GRÁFICOS
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                v_dia = df_f.groupby('Data_Formatada')['Valor_Bruto'].sum().reset_index()
                st.plotly_chart(px.line(v_dia, x='Data_Formatada', y='Valor_Bruto', title="Evolução de Vendas", markers=True, color_discrete_sequence=['#FF8C00']), use_container_width=True)
            with c_g2:
                rank = df_f.groupby('Produto').size().reset_index(name='Qtd').sort_values('Qtd', ascending=True)
                st.plotly_chart(px.bar(rank, x='Qtd', y='Produto', orientation='h', title="Ranking de Saída", color_discrete_sequence=['#FF8C00']), use_container_width=True)
        else:
            st.info("Nenhuma venda registrada para análise.")

    # --- TAB 3: HISTÓRICO ---
    with tab3:
        st.subheader("Livro de Vendas")
        df_h = load_data()
        if not df_h.empty:
            st.dataframe(df_h.drop(columns=['Data_Formatada']).iloc[::-1], use_container_width=True)
            if st.button("🗑️ Excluir Último Registro"):
                df_h = df_h.drop(df_h.index[-1])
                conn.update(worksheet="Vendas", data=df_h.drop(columns=['Data_Formatada'], errors='ignore'))
                st.rerun()
