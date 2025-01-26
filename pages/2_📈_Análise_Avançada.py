import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app import DashboardTecnicos, load_css
from datetime import datetime, timedelta, date

def analisar_tempo_execucao(dados):
    st.subheader("⏱️ Análise de Tempo de Execução")
    
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

def preparar_dados(dados):
    """Prepara os dados para análise, criando colunas calculadas"""
    try:
        dados = dados.copy()
        
        # Verifica as colunas disponíveis
        st.write("Colunas disponíveis:", dados.columns.tolist())
        
        # Converte datas
        if 'DATA_TOA' in dados.columns:
            dados['DATA_TOA'] = pd.to_datetime(dados['DATA_TOA'])
        
        # Verifica se já temos a coluna TEMPO_MINUTOS
        if 'TEMPO_MINUTOS' not in dados.columns:
            st.warning("Coluna TEMPO_MINUTOS não encontrada. Usando valor padrão.")
            dados['TEMPO_MINUTOS'] = 60  # valor padrão de 1 hora
        
        # Garante que valores monetários sejam numéricos
        for col in ['VALOR TÉCNICO', 'VALOR EMPRESA']:
            if col in dados.columns:
                dados[col] = pd.to_numeric(dados[col].astype(str).str.replace('R$', '').str.replace(',', '.'), errors='coerce')
        
        return dados
    
    except Exception as e:
        st.error(f"Erro ao preparar dados: {str(e)}")
        st.error(f"Colunas disponíveis: {', '.join(dados.columns)}")
        raise e

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
    dados = None
    
    if dashboard.carregar_dados(arquivo):
        try:
            # Carrega e prepara os dados
            dados = preparar_dados(dashboard.dados)
            
            # Filtros
            st.sidebar.title("Filtros")
            
            # Converte datas para datetime se necessário
            if not pd.api.types.is_datetime64_any_dtype(dados['DATA_TOA']):
                dados['DATA_TOA'] = pd.to_datetime(dados['DATA_TOA'])
            
            data_min_default = dados['DATA_TOA'].min().date()
            data_max_default = dados['DATA_TOA'].max().date()
            
            # Filtro de data
            data_min = st.sidebar.date_input(
                "Data Inicial",
                value=data_min_default,
                min_value=data_min_default,
                max_value=data_max_default
            )
            
            data_max = st.sidebar.date_input(
                "Data Final",
                value=data_max_default,
                min_value=data_min_default,
                max_value=data_max_default
            )
            
            # Filtro de grupo/base
            grupos_disponiveis = ['Todos'] + sorted(dados['GRUPO'].unique().tolist())
            grupo = st.sidebar.selectbox("Grupo", grupos_disponiveis)
            
            # Filtra bases baseado no grupo selecionado
            if grupo != 'Todos':
                bases_filtradas = dados[dados['GRUPO'] == grupo]['BASE'].unique()
            else:
                bases_filtradas = dados['BASE'].unique()
            
            bases_disponiveis = ['Todas'] + sorted(bases_filtradas.tolist())
            base = st.sidebar.selectbox("Base", bases_disponiveis)
            
            # Aplica filtros
            mask = (dados['DATA_TOA'].dt.date >= data_min) & \
                   (dados['DATA_TOA'].dt.date <= data_max)
            
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
            
        except Exception as e:
            st.error(f"Erro ao processar os dados: {str(e)}")
            if dados is not None:
                st.error(f"Colunas disponíveis: {', '.join(dados.columns)}")
            st.error("Por favor, verifique o formato dos dados")

if __name__ == "__main__":
    main() 