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
        
        # Reseta o índice e ajusta os nomes das colunas
        tempo_servico = tempo_servico.reset_index()
        tempo_servico.columns = ['TIPO DE SERVIÇO', 'TEMPO_MEDIO', 'QUANTIDADE']
        
        fig = px.bar(
            tempo_servico,
            x='TIPO DE SERVIÇO',
            y='TEMPO_MEDIO',
            title='Tempo Médio por Tipo de Serviço (minutos)',
            labels={
                'TIPO DE SERVIÇO': 'Tipo de Serviço',
                'TEMPO_MEDIO': 'Tempo Médio (min)',
            },
            text='QUANTIDADE'
        )
        
        fig.update_traces(
            texttemplate='%{text} serviços',
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribuição de tempo
        fig = px.histogram(
            dados,
            x='TEMPO_MINUTOS',
            title='Distribuição do Tempo de Execução',
            nbins=30,
            labels={
                'TEMPO_MINUTOS': 'Tempo (minutos)',
                'count': 'Quantidade'
            }
        )
        
        # Adiciona linha vertical com a média
        fig.add_vline(
            x=dados['TEMPO_MINUTOS'].mean(),
            line_dash="dash",
            line_color="red",
            annotation_text=f"Média: {dados['TEMPO_MINUTOS'].mean():.1f} min"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def analisar_produtividade_regional(dados):
    st.subheader("🗺️ Análise Regional por Base")
    
    # Agrupa por BASE
    prod_regional = dados.groupby('BASE').agg({
        'CONTRATO': 'count',
        'VALOR EMPRESA': 'sum',
        'TECNICO': 'nunique'
    }).reset_index()
    
    # Calcula métricas
    prod_regional['CONTRATOS_POR_TECNICO'] = (prod_regional['CONTRATO'] / 
                                             prod_regional['TECNICO']).round(2)
    prod_regional['VALOR_MEDIO_CONTRATO'] = (prod_regional['VALOR EMPRESA'] / 
                                            prod_regional['CONTRATO']).round(2)
    
    # Visualizações
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras para contratos por técnico
        fig = px.bar(
            prod_regional,
            x='BASE',
            y='CONTRATOS_POR_TECNICO',
            title='Produtividade por Base',
            labels={
                'BASE': 'Base',
                'CONTRATOS_POR_TECNICO': 'Contratos por Técnico'
            },
            text='CONTRATOS_POR_TECNICO'
        )
        
        fig.update_traces(
            texttemplate='%{text:.1f}',
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de pizza para distribuição de valor
        fig = px.pie(
            prod_regional,
            values='VALOR EMPRESA',
            names='BASE',
            title='Distribuição de Valor por Base',
            hover_data=['CONTRATOS_POR_TECNICO', 'VALOR_MEDIO_CONTRATO']
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela resumo
    st.write("### Resumo por Base")
    
    # Formata a tabela
    tabela_resumo = prod_regional.copy()
    tabela_resumo['VALOR EMPRESA'] = tabela_resumo['VALOR EMPRESA'].apply(lambda x: f"R$ {x:,.2f}")
    tabela_resumo['VALOR_MEDIO_CONTRATO'] = tabela_resumo['VALOR_MEDIO_CONTRATO'].apply(lambda x: f"R$ {x:,.2f}")
    
    tabela_resumo.columns = [
        'Base',
        'Total Contratos',
        'Valor Total',
        'Total Técnicos',
        'Contratos/Técnico',
        'Valor Médio/Contrato'
    ]
    
    st.dataframe(
        tabela_resumo,
        use_container_width=True,
        hide_index=True
    )

def analisar_tipo_servico(dados):
    st.subheader("🔧 Análise por Tipo de Serviço")
    
    tipo_servico = dados.groupby('TIPO DE SERVIÇO').agg({
        'CONTRATO': 'count',
        'VALOR EMPRESA': ['sum', 'mean'],
        'TEMPO_MINUTOS': 'mean'
    }).round(2)
    
    # Reseta o índice e ajusta os nomes das colunas
    tipo_servico = tipo_servico.reset_index()
    tipo_servico.columns = [
        'TIPO DE SERVIÇO',
        'TOTAL_CONTRATOS',
        'VALOR_TOTAL',
        'VALOR_MEDIO',
        'TEMPO_MEDIO'
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza para distribuição de contratos
        fig = px.pie(
            tipo_servico,
            values='TOTAL_CONTRATOS',
            names='TIPO DE SERVIÇO',
            title='Distribuição por Tipo de Serviço',
            hover_data=['VALOR_MEDIO']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de barras para valor médio
        fig = px.bar(
            tipo_servico,
            x='TIPO DE SERVIÇO',
            y='VALOR_MEDIO',
            title='Valor Médio por Tipo de Serviço',
            text='TOTAL_CONTRATOS'
        )
        
        fig.update_traces(
            texttemplate='%{text} contratos',
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela resumo
    st.write("### Resumo por Tipo de Serviço")
    
    # Formata a tabela
    tabela_resumo = tipo_servico.copy()
    tabela_resumo['VALOR_TOTAL'] = tabela_resumo['VALOR_TOTAL'].apply(lambda x: f"R$ {x:,.2f}")
    tabela_resumo['VALOR_MEDIO'] = tabela_resumo['VALOR_MEDIO'].apply(lambda x: f"R$ {x:,.2f}")
    tabela_resumo['TEMPO_MEDIO'] = tabela_resumo['TEMPO_MEDIO'].apply(lambda x: f"{x:.1f} min")
    
    tabela_resumo.columns = [
        'Tipo de Serviço',
        'Total Contratos',
        'Valor Total',
        'Valor Médio',
        'Tempo Médio'
    ]
    
    st.dataframe(
        tabela_resumo,
        use_container_width=True,
        hide_index=True
    )

def analisar_horarios(dados):
    st.subheader("🕒 Análise por Período")
    
    # Usa a hora da DATA_TOA
    dados['HORA'] = dados['DATA_TOA'].dt.hour
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Análise por hora do dia
        prod_horario = dados.groupby('HORA').agg({
            'CONTRATO': 'count',
            'VALOR EMPRESA': 'sum',
            'STATUS': lambda x: (x == 'Executado').mean() * 100
        }).reset_index()
        
        fig = px.bar(
            prod_horario,
            x='HORA',
            y='CONTRATO',
            title='Distribuição de Serviços por Hora',
            labels={
                'HORA': 'Hora do Dia',
                'CONTRATO': 'Quantidade de Serviços'
            },
            text='CONTRATO'
        )
        
        fig.update_traces(
            texttemplate='%{text}',
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Análise por dia da semana
        prod_dia = dados.groupby('DIA_SEMANA').agg({
            'CONTRATO': 'count',
            'VALOR EMPRESA': 'mean',
            'STATUS': lambda x: (x == 'Executado').mean() * 100
        }).reset_index()
        
        # Ordena os dias da semana
        ordem_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        prod_dia['DIA_SEMANA'] = pd.Categorical(prod_dia['DIA_SEMANA'], categories=ordem_dias, ordered=True)
        prod_dia = prod_dia.sort_values('DIA_SEMANA')
        
        fig = px.bar(
            prod_dia,
            x='DIA_SEMANA',
            y='CONTRATO',
            title='Distribuição de Serviços por Dia da Semana',
            labels={
                'DIA_SEMANA': 'Dia da Semana',
                'CONTRATO': 'Quantidade de Serviços'
            },
            text='CONTRATO'
        )
        
        fig.update_traces(
            texttemplate='%{text}',
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela resumo
    st.write("### Resumo por Período")
    
    # Prepara dados para a tabela
    tabela_resumo = prod_horario.copy()
    tabela_resumo['VALOR EMPRESA'] = tabela_resumo['VALOR EMPRESA'].apply(lambda x: f"R$ {x:,.2f}")
    tabela_resumo['STATUS'] = tabela_resumo['STATUS'].apply(lambda x: f"{x:.1f}%")
    
    tabela_resumo.columns = [
        'Hora',
        'Total Serviços',
        'Valor Total',
        'Taxa de Sucesso'
    ]
    
    st.dataframe(
        tabela_resumo,
        use_container_width=True,
        hide_index=True
    )

def analisar_eficiencia_tecnicos(dados):
    st.subheader("👨‍🔧 Análise de Eficiência dos Técnicos")
    
    # Calcula métricas por técnico
    eficiencia = dados.groupby('TECNICO').agg({
        'CONTRATO': 'count',
        'VALOR EMPRESA': ['sum', 'mean'],
        'TEMPO_MINUTOS': 'mean',
        'STATUS': lambda x: (x == 'Executado').mean() * 100
    }).round(2)
    
    # Ajusta os nomes das colunas
    eficiencia.columns = [
        'TOTAL_CONTRATOS',
        'VALOR_TOTAL',
        'VALOR_MEDIO',
        'TEMPO_MEDIO',
        'TAXA_SUCESSO'
    ]
    eficiencia = eficiencia.reset_index()
    
    # Calcula produtividade
    eficiencia['PRODUTIVIDADE'] = (eficiencia['TOTAL_CONTRATOS'] * 
                                  eficiencia['TAXA_SUCESSO'] / 100).round(2)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras para total de contratos
        fig = px.bar(
            eficiencia.sort_values('TOTAL_CONTRATOS', ascending=True).tail(10),
            x='TOTAL_CONTRATOS',
            y='TECNICO',
            orientation='h',
            title='Top 10 Técnicos por Volume',
            labels={
                'TOTAL_CONTRATOS': 'Total de Contratos',
                'TECNICO': 'Técnico'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de barras para taxa de sucesso
        fig = px.bar(
            eficiencia.sort_values('TAXA_SUCESSO', ascending=True).tail(10),
            x='TAXA_SUCESSO',
            y='TECNICO',
            orientation='h',
            title='Top 10 Técnicos por Taxa de Sucesso',
            labels={
                'TAXA_SUCESSO': 'Taxa de Sucesso (%)',
                'TECNICO': 'Técnico'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela resumo
    st.write("### Resumo por Técnico")
    
    # Formata a tabela
    tabela_resumo = eficiencia.copy()
    tabela_resumo['VALOR_TOTAL'] = tabela_resumo['VALOR_TOTAL'].apply(lambda x: f"R$ {x:,.2f}")
    tabela_resumo['VALOR_MEDIO'] = tabela_resumo['VALOR_MEDIO'].apply(lambda x: f"R$ {x:,.2f}")
    tabela_resumo['TAXA_SUCESSO'] = tabela_resumo['TAXA_SUCESSO'].apply(lambda x: f"{x:.1f}%")
    tabela_resumo['TEMPO_MEDIO'] = tabela_resumo['TEMPO_MEDIO'].apply(lambda x: f"{x:.1f} min")
    
    tabela_resumo.columns = [
        'Técnico',
        'Total Contratos',
        'Valor Total',
        'Valor Médio',
        'Tempo Médio',
        'Taxa de Sucesso',
        'Produtividade'
    ]
    
    st.dataframe(
        tabela_resumo.sort_values('Total Contratos', ascending=False),
        use_container_width=True,
        hide_index=True
    )

def preparar_dados(dados):
    """Prepara os dados para análise, criando colunas calculadas"""
    try:
        dados = dados.copy()
        
        # Converte datas
        if 'DATA_TOA' in dados.columns:
            dados['DATA_TOA'] = pd.to_datetime(dados['DATA_TOA'])
        
        # Garante que valores monetários sejam numéricos
        for col in ['VALOR TÉCNICO', 'VALOR EMPRESA']:
            if col in dados.columns:
                dados[col] = pd.to_numeric(
                    dados[col].astype(str)
                    .str.replace('R$', '')
                    .str.replace('.', '')
                    .str.replace(',', '.'),
                    errors='coerce'
                )
        
        # Calcula métricas adicionais
        if 'TEMPO_MINUTOS' not in dados.columns:
            # Calcula tempo médio por tipo de serviço
            tempo_medio_servico = {
                'ADESAO DE ASSINATURA': 90,
                'MUDANCA DE ENDERECO': 120,
                'VISITA TECNICA': 60,
                'SERVICOS': 45,
                'MUDANCA DE PACOTE': 30
            }
            
            # Aplica tempo médio baseado no tipo de serviço
            dados['TEMPO_MINUTOS'] = dados['TIPO DE SERVIÇO'].map(
                lambda x: tempo_medio_servico.get(x, 60)
            )
            
            st.info("Usando tempos médios estimados por tipo de serviço")
        
        # Adiciona outras métricas úteis
        dados['VALOR_POR_MINUTO'] = dados['VALOR EMPRESA'] / dados['TEMPO_MINUTOS']
        dados['MES'] = dados['DATA_TOA'].dt.month
        dados['DIA_SEMANA'] = dados['DATA_TOA'].dt.day_name()
        
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
            analisar_tipo_servico(dados_filtrados)
            analisar_horarios(dados_filtrados)
            analisar_eficiencia_tecnicos(dados_filtrados)
            
        except Exception as e:
            st.error(f"Erro ao processar os dados: {str(e)}")
            if dados is not None:
                st.error(f"Colunas disponíveis: {', '.join(dados.columns)}")
            st.error("Por favor, verifique o formato dos dados")

if __name__ == "__main__":
    main() 