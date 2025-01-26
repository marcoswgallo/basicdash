import streamlit as st
import pandas as pd
import numpy as np
from streamlit_app import DashboardTecnicos, load_css

def analise_inteligente(dados):
    """Gera insights automáticos dos dados"""
    insights = []
    
    # Verifica se a coluna GRUPO existe
    if 'GRUPO' in dados.columns:
        # Análise por Grupo
        prod_por_grupo = dados.groupby('GRUPO').agg({
            'CONTRATO': 'count',
            'TECNICO': 'nunique',
            'VALOR EMPRESA': 'sum'
        })
        
        # Produtividade por grupo
        prod_por_tecnico_grupo = prod_por_grupo['CONTRATO'] / prod_por_grupo['TECNICO']
        melhor_grupo = prod_por_tecnico_grupo.idxmax()
        
        insights.append(f"📊 O grupo mais produtivo é **{melhor_grupo}** com média de "
                       f"**{prod_por_tecnico_grupo[melhor_grupo]:.1f}** contratos por técnico")
        
        # Distribuição por grupo
        for grupo in prod_por_grupo.index:
            total_grupo = prod_por_grupo.loc[grupo, 'CONTRATO']
            perc_grupo = (total_grupo / dados['CONTRATO'].count()) * 100
            insights.append(f"📌 Grupo **{grupo}**: representa **{perc_grupo:.1f}%** dos contratos")
    
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
    
    load_css()
    
    st.title("📊 Resumo por Base")
    
    # Menu na sidebar (para manter consistência)
    with st.sidebar:
        st.title("🔧 Menu Principal")
    
    dashboard = DashboardTecnicos()
    arquivos = dashboard.listar_arquivos()
    
    if not arquivos:
        st.error("Nenhum arquivo encontrado na pasta Dados_excel")
        return
        
    arquivo = arquivos[0]
    
    if dashboard.carregar_dados(arquivo):
        if dashboard.dados is not None:
            # Adiciona filtros
            st.write("### Filtros")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                grupos_disponiveis = ['Todos'] + sorted(dashboard.dados['GRUPO'].unique().tolist())
                grupo_selecionado = st.selectbox(
                    "Selecione o Grupo:",
                    grupos_disponiveis,
                    key='grupo_selector_resumo'
                )
                
                # Filtra as bases baseado no grupo selecionado
                if grupo_selecionado != 'Todos':
                    bases_filtradas = dashboard.dados[dashboard.dados['GRUPO'] == grupo_selecionado]['BASE'].unique()
                else:
                    bases_filtradas = dashboard.dados['BASE'].unique()
                
                bases_disponiveis = ['Todas'] + sorted(bases_filtradas.tolist())
                base_selecionada = st.selectbox(
                    "Selecione a Base:",
                    bases_disponiveis,
                    key='base_selector_resumo'
                )
            
            with col2:
                status_disponiveis = sorted(dashboard.dados['STATUS'].dropna().unique().tolist())
                status_selecionados = st.multiselect(
                    "Selecione os Status:",
                    status_disponiveis,
                    default=status_disponiveis,
                    key='status_selector_resumo'
                )
            
            # Aplica os filtros
            dados_filtrados = dashboard.dados.copy()
            
            if grupo_selecionado != 'Todos':
                dados_filtrados = dados_filtrados[dados_filtrados['GRUPO'] == grupo_selecionado]
            
            if base_selecionada != 'Todas':
                dados_filtrados = dados_filtrados[dados_filtrados['BASE'] == base_selecionada]
            
            if status_selecionados:
                dados_filtrados = dados_filtrados[dados_filtrados['STATUS'].isin(status_selecionados)]
            
            # Mostra as tabelas com os dados filtrados
            dashboard.mostrar_tabela_bases(dados_filtrados)
            
            # Continua com as análises...
            with st.spinner("Gerando insights..."):
                try:
                    insights = analise_inteligente(dados_filtrados)
                    cols = st.columns(2)
                    for i, insight in enumerate(insights):
                        with cols[i % 2]:
                            st.info(insight)
                except Exception as e:
                    st.error(f"Erro ao gerar insights: {str(e)}")
        
        # Adiciona análises comparativas
        st.write("## 📊 Análises Comparativas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de Eficiência
            dados_eficiencia = dados_filtrados.groupby('BASE').agg({
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
            dados_rent = dados_filtrados.groupby('BASE').agg({
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