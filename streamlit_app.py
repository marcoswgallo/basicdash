import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import gc

class DashboardTecnicos:
    def __init__(self):
        self.dados = None
        self.pasta_dados = "Dados_excel"
        self.cached_file = None
        
        # Colunas que realmente vamos usar
        self.colunas_necessarias = [
            'TECNICO', 'DATA_TOA', 'CONTRATO', 'STATUS', 
            'TIPO DE SERVIÇO', 'VALOR TÉCNICO', 'VALOR EMPRESA', 'BASE'
        ]
        
        # Otimização: Definir tipos de dados específicos para cada coluna
        self.dtypes = {
            'TECNICO': 'category',        # Para strings que se repetem
            'BASE': 'category',
            'STATUS': 'category',
            'TIPO DE SERVIÇO': 'category',
            'CONTRATO': 'category',
            'VALOR TÉCNICO': 'float32',   # Reduz precisão para economizar memória
            'VALOR EMPRESA': 'float32'
        }
        
    def listar_arquivos(self):
        """
        Lista todos os arquivos Excel e CSV na pasta Dados_excel
        """
        try:
            arquivos = [f for f in os.listdir(self.pasta_dados) 
                       if f.endswith(('.xlsx', '.csv'))]
            return arquivos
        except Exception as e:
            st.error(f"Erro ao listar arquivos: {e}")
            return []
        
    @st.cache_data  # Cache do Streamlit para dados
    def carregar_dados_cache(_self, nome_arquivo, colunas):
        """
        Carrega apenas as colunas necessárias do arquivo com cache
        """
        caminho_completo = os.path.join(_self.pasta_dados, nome_arquivo)
        if nome_arquivo.endswith('.csv'):
            return pd.read_csv(caminho_completo, usecols=colunas)
        elif nome_arquivo.endswith('.xlsx'):
            return pd.read_excel(caminho_completo, usecols=colunas)

    # Alternativa: podemos também tornar o método estático
    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)
    def carregar_dados_cache_alt(pasta_dados, nome_arquivo, colunas, dtypes):
        """
        Versão otimizada do carregamento de dados
        """
        caminho_completo = os.path.join(pasta_dados, nome_arquivo)
        
        # Primeiro carrega sem definir dtypes
        if nome_arquivo.endswith('.xlsx'):
            df = pd.read_excel(
                caminho_completo,
                usecols=colunas,
                engine='openpyxl'
            )
        elif nome_arquivo.endswith('.csv'):
            df = pd.read_csv(
                caminho_completo,
                usecols=colunas,
                low_memory=False
            )
            
        # Trata as colunas de valor antes de converter os tipos
        for coluna in ['VALOR TÉCNICO', 'VALOR EMPRESA']:
            if coluna in df.columns:
                df[coluna] = (pd.to_numeric(
                    df[coluna]
                    .astype(str)
                    .str.replace('R$', '')
                    .str.replace('.', '')
                    .str.replace(',', '.')
                    .str.strip(),
                    errors='coerce'
                ).fillna(0))
        
        # Trata a coluna BASE antes de converter para category
        if 'BASE' in df.columns:
            df['BASE'] = df['BASE'].fillna('Não Informado').str.strip()
            
        # Agora converte os tipos de forma segura
        for coluna, tipo in dtypes.items():
            if coluna in df.columns:
                try:
                    if tipo == 'category':
                        # Para colunas categoria, garantimos que não há valores vazios
                        df[coluna] = df[coluna].fillna('Não Informado')
                    df[coluna] = df[coluna].astype(tipo)
                except Exception as e:
                    print(f"Erro ao converter coluna {coluna}: {e}")
        
        return df

    def carregar_dados(self, nome_arquivo):
        """
        Carrega e processa os dados de forma otimizada
        """
        try:
            if self.cached_file == nome_arquivo and self.dados is not None:
                return True
                
            # Carrega dados com otimizações
            self.dados = self.carregar_dados_cache_alt(
                self.pasta_dados, 
                nome_arquivo, 
                self.colunas_necessarias,
                self.dtypes
            )
            self.cached_file = nome_arquivo
            
            # Otimiza processamento de datas
            if 'DATA_TOA' in self.dados.columns:
                self.dados['DATA_TOA'] = pd.to_datetime(self.dados['DATA_TOA'], errors='coerce')
            
            # Otimiza memória
            self.dados = self.dados.copy()
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
            return False
            
    def mostrar_dados_basicos(self):
        """
        Mostra apenas informações básicas sem expor os dados
        """
        if self.dados is not None:
            total_registros = len(self.dados)
            total_tecnicos = self.dados['TECNICO'].nunique()
            total_bases = self.dados['BASE'].nunique()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Registros", f"{total_registros:,}")
            with col2:
                st.metric("Total de Técnicos", total_tecnicos)
            with col3:
                st.metric("Total de Bases", total_bases)

    def analisar_produtividade(self):
        """
        Análise de produtividade dos técnicos
        """
        if self.dados is not None:
            try:
                # Verifica se há datas válidas
                datas_validas = self.dados['DATA_TOA'].dropna()
                if len(datas_validas) == 0:
                    st.error("Não foi possível processar as datas no arquivo")
                    return
                
                data_min = datas_validas.min()
                data_max = datas_validas.max()
                
                # Cria uma linha para os filtros
                st.write("### Filtros")
                col1, col2 = st.columns(2)
                
                # Filtro de BASE
                with col1:
                    if 'BASE' in self.dados.columns:
                        bases_disponiveis = ['Todas'] + sorted(
                            self.dados['BASE']
                            .replace('', 'Não Informado')
                            .unique()
                            .tolist()
                        )
                        base_selecionada = st.selectbox(
                            "Selecione a Base:",
                            bases_disponiveis,
                            key='base_selector'
                        )
                    else:
                        st.error(f"Coluna BASE não encontrada no arquivo")
                        return
                
                # Filtro de STATUS
                with col2:
                    if 'STATUS' in self.dados.columns:
                        status_disponiveis = sorted(self.dados['STATUS'].dropna().unique().tolist())
                        status_selecionados = st.multiselect(
                            "Selecione os Status:",
                            status_disponiveis,
                            default=status_disponiveis  # Começa com todos selecionados
                        )
                    else:
                        st.error(f"Coluna STATUS não encontrada no arquivo")
                        return
                
                # Aplica os filtros
                # 1. Filtro de período
                mask_periodo = (self.dados['DATA_TOA'] >= data_min) & \
                             (self.dados['DATA_TOA'] <= data_max)
                
                # 2. Filtro de BASE
                if base_selecionada != 'Todas':
                    mask_base = (self.dados['BASE'].fillna('Não Informado') == base_selecionada)
                else:
                    mask_base = pd.Series(True, index=self.dados.index)
                
                # 3. Filtro de STATUS
                if status_selecionados:
                    mask_status = self.dados['STATUS'].isin(status_selecionados)
                else:
                    st.warning("Por favor, selecione pelo menos um status")
                    return
                
                # Aplica todos os filtros
                dados_filtrados = self.dados[mask_periodo & mask_base & mask_status]
                
                if len(dados_filtrados) == 0:
                    st.warning("Nenhum dado encontrado para os filtros selecionados")
                    return
                
                # Mostra quantidade de registros após filtros
                st.info(f"Mostrando {len(dados_filtrados):,} registros que atendem aos filtros selecionados")
                
                # Adiciona métricas por base
                st.write("### Métricas por Base")
                metricas_base = dados_filtrados.groupby('BASE').agg({
                    'TECNICO': 'nunique',
                    'CONTRATO': 'nunique',
                    'VALOR TÉCNICO': 'sum',
                    'VALOR EMPRESA': 'sum'
                }).reset_index()
                
                metricas_base.columns = ['Base', 'Total Técnicos', 'Total Contratos', 'Valor Técnicos', 'Valor Empresa']
                st.dataframe(metricas_base.style.format({
                    'Valor Técnicos': 'R$ {:,.2f}',
                    'Valor Empresa': 'R$ {:,.2f}'
                }))
                
                # Métricas gerais
                total_tecnicos = dados_filtrados['TECNICO'].nunique()
                total_contratos = dados_filtrados['CONTRATO'].nunique()
                total_valor_tecnico = dados_filtrados['VALOR TÉCNICO'].sum()
                total_valor_empresa = dados_filtrados['VALOR EMPRESA'].sum()
                
                # Cards com métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total de Técnicos", total_tecnicos)
                with col2:
                    st.metric("Total de Contratos", total_contratos)
                with col3:
                    st.metric("Valor Total Técnicos", f"R$ {total_valor_tecnico:,.2f}")
                with col4:
                    st.metric("Valor Total Empresa", f"R$ {total_valor_empresa:,.2f}")
                
                # Produtividade por técnico
                if base_selecionada != 'Todas':
                    # Filtra apenas os técnicos da base selecionada
                    tecnicos_da_base = dados_filtrados[dados_filtrados['BASE'] == base_selecionada]
                    
                    # Verifica se há dados para a base selecionada
                    if len(tecnicos_da_base) == 0:
                        st.warning(f"Nenhum dado encontrado para a base {base_selecionada}")
                        return
                    
                    # Agrupa por técnico apenas os dados da base selecionada
                    prod_tecnico = (tecnicos_da_base
                        .groupby('TECNICO')
                        .agg({
                            'CONTRATO': 'nunique',
                            'VALOR TÉCNICO': 'sum',
                            'VALOR EMPRESA': 'sum'
                        })
                        .reset_index()
                        .sort_values('CONTRATO', ascending=False)  # Ordena por contratos
                    )
                    
                    prod_tecnico.columns = ['Técnico', 'Contratos', 'Valor Técnico', 'Valor Empresa']
                    
                    # Gráfico de contratos por técnico
                    st.write(f"### Contratos por Técnico - {base_selecionada}")
                    
                    # Remove técnicos com 0 contratos
                    prod_tecnico = prod_tecnico[prod_tecnico['Contratos'] > 0]
                    
                    fig = px.bar(prod_tecnico, 
                               x='Contratos',
                               y='Técnico',
                               title=f'Contratos Executados por Técnico - {base_selecionada}',
                               height=max(600, len(prod_tecnico) * 25),  # Altura dinâmica
                               orientation='h'  # Barras horizontais
                    )
                    
                    fig.update_layout(
                        showlegend=False,
                        xaxis_title="Quantidade de Contratos",
                        yaxis_title="Técnico",
                        yaxis={'categoryorder':'total descending'},  # Ordena do maior para o menor
                        margin=dict(l=250, r=50)  # Margem para nomes longos
                    )
                    
                    # Adiciona rótulos nas barras
                    fig.update_traces(
                        texttemplate='%{x}',
                        textposition='outside',
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Análise por tipo de serviço
                st.write("### Análise por Tipo de Serviço")
                
                # Se uma base específica foi selecionada, mostra apenas dados dela
                if base_selecionada != 'Todas':
                    servicos_analise = dados_filtrados.groupby([
                        'TIPO DE SERVIÇO'
                    ])['CONTRATO'].nunique().reset_index()
                    
                    # Ordena por quantidade de contratos
                    servicos_analise = servicos_analise.sort_values('CONTRATO', ascending=False)
                    
                    fig = px.bar(servicos_analise, 
                                x='CONTRATO',
                                y='TIPO DE SERVIÇO',
                                title=f'Contratos por Tipo de Serviço - {base_selecionada}',
                                height=max(400, len(servicos_analise) * 30),
                                orientation='h')
                else:
                    # Se "Todas" as bases, mantém a visualização por base
                    servicos_analise = dados_filtrados.groupby([
                        'BASE',
                        'TIPO DE SERVIÇO'
                    ])['CONTRATO'].nunique().reset_index()
                    
                    # Ordena por quantidade de contratos
                    servicos_analise = servicos_analise.sort_values(['BASE', 'CONTRATO'], ascending=[True, False])
                    
                    fig = px.bar(servicos_analise, 
                                y='BASE',
                                x='CONTRATO',
                                color='TIPO DE SERVIÇO',
                                title='Contratos por Tipo de Serviço e Base',
                                height=max(400, len(servicos_analise['BASE'].unique()) * 50),
                                barmode='group')
                
                fig.update_layout(
                    showlegend=True,
                    xaxis_title="Quantidade de Contratos",
                    yaxis_title="Tipo de Serviço" if base_selecionada != 'Todas' else "Base",
                    yaxis={'categoryorder':'total ascending'},
                    legend_title="Tipo de Serviço"
                )
                
                # Adiciona rótulos nas barras se for base específica
                if base_selecionada != 'Todas':
                    fig.update_traces(
                        texttemplate='%{x}',
                        textposition='outside',
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Valores por Base
                st.write("### Valores")
                
                if base_selecionada != 'Todas':
                    # Para base específica, mostra apenas o total
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Valor Total Técnicos", f"R$ {dados_filtrados['VALOR TÉCNICO'].sum():,.2f}")
                    with col2:
                        st.metric("Valor Total Empresa", f"R$ {dados_filtrados['VALOR EMPRESA'].sum():,.2f}")
                else:
                    # Para todas as bases, mostra o gráfico por base
                    valores_base = dados_filtrados.groupby('BASE').agg({
                        'VALOR TÉCNICO': 'sum',
                        'VALOR EMPRESA': 'sum'
                    }).reset_index()
                    
                    fig = px.bar(valores_base,
                               y='BASE',
                               x=['VALOR TÉCNICO', 'VALOR EMPRESA'],
                               title='Valores por Base',
                               height=max(400, len(valores_base) * 50),
                               barmode='group')
                    
                    fig.update_layout(
                        showlegend=True,
                        xaxis_title="Valor (R$)",
                        yaxis_title="Base",
                        yaxis={'categoryorder':'total ascending'},
                        xaxis=dict(tickformat="R$ ,.2f")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Erro na análise: {str(e)}")
                st.error("Detalhes dos dados:")
                st.write("Colunas disponíveis:", list(self.dados.columns))
                st.write("Amostra da coluna de valor:", self.dados['VALOR TÉCNICO'].head())

    def analisar_status(self):
        """
        Análise dos status dos serviços
        """
        if self.dados is not None:
            try:
                # Verifica se há datas válidas
                datas_validas = self.dados['DATA_TOA'].dropna()
                if len(datas_validas) == 0:
                    st.error("Não foi possível processar as datas no arquivo")
                    return
                
                data_min = datas_validas.min()
                data_max = datas_validas.max()
                
                # Filtros
                st.write("### Filtros")
                col1, col2 = st.columns(2)
                
                # Filtro de BASE
                with col1:
                    bases_disponiveis = ['Todas'] + sorted(
                        self.dados['BASE']
                        .replace('', 'Não Informado')
                        .unique()
                        .tolist()
                    )
                    base_selecionada = st.selectbox(
                        "Selecione a Base:",
                        bases_disponiveis,
                        key='base_selector_status'
                    )
                
                # Aplica filtros
                if base_selecionada != 'Todas':
                    dados_filtrados = self.dados[self.dados['BASE'] == base_selecionada]
                else:
                    dados_filtrados = self.dados
                
                # Análise de Status
                status_count = dados_filtrados.groupby('STATUS')['CONTRATO'].nunique().reset_index()
                status_count.columns = ['Status', 'Quantidade']
                status_count = status_count.sort_values('Quantidade', ascending=True)
                
                # Gráfico de Status
                fig = px.bar(status_count,
                           x='Quantidade',
                           y='Status',
                           orientation='h',
                           title=f'Quantidade de Contratos por Status {" - " + base_selecionada if base_selecionada != "Todas" else ""}')
                
                fig.update_layout(
                    showlegend=False,
                    xaxis_title="Quantidade de Contratos",
                    yaxis_title="Status",
                    height=max(400, len(status_count) * 30),
                    margin=dict(l=250, r=50)
                )
                
                fig.update_traces(
                    texttemplate='%{x}',
                    textposition='outside',
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Análise temporal de status
                status_temporal = dados_filtrados.groupby([
                    dados_filtrados['DATA_TOA'].dt.date,
                    'STATUS'
                ])['CONTRATO'].nunique().reset_index()
                
                fig = px.line(status_temporal,
                            x='DATA_TOA',
                            y='CONTRATO',
                            color='STATUS',
                            title=f'Evolução dos Status ao Longo do Tempo{" - " + base_selecionada if base_selecionada != "Todas" else ""}')
                
                fig.update_layout(
                    xaxis_title="Data",
                    yaxis_title="Quantidade de Contratos",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela resumo
                st.write("### Resumo por Status")
                resumo_status = dados_filtrados.groupby('STATUS').agg({
                    'CONTRATO': 'nunique',
                    'VALOR TÉCNICO': 'sum',
                    'VALOR EMPRESA': 'sum'
                }).reset_index()
                
                resumo_status.columns = ['Status', 'Quantidade de Contratos', 'Valor Técnico', 'Valor Empresa']
                st.dataframe(resumo_status.style.format({
                    'Valor Técnico': 'R$ {:,.2f}',
                    'Valor Empresa': 'R$ {:,.2f}'
                }))
                
            except Exception as e:
                st.error(f"Erro na análise de status: {str(e)}")

def main():
    st.set_page_config(
        page_title="Dashboard de Produtividade",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Configurações de estilo
    st.markdown("""
        <style>
            .reportview-container {
                margin-top: -2em;
            }
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display: none;}
        </style>
    """, unsafe_allow_html=True)
    
    # Menu na sidebar
    with st.sidebar:
        selected = st.radio(
            "Selecione a Análise",
            ["Produtividade dos Técnicos", "Status dos Serviços"]
        )
    
    dashboard = DashboardTecnicos()
    
    # Lista arquivos disponíveis
    arquivos = dashboard.listar_arquivos()
    
    if not arquivos:
        st.error("Nenhum arquivo encontrado na pasta Dados_excel")
    else:
        arquivo = arquivos[0]
        
        if dashboard.carregar_dados(arquivo):
            if selected == "Produtividade dos Técnicos":
                st.title("Dashboard de Produtividade - Técnicos")
                dashboard.mostrar_dados_basicos()
                dashboard.analisar_produtividade()
            else:
                st.title("Dashboard de Status dos Serviços")
                dashboard.analisar_status()  # Novo método para análise de status

if __name__ == "__main__":
    main() 