import streamlit as st
import pandas as pd
from streamlit_app import DashboardTecnicos, load_css

def main():
    st.set_page_config(
        page_title="Resumo por Base",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Carrega o CSS
    load_css()
    
    st.title("📊 Resumo por Base")
    
    dashboard = DashboardTecnicos()
    arquivos = dashboard.listar_arquivos()
    
    if not arquivos:
        st.error("Nenhum arquivo encontrado na pasta Dados_excel")
        return
        
    arquivo = arquivos[0]  # Usa o primeiro arquivo encontrado
    
    if dashboard.carregar_dados(arquivo):
        # Usa todos os dados sem filtros
        dashboard.mostrar_tabela_bases(dashboard.dados)

if __name__ == "__main__":
    main() 