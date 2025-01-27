import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_app import DashboardTecnicos
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from prophet import Prophet
from datetime import timedelta

def prever_demanda(dados):
    """Prevê a demanda futura de serviços usando séries temporais"""
    st.subheader("🔮 Previsão de Demanda")
    
    try:
        # Agrupa por data e conta serviços
        demanda_diaria = dados.groupby('DATA_TOA')['CONTRATO'].count().reset_index()
        
        # Prepara dados para o Prophet
        df_prophet = demanda_diaria.rename(columns={'DATA_TOA': 'ds', 'CONTRATO': 'y'})
        
        with st.spinner('Treinando modelo de previsão...'):
            # Treina modelo
            model = Prophet(daily_seasonality=True)
            model.fit(df_prophet)
            
            # Faz previsão para próximos 30 dias
            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)
        
        # Plota resultados
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de previsão
            fig = px.line(
                forecast, 
                x='ds', 
                y=['yhat', 'yhat_lower', 'yhat_upper'],
                title='Previsão de Demanda - Próximos 30 dias',
                labels={
                    'ds': 'Data',
                    'yhat': 'Previsão',
                    'yhat_lower': 'Limite Inferior',
                    'yhat_upper': 'Limite Superior'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Componentes da previsão
            fig = model.plot_components(forecast)
            st.pyplot(fig)
        
        # Métricas de previsão
        st.write("### Métricas de Previsão")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            media_atual = df_prophet['y'].mean()
            media_prevista = forecast['yhat'].tail(30).mean()
            variacao = ((media_prevista - media_atual) / media_atual) * 100
            
            st.metric(
                "Média Diária Prevista",
                f"{media_prevista:.1f}",
                f"{variacao:+.1f}%"
            )
        
        with col2:
            st.metric(
                "Pico Previsto",
                f"{forecast['yhat'].max():.1f}",
                f"Data: {forecast.loc[forecast['yhat'].idxmax(), 'ds'].strftime('%d/%m/%Y')}"
            )
        
        with col3:
            st.metric(
                "Vale Previsto",
                f"{forecast['yhat'].min():.1f}",
                f"Data: {forecast.loc[forecast['yhat'].idxmin(), 'ds'].strftime('%d/%m/%Y')}"
            )
            
    except Exception as e:
        st.error(f"Erro ao gerar previsão: {str(e)}")

def analisar_clusters_tecnicos(dados):
    """Agrupa técnicos em clusters por performance"""
    st.subheader("🎯 Análise de Clusters de Performance")
    
    try:
        # Prepara dados dos técnicos
        metricas_tecnicos = dados.groupby('TECNICO').agg({
            'CONTRATO': 'count',
            'VALOR EMPRESA': 'mean',
            'TEMPO_MINUTOS': 'mean',
            'STATUS': lambda x: (x == 'Executado').mean() * 100
        }).reset_index()
        
        # Seleciona features para clustering
        features = ['CONTRATO', 'VALOR EMPRESA', 'TEMPO_MINUTOS', 'STATUS']
        X = metricas_tecnicos[features].values
        
        # Normaliza dados
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determina número ideal de clusters
        inertias = []
        K = range(1, 10)
        for k in K:
            kmeans = KMeans(n_clusters=k)
            kmeans.fit(X_scaled)
            inertias.append(kmeans.inertia_)
        
        # Aplica K-means com número ideal de clusters
        n_clusters = 3  # Pode ser ajustado baseado no elbow plot
        kmeans = KMeans(n_clusters=n_clusters)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Adiciona clusters ao dataframe
        metricas_tecnicos['CLUSTER'] = clusters
        
        # Visualizações
        col1, col2 = st.columns(2)
        
        with col1:
            # Scatter plot 3D
            fig = px.scatter_3d(
                metricas_tecnicos,
                x='CONTRATO',
                y='VALOR EMPRESA',
                z='TEMPO_MINUTOS',
                color='CLUSTER',
                hover_data=['TECNICO'],
                title='Clusters de Técnicos - Visualização 3D'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Características dos clusters
            for i in range(n_clusters):
                st.write(f"### Cluster {i}")
                cluster_data = metricas_tecnicos[metricas_tecnicos['CLUSTER'] == i]
                
                st.write(f"Quantidade de técnicos: {len(cluster_data)}")
                st.write(f"Média de contratos: {cluster_data['CONTRATO'].mean():.1f}")
                st.write(f"Taxa média de sucesso: {cluster_data['STATUS'].mean():.1f}%")
                
        # Lista técnicos por cluster
        st.write("### Detalhamento dos Clusters")
        for i in range(n_clusters):
            with st.expander(f"Cluster {i}"):
                cluster_data = metricas_tecnicos[metricas_tecnicos['CLUSTER'] == i]
                st.dataframe(cluster_data)
                
    except Exception as e:
        st.error(f"Erro na análise de clusters: {str(e)}")

def detectar_anomalias(dados):
    """Detecta serviços com padrões anômalos"""
    st.subheader("🔍 Detecção de Anomalias")
    
    try:
        # Prepara features para detecção
        features = ['TEMPO_MINUTOS', 'VALOR EMPRESA']
        X = dados[features].values
        
        # Treina modelo
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomalias = iso_forest.fit_predict(X)
        
        # Adiciona resultado ao dataframe
        dados_anomalias = dados.copy()
        dados_anomalias['ANOMALIA'] = anomalias
        
        # Visualizações
        col1, col2 = st.columns(2)
        
        with col1:
            # Scatter plot de anomalias
            fig = px.scatter(
                dados_anomalias,
                x='TEMPO_MINUTOS',
                y='VALOR EMPRESA',
                color='ANOMALIA',
                title='Detecção de Serviços Anômalos',
                labels={
                    'TEMPO_MINUTOS': 'Tempo (minutos)',
                    'VALOR EMPRESA': 'Valor (R$)',
                    'ANOMALIA': 'Normal / Anômalo'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Estatísticas das anomalias
            total_anomalias = (anomalias == -1).sum()
            taxa_anomalias = (total_anomalias / len(anomalias)) * 100
            
            st.metric("Total de Anomalias", total_anomalias)
            st.metric("Taxa de Anomalias", f"{taxa_anomalias:.1f}%")
            
        # Detalhamento das anomalias
        st.write("### Serviços Anômalos Detectados")
        anomalos = dados_anomalias[dados_anomalias['ANOMALIA'] == -1]
        st.dataframe(anomalos)
        
    except Exception as e:
        st.error(f"Erro na detecção de anomalias: {str(e)}")

def gerar_recomendacoes(dados):
    """Gera recomendações baseadas em padrões identificados"""
    st.subheader("💡 Recomendações Inteligentes")
    
    try:
        # Análise de padrões de sucesso
        dados_sucesso = dados[dados['STATUS'] == 'Executado']
        
        # Melhores horários
        melhores_horarios = dados_sucesso.groupby('HORA')['CONTRATO'].count()
        pior_horario = melhores_horarios.idxmin()
        melhor_horario = melhores_horarios.idxmax()
        
        # Melhores técnicos
        melhores_tecnicos = dados_sucesso.groupby('TECNICO').agg({
            'CONTRATO': 'count',
            'VALOR EMPRESA': 'mean',
            'TEMPO_MINUTOS': 'mean'
        }).sort_values('CONTRATO', ascending=False)
        
        # Visualizações
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Melhores Horários")
            fig = px.bar(
                melhores_horarios,
                title='Distribuição de Sucesso por Hora',
                labels={'value': 'Quantidade de Serviços'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.write("### Melhores Técnicos")
            fig = px.bar(
                melhores_tecnicos.head(10),
                y='CONTRATO',
                title='Top 10 Técnicos mais Produtivos'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recomendações
        st.write("### Recomendações Baseadas em Dados")
        
        with st.expander("📊 Distribuição de Serviços"):
            st.write(f"- Melhor horário para serviços: {melhor_horario}h")
            st.write(f"- Horário a evitar: {pior_horario}h")
            st.write(f"- Taxa de sucesso no melhor horário: {(melhores_horarios.max()/melhores_horarios.sum()*100):.1f}%")
        
        with st.expander("👨‍🔧 Alocação de Técnicos"):
            st.write("Top 3 técnicos mais eficientes:")
            for i, (tecnico, dados) in enumerate(melhores_tecnicos.head(3).iterrows(), 1):
                st.write(f"{i}. {tecnico}")
                st.write(f"   - Serviços realizados: {dados['CONTRATO']:.0f}")
                st.write(f"   - Tempo médio: {dados['TEMPO_MINUTOS']:.1f} min")
                st.write(f"   - Valor médio: R$ {dados['VALOR EMPRESA']:.2f}")
        
    except Exception as e:
        st.error(f"Erro ao gerar recomendações: {str(e)}")

def main():
    st.set_page_config(page_title="Análise IA", layout="wide")
    
    st.title("🤖 Análise com Inteligência Artificial")
    
    dashboard = DashboardTecnicos()
    arquivos = dashboard.listar_arquivos()
    
    if not arquivos:
        st.error("Nenhum arquivo encontrado")
        return
        
    arquivo = arquivos[0]
    
    if dashboard.carregar_dados(arquivo):
        try:
            dados = dashboard.dados.copy()
            
            # Converte datas
            dados['DATA_TOA'] = pd.to_datetime(dados['DATA_TOA'])
            
            # Adiciona coluna de hora
            dados['HORA'] = dados['DATA_TOA'].dt.hour
            
            # Menu de análises
            analise = st.sidebar.selectbox(
                "Escolha a Análise",
                ["Previsão de Demanda", 
                 "Clusters de Performance",
                 "Detecção de Anomalias",
                 "Recomendações"]
            )
            
            if analise == "Previsão de Demanda":
                prever_demanda(dados)
            elif analise == "Clusters de Performance":
                analisar_clusters_tecnicos(dados)
            elif analise == "Detecção de Anomalias":
                detectar_anomalias(dados)
            else:
                gerar_recomendacoes(dados)
                
        except Exception as e:
            st.error(f"Erro ao processar dados: {str(e)}")
            st.error(f"Colunas disponíveis: {', '.join(dados.columns)}")

if __name__ == "__main__":
    main() 