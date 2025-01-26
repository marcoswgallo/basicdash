import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app import DashboardTecnicos, load_css
from datetime import datetime, timedelta

def analisar_tempo_execucao(dados):
    st.subheader("⏱️ Análise de Tempo de Execução")
    
    # Converte tempo para minutos
    dados['TEMPO_EXECUCAO'] = pd.to_datetime(dados['HORA_FIM']) - pd.to_datetime(dados['HORA_INICIO'])
    dados['TEMPO_MINUTOS'] = dados['TEMPO_EXECUCAO'].dt.total_seconds() / 60
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tempo médio por tipo de serviço
        tempo_servico = dados.groupby('TIPO DE SERVIÇO').agg({
            'TEMPO_MINUTOS': ['mean', 'count']
        }).round(2)
        
        fig = px.bar(
            tempo_servico.reset_index(),
            x='TIPO DE SERVIÇO',
            y=('TEMPO_MINUTOS', 'mean'),
            title='Tempo Médio por Tipo de Serviço (minutos)',
            labels={'TEMPO_MINUTOS': 'Minutos', 'count': 'Quantidade'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribuição de tempo
        fig = px.histogram(
            dados,
            x='TEMPO_MINUTOS',
            title='Distribuição do Tempo de Execução',
            nbins=30
        )
        st.plotly_chart(fig, use_container_width=True)

def analisar_produtividade_regional(dados):
    st.subheader("🗺️ Análise Regional")
    
    prod_regional = dados.groupby(['CIDADE', 'BAIRRO']).agg({
        'CONTRATO': 'count',
        'VALOR EMPRESA': 'sum',
        'TECNICO': 'nunique'
    }).reset_index()
    
    prod_regional['CONTRATOS_POR_TECNICO'] = prod_regional['CONTRATO'] / prod_regional['TECNICO']
    prod_regional['VALOR_MEDIO_CONTRATO'] = prod_regional['VALOR EMPRESA'] / prod_regional['CONTRATO']
    
    # Mapa de calor por cidade/bairro
    fig = px.treemap(
        prod_regional,
        path=[px.Constant("Total"), 'CIDADE', 'BAIRRO'],
        values='CONTRATO',
        color='VALOR_MEDIO_CONTRATO',
        title='Distribuição de Contratos por Região',
        color_continuous_scale='RdYlBu'
    )
    st.plotly_chart(fig, use_container_width=True)

def analisar_tipo_residencia(dados):
    st.subheader("🏠 Análise por Tipo de Residência")
    
    tipo_residencia = dados.groupby('TIPO RESIDÊNCIA').agg({
        'CONTRATO': 'count',
        'VALOR EMPRESA': ['sum', 'mean'],
        'TEMPO_MINUTOS': 'mean'
    }).round(2)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza
        fig = px.pie(
            tipo_residencia.reset_index(),
            values=('CONTRATO', ''),
            names='TIPO RESIDÊNCIA',
            title='Distribuição por Tipo de Residência'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Comparativo de valores
        fig = px.bar(
            tipo_residencia.reset_index(),
            x='TIPO RESIDÊNCIA',
            y=('VALOR EMPRESA', 'mean'),
            title='Valor Médio por Tipo de Residência'
        )
        st.plotly_chart(fig, use_container_width=True)

def analisar_horarios(dados):
    st.subheader("🕒 Análise de Horários")
    
    dados['HORA_INICIO'] = pd.to_datetime(dados['HORA_INICIO']).dt.hour
    
    prod_horario = dados.groupby('HORA_INICIO').agg({
        'CONTRATO': 'count',
        'VALOR EMPRESA': 'sum',
        'STATUS': lambda x: (x == 'Executado').mean() * 100
    }).rename(columns={'STATUS': 'TAXA_SUCESSO'})
    
    # Gráfico de linha do tempo
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=prod_horario.index,
        y=prod_horario['CONTRATO'],
        name='Quantidade de Contratos',
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=prod_horario.index,
        y=prod_horario['TAXA_SUCESSO'],
        name='Taxa de Sucesso (%)',
        mode='lines+markers',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Produtividade por Hora do Dia',
        yaxis=dict(title='Quantidade de Contratos'),
        yaxis2=dict(title='Taxa de Sucesso (%)', overlaying='y', side='right')
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analisar_eficiencia_tecnicos(dados):
    st.subheader("👨‍🔧 Análise de Eficiência dos Técnicos")
    
    eficiencia = dados.groupby('TECNICO').agg({
        'CONTRATO': 'count',
        'VALOR EMPRESA': 'sum',
        'TEMPO_MINUTOS': 'mean',
        'STATUS': lambda x: (x == 'Executado').mean() * 100
    }).round(2)
    
    eficiencia['VALOR_POR_HORA'] = (eficiencia['VALOR EMPRESA'] / 
                                   (eficiencia['TEMPO_MINUTOS'].sum() / 60))
    
    # Ranking dos técnicos
    fig = px.scatter(
        eficiencia.reset_index(),
        x='CONTRATO',
        y='VALOR_POR_HORA',
        size='TEMPO_MINUTOS',
        color='STATUS',
        hover_data=['TECNICO'],
        title='Performance dos Técnicos'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def mostrar_kpis(dados):
    st.subheader("📊 KPIs Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        taxa_sucesso = (dados['STATUS'] == 'Executado').mean() * 100
        st.metric(
            "Taxa de Sucesso",
            f"{taxa_sucesso:.1f}%",
            help="Percentual de serviços executados com sucesso"
        )
        
    with col2:
        tempo_medio = dados['TEMPO_MINUTOS'].mean()
        st.metric(
            "Tempo Médio",
            f"{tempo_medio:.1f} min",
            help="Tempo médio de execução dos serviços"
        )
        
    with col3:
        valor_medio = dados['VALOR EMPRESA'].mean()
        st.metric(
            "Valor Médio",
            f"R$ {valor_medio:.2f}",
            help="Valor médio por serviço"
        )
        
    with col4:
        produtividade = dados.groupby('TECNICO')['CONTRATO'].count().mean()
        st.metric(
            "Contratos/Técnico",
            f"{produtividade:.1f}",
            help="Média de contratos por técnico"
        )

def main():
    st.set_page_config(page_title="Análise Avançada", layout="wide")
    
    st.title("📈 Análise Avançada")
    
    dashboard = DashboardTecnicos()
    arquivos = dashboard.listar_arquivos()
    
    if not arquivos:
        st.error("Nenhum arquivo encontrado")
        return
        
    arquivo = arquivos[0]
    
    if dashboard.carregar_dados(arquivo):
        dados = dashboard.dados.copy()
        
        # Filtros
        st.sidebar.title("Filtros")
        
        # Converte datas para datetime
        dados['DATA_TOA'] = pd.to_datetime(dados['DATA_TOA']).dt.date
        datas_disponiveis = sorted(dados['DATA_TOA'].unique())
        
        # Filtro de data
        data_min = st.sidebar.date_input(
            "Data Inicial",
            value=datas_disponiveis[0],
            min_value=min(datas_disponiveis),
            max_value=max(datas_disponiveis)
        )
        
        data_max = st.sidebar.date_input(
            "Data Final",
            value=datas_disponiveis[-1],
            min_value=min(datas_disponiveis),
            max_value=max(datas_disponiveis)
        )
        
        # Filtro de grupo/base
        grupo = st.sidebar.selectbox("Grupo", ['Todos'] + sorted(dados['GRUPO'].unique().tolist()))
        base = st.sidebar.selectbox("Base", ['Todas'] + sorted(dados['BASE'].unique().tolist()))
        
        # Aplica filtros
        mask = (dados['DATA_TOA'] >= data_min) & (dados['DATA_TOA'] <= data_max)
               
        if grupo != 'Todos':
            mask &= dados['GRUPO'] == grupo
            
        if base != 'Todas':
            mask &= dados['BASE'] == base
            
        dados_filtrados = dados[mask].copy()
        
        if len(dados_filtrados) == 0:
            st.warning("Nenhum dado encontrado para os filtros selecionados")
            return
            
        # Mostra análises
        mostrar_kpis(dados_filtrados)
        analisar_tempo_execucao(dados_filtrados)
        analisar_produtividade_regional(dados_filtrados)
        analisar_tipo_residencia(dados_filtrados)
        analisar_horarios(dados_filtrados)
        analisar_eficiencia_tecnicos(dados_filtrados)

if __name__ == "__main__":
    main() 