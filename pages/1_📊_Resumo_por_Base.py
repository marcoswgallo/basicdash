import streamlit as st
import pandas as pd
import numpy as np
from streamlit_app import DashboardTecnicos, load_css

def analise_inteligente(dados):
    """Gera insights automáticos dos dados"""
    insights = []
    
    # 1. Análise de Produtividade
    prod_por_base = dados.groupby('BASE').agg({
        'CONTRATO': 'count',
        'TECNICO': 'nunique',
        'VALOR EMPRESA': 'sum'
    })
    
    # Identifica bases mais produtivas
    prod_por_tecnico = prod_por_base['CONTRATO'] / prod_por_base['TECNICO']
    melhor_base = prod_por_tecnico.idxmax()
    pior_base = prod_por_tecnico.idxmin()
    
    insights.append(f"🏆 A base mais produtiva é **{melhor_base}** com média de "
                   f"**{prod_por_tecnico[melhor_base]:.1f}** contratos por técnico")
    
    # 2. Análise de Rentabilidade
    rent_por_base = prod_por_base['VALOR EMPRESA'] / prod_por_base['TECNICO']
    melhor_rent = rent_por_base.idxmax()
    
    insights.append(f"💰 A base mais rentável é **{melhor_rent}** com média de "
                   f"**R$ {rent_por_base[melhor_rent]:,.2f}** por técnico")
    
    # 3. Análise de Eficiência
    media_contratos = prod_por_tecnico.mean()
    bases_eficientes = prod_por_tecnico[prod_por_tecnico > media_contratos].index.tolist()
    
    insights.append(f"⭐ **{len(bases_eficientes)}** bases estão acima da média de "
                   f"produtividade ({media_contratos:.1f} contratos/técnico)")
    
    # 4. Análise de Desconexões
    desconexoes = dados[dados['TIPO DE SERVIÇO'].str.contains('DESCONEX', case=False, na=False)]
    taxa_desconexao = len(desconexoes) / len(dados) * 100
    
    insights.append(f"📉 Taxa de desconexão geral: **{taxa_desconexao:.1f}%** dos contratos")
    
    # 5. Análise de Tendências
    if 'DATA_TOA' in dados.columns:
        dados_recentes = dados[dados['DATA_TOA'] >= dados['DATA_TOA'].max() - pd.Timedelta(days=30)]
        bases_crescimento = dados_recentes.groupby('BASE')['CONTRATO'].count().sort_values(ascending=False)
        
        insights.append(f"📈 Bases com maior volume recente: **{', '.join(bases_crescimento.head(3).index)}**")
    
    return insights

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
        
        # Adiciona seção de insights
        st.write("## 🧠 Análise Inteligente")
        
        with st.spinner("Gerando insights..."):
            insights = analise_inteligente(dashboard.dados)
            
            # Mostra insights em cards
            cols = st.columns(2)
            for i, insight in enumerate(insights):
                with cols[i % 2]:
                    st.info(insight)
        
        # Adiciona análises comparativas
        st.write("## 📊 Análises Comparativas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de Eficiência
            dados_eficiencia = dashboard.dados.groupby('BASE').agg({
                'CONTRATO': 'count',
                'TECNICO': 'nunique'
            })
            dados_eficiencia['Eficiência'] = dados_eficiencia['CONTRATO'] / dados_eficiencia['TECNICO']
            
            media_geral = dados_eficiencia['Eficiência'].mean()
            
            import plotly.express as px
            fig = px.bar(
                dados_eficiencia.reset_index(),
                x='BASE',
                y='Eficiência',
                title='Eficiência por Base (Contratos/Técnico)'
            )
            
            # Adiciona linha da média
            fig.add_hline(
                y=media_geral,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Média: {media_geral:.1f}"
            )
            
            st.plotly_chart(fig)
        
        with col2:
            # Gráfico de Rentabilidade
            dados_rent = dashboard.dados.groupby('BASE').agg({
                'VALOR EMPRESA': 'sum',
                'TECNICO': 'nunique'
            })
            dados_rent['Rentabilidade'] = dados_rent['VALOR EMPRESA'] / dados_rent['TECNICO']
            
            fig = px.bar(
                dados_rent.reset_index(),
                x='BASE',
                y='Rentabilidade',
                title='Rentabilidade por Base (R$/Técnico)'
            )
            
            st.plotly_chart(fig)

if __name__ == "__main__":
    main() 