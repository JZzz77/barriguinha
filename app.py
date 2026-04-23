import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO E LOGIN (Mantidos para estabilidade)
st.set_page_config(page_title="Barriguinha Admin v2.7", layout="wide", page_icon="🍔")
st.markdown("""<style>.stButton>button { width: 100%; border-radius: 8px; background-color: #FF8C00; color: white !important; font-weight: bold; height: 3.5em; border: none; } [data-testid="stMetricValue"] { color: #FF8C00 !important; font-weight: bold; } div[data-testid="stMetric"] { background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #FF8C00; } div[data-testid="stExpander"] { border: none; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; } .carrinho-box { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 4px solid #32CD32; margin-bottom: 10px; color: #333; }</style>""", unsafe_allow_html=True)

def check_password():
    def password_entered():
        if st.session_state["password_input"] == "BARRIGA2024": st.session_state["password_correct"] = True
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
                if 'Telefone_Cliente' in df.columns: df['Telefone_Cliente'] = df['Telefone_Cliente'].astype(str).str.replace('.0', '', regex=False)
            return df
        except: return pd.DataFrame()

    if "carrinho" not in st.session_state: st.session_state["carrinho"] = []

    # --- BANCO DE DADOS INTEGRADO (Lanches + Bebidas + Batatas) ---
    if "menu_df" not in st.session_state:
        dados = [
            {"Produto": "Smash de Responsa", "Preço Whats": 16.9, "Preço iFood": 19.9, "Carne (g)": 80, "Queijo": True, "Combo": False, "Tipo": "Lanche"},
            {"Produto": "Dobradinha Smash", "Preço Whats": 22.9, "Preço iFood": 27.9, "Carne (g)": 160, "Queijo": True, "Combo": False, "Tipo": "Lanche"},
            {"Produto": "Combo Tanquinho", "Preço Whats": 27.9, "Preço iFood": 32.9, "Carne (g)": 80, "Queijo": True, "Combo": True, "Tipo": "Lanche"},
            {"Produto": "Batata P (100g)", "Preço Whats": 8.9, "Preço iFood": 11.9, "Carne (g)": 0, "Queijo": False, "Combo": False, "Tipo": "Batata"},
            {"Produto": "Batata M (200g)", "Preço Whats": 15.9, "Preço iFood": 19.9, "Carne (g)": 0, "Queijo": False, "Combo": False, "Tipo": "Batata"},
            {"Produto": "Batata G (350g)", "Preço Whats": 24.9, "Preço iFood": 32.9, "Carne (g)": 0, "Queijo": False, "Combo": False, "Tipo": "Batata"},
            {"Produto": "Adicional Cheddar/Bacon", "Preço Whats": 6.0, "Preço iFood": 8.0, "Carne (g)": 0, "Queijo": False, "Combo": False, "Tipo": "Adicional"},
            {"Produto": "Coca 2L", "Preço Whats": 14.9, "Preço iFood": 18.9, "Carne (g)": 0, "Queijo": False, "Combo": False, "Tipo": "Bebida"},
            {"Produto": "Refris Lata", "Preço Whats": 5.9, "Preço iFood": 7.9, "Carne (g)": 0, "Queijo": False, "Combo": False, "Tipo": "Bebida"},
            {"Produto": "Suco Del Valle", "Preço Whats": 7.9, "Preço iFood": 9.9, "Carne (g)": 0, "Queijo": False, "Combo": False, "Tipo": "Bebida"},
            {"Produto": "Água sem Gás", "Preço Whats": 3.9, "Preço iFood": 5.9, "Carne (g)": 0, "Queijo": False, "Combo": False, "Tipo": "Bebida"}
        ]
        st.session_state["menu_df"] = pd.DataFrame(dados)

    # --- SIDEBAR CUSTOS ---
    st.sidebar.header("🛒 Custos Insumos")
    p_carne = st.sidebar.number_input("Carne KG", value=34.90)
    p_refri_lata = st.sidebar.number_input("Custo Refri Lata", value=2.50)
    p_coca_2l = st.sidebar.number_input("Custo Coca 2L", value=8.50)
    p_batata_kg = st.sidebar.number_input("Custo Batata KG (Congelada)", value=18.00)

    def calcular_custo_v2(nome):
        prod = st.session_state["menu_df"][st.session_state["menu_df"]["Produto"] == nome].iloc[0]
        if prod["Tipo"] == "Bebida":
            return p_coca_2l if "2L" in nome else p_refri_lata
        if prod["Tipo"] == "Batata":
            gramas = 100 if "P" in nome else (200 if "M" in nome else 350)
            return (p_batata_kg * (gramas/1000)) + 0.80 # + embalagem
        if prod["Tipo"] == "Adicional": return 2.00
        # Lanches (Simplificado p/ o exemplo, mantendo sua lógica anterior)
        custo = 1.47 + 1.50 + (p_carne * (prod["Carne (g)"] / 1000.0)) + 2.10
        if prod["Combo"]: custo += (p_batata_kg * 0.1) + p_refri_lata
        return custo

    tab1, tab2, tab3 = st.tabs(["📝 PDV", "📈 Dash", "💎 VIPs"])

    with tab1:
        with st.expander("✨ Novo Pedido", expanded=True):
            c1, c2 = st.columns(2)
            canal = c1.radio("Canal", ["WhatsApp", "iFood"], horizontal=True)
            tel = c2.text_input("WhatsApp Cliente (Apenas Números):", max_chars=11)
            if canal == "iFood": tel = "99999999999"
            
            st.divider()
            col_p, col_q, col_b = st.columns([3, 1, 1])
            p_sel = col_p.selectbox("Item:", st.session_state["menu_df"]["Produto"].tolist())
            q_sel = col_q.number_input("Qtd:", min_value=1, value=1)
            if col_btn := col_b.button("➕"):
                st.session_state["carrinho"].append({"Produto": p_sel, "Qtd": q_sel})
                st.rerun()

            if st.session_state["carrinho"]:
                v_total, c_total, nomes = 0, 0, []
                for i in st.session_state["carrinho"]:
                    p_info = st.session_state["menu_df"][st.session_state["menu_df"]["Produto"] == i["Produto"]].iloc[0]
                    v_un = p_info["Preço iFood"] if canal == "iFood" else p_info["Preço Whats"]
                    v_total += v_un * i["Qtd"]; c_total += calcular_custo_v2(i["Produto"]) * i["Qtd"]
                    nomes.append(f"{i['Qtd']}x {i['Produto']}")
                
                st.info(f"🛒 Carrinho: {', '.join(nomes)}")
                st.metric("Total", f"R$ {v_total:.2f}")
                if st.button("🚀 SALVAR VENDA"):
                    taxa = 0.26 if canal == "iFood" else 0.0
                    lucro = (v_total * (1 - taxa)) - c_total
                    novo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y"), "Hora": datetime.now().strftime("%H:%M"), "Telefone_Cliente": tel, "Produto": " + ".join(nomes), "Canal": canal, "Valor_Bruto": v_total, "Lucro_Liquido": round(lucro, 2)}])
                    conn.update(worksheet="Vendas", data=pd.concat([load_data().drop(columns=['Data_Formatada'], errors='ignore'), novo], ignore_index=True))
                    st.session_state["carrinho"] = []; st.success("Venda salva!"); st.balloons()
