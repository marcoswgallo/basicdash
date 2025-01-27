import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import gc

# Adicione esta constante no início do arquivo, após os imports
GRUPOS_BASES = {
    'Instalação': [
        'BASE BAURU',
        'BASE BOTUCATU',
        'BASE CAMPINAS',
        'BASE LIMEIRA',
        'BASE PAULINIA',
        'BASE PIRACICABA',
        'BASE RIBEIRAO PRETO',
        'BASE SAO JOSE DO RIO PRETO',
        'BASE SOROCABA',
        'BASE SUMARE',
        'GPON BAURU',
        'GPON RIBEIRAO PRETO'
    ],
    'Manutenção': [
        'BASE ARARAS VT',
        'BASE BOTUCATU VT',
        'BASE MDU ARARAS',
        'BASE MDU BAURU',
        'BASE MDU MOGI',
        'BASE MDU PIRACICABA',
        'BASE MDU SJRP',
        'BASE PIRACICABA VT',
        'BASE RIBEIRÃO VT',
        'BASE SERTAOZINHO VT',
        'BASE SUMARE VT',
        'BASE VAR BAURU',
        'BASE VAR PIRACICABA',
        'BASE VAR SUMARE'
    ],
    'Desconexão': [
        'DESCONEXAO',
        'DESCONEXÃO BOTUCATU',
        'DESCONEXÃO CAMPINAS',
        'DESCONEXAO RIBEIRAO PRETO'
    ]
}

# Função auxiliar para encontrar o grupo de uma base
def get_grupo_base(base):
    for grupo, bases in GRUPOS_BASES.items():
        if base in bases:
            return grupo
    return "Outros"  # Para bases que não estão em nenhum grupo

class DashboardTecnicos:
    def __init__(self):
        self.dados = None
        self.pasta_dados = "Dados_excel"
        self.cached_file = None
        
        # Verifica se a pasta existe
        if not os.path.exists(self.pasta_dados):
            os.makedirs(self.pasta_dados)
            st.warning(f"Pasta {self.pasta_dados} foi criada. Por favor, adicione seus arquivos Excel/CSV nela.")
        
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
        
        self.grupos_bases = GRUPOS_BASES
        
    def listar_arquivos(self):
        """
        Lista todos os arquivos Excel e CSV na pasta Dados_excel
        """
        try:
            if not os.path.exists(self.pasta_dados):
                st.error(f"Pasta {self.pasta_dados} não encontrada")
                return []
            
            arquivos = [f for f in os.listdir(self.pasta_dados) 
                       if f.endswith(('.xlsx', '.csv'))]
            
            if not arquivos:
                st.warning(f"Nenhum arquivo Excel/CSV encontrado em {self.pasta_dados}")
                st.info("Formatos suportados: .xlsx, .csv")
                return []
            
            return sorted(arquivos)  # Retorna arquivos em ordem alfabética
        
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
    @st.cache_data(ttl=3600, show_spinner=False, max_entries=3)  # Limita o número de entradas em cache
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
                    .str.replace(r'[R$.]', '', regex=True)  # Remove R$ e pontos
                    .str.replace(',', '.', regex=False)     # Troca vírgula por ponto
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
                
            # Limpa a memória antes de carregar novos dados
            if self.dados is not None:
                del self.dados
                gc.collect()
                
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
                self.dados['DATA_TOA'] = pd.to_datetime(
                    self.dados['DATA_TOA'],
                    dayfirst=True,  # Especifica que o dia vem primeiro
                    errors='coerce'
                )
            
            # Otimiza memória
            self.dados = self.dados.copy()
            
            # Adiciona coluna de grupo
            self.dados['GRUPO'] = self.dados['BASE'].apply(get_grupo_base)
            
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
        if self.dados is None:
            st.error("Nenhum dado carregado. Por favor, carregue um arquivo primeiro.")
            return
        
        try:
            # Validação inicial dos dados
            colunas_obrigatorias = ['DATA_TOA', 'TECNICO', 'BASE', 'STATUS', 'CONTRATO']
            colunas_faltantes = [col for col in colunas_obrigatorias if col not in self.dados.columns]
            
            if colunas_faltantes:
                st.error(f"Colunas obrigatórias faltando: {', '.join(colunas_faltantes)}")
                return
            
            # Verifica se há datas válidas
            datas_validas = self.dados['DATA_TOA'].dropna()
            if len(datas_validas) == 0:
                st.error("Não foi possível processar as datas no arquivo")
                return
            
            data_min = datas_validas.min()
            data_max = datas_validas.max()
            
            # Filtros
            st.write("### Filtros")
            col1, col2, col3 = st.columns(3)  # Mudamos para 3 colunas
            
            # Filtro de GRUPO e BASE
            with col1:
                if 'GRUPO' in self.dados.columns:
                    grupos_disponiveis = ['Todos'] + sorted(self.dados['GRUPO'].unique().tolist())
                    grupo_selecionado = st.selectbox(
                        "Selecione o Grupo:",
                        grupos_disponiveis,
                        key='grupo_selector'
                    )
                    
                    # Filtra as bases baseado no grupo selecionado
                    if grupo_selecionado != 'Todos':
                        bases_filtradas = self.dados[self.dados['GRUPO'] == grupo_selecionado]['BASE'].unique()
                    else:
                        bases_filtradas = self.dados['BASE'].unique()
                    
                    bases_disponiveis = ['Todas'] + sorted(bases_filtradas.tolist())
                    base_selecionada = st.selectbox(
                        "Selecione a Base:",
                        bases_disponiveis,
                        key='base_selector'
                    )
            
            # Filtro de STATUS
            with col2:
                if 'STATUS' in self.dados.columns:
                    status_disponiveis = sorted(self.dados['STATUS'].dropna().unique().tolist())
                    status_selecionados = st.multiselect(
                        "Selecione os Status:",
                        status_disponiveis,
                        default=status_disponiveis
                    )
            
            # Aplica os filtros
            # 1. Filtro de período
            mask_periodo = (self.dados['DATA_TOA'] >= data_min) & \
                          (self.dados['DATA_TOA'] <= data_max)
            
            # 2. Filtro de GRUPO e BASE
            if grupo_selecionado != 'Todos':
                mask_grupo = (self.dados['GRUPO'] == grupo_selecionado)
            else:
                mask_grupo = pd.Series(True, index=self.dados.index)
            
            if base_selecionada != 'Todas':
                mask_base = (self.dados['BASE'] == base_selecionada)
            else:
                mask_base = pd.Series(True, index=self.dados.index)
            
            # 3. Filtro de STATUS
            if status_selecionados:
                mask_status = self.dados['STATUS'].isin(status_selecionados)
            else:
                st.warning("Por favor, selecione pelo menos um status")
                return
            
            # Aplica todos os filtros
            dados_filtrados = self.dados[mask_periodo & mask_grupo & mask_base & mask_status]
            
            # Remove bases com valores zerados
            dados_agrupados = dados_filtrados.groupby('BASE').agg({
                'CONTRATO': 'count',
                'VALOR EMPRESA': 'sum'
            }).reset_index()
            
            bases_ativas = dados_agrupados[
                (dados_agrupados['CONTRATO'] > 0) | 
                (dados_agrupados['VALOR EMPRESA'] > 0)
            ]['BASE'].unique()
            
            dados_filtrados = dados_filtrados[dados_filtrados['BASE'].isin(bases_ativas)]
            
            if len(dados_filtrados) == 0:
                st.warning("Nenhum dado encontrado para os filtros selecionados")
                return
            
            # Adiciona métricas dinâmicas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_registros = len(dados_filtrados)
                st.metric(
                    "Total de Registros",
                    f"{total_registros:,}",
                    help="Número total de registros após aplicar os filtros"
                )
            
            with col2:
                total_tecnicos = dados_filtrados['TECNICO'].nunique()
                st.metric(
                    "Total de Técnicos",
                    f"{total_tecnicos:,}",
                    help="Número de técnicos únicos"
                )
            
            with col3:
                valor_total = dados_filtrados['VALOR EMPRESA'].sum()
                st.metric(
                    "Valor Total",
                    f"R$ {valor_total:,.2f}",
                    help="Soma do valor empresa"
                )
            
            with col4:
                media_por_tecnico = valor_total / total_tecnicos if total_tecnicos > 0 else 0
                st.metric(
                    "Média por Técnico",
                    f"R$ {media_por_tecnico:,.2f}",
                    help="Valor total dividido pelo número de técnicos"
                )
            
            # Adiciona informação do filtro atual
            if grupo_selecionado != 'Todos' or base_selecionada != 'Todas':
                st.info(
                    f"📊 Mostrando dados para: " +
                    (f"Grupo **{grupo_selecionado}**" if grupo_selecionado != 'Todos' else '') +
                    (' > ' if grupo_selecionado != 'Todos' and base_selecionada != 'Todas' else '') +
                    (f"Base **{base_selecionada}**" if base_selecionada != 'Todas' else '')
                )
            
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

    def mostrar_tabela_bases(self, dados_filtrados, grupo_selecionado='Todos'):
        """
        Mostra os dados em formato de tabela similar ao Excel
        """
        try:
            # Verifica se há dados
            if len(dados_filtrados) == 0:
                st.warning("Não há dados para gerar as tabelas com os filtros atuais")
                return

            # Filtra por grupo se necessário
            if grupo_selecionado != 'Todos':
                dados_filtrados = dados_filtrados[dados_filtrados['GRUPO'] == grupo_selecionado]

            # Remove bases com valores zerados
            dados_agrupados = dados_filtrados.groupby('BASE').agg({
                'VALOR EMPRESA': 'sum',
                'CONTRATO': 'count',
                'TECNICO': 'nunique'
            }).reset_index()
            
            # Filtra apenas bases com valores ou contratos
            dados_agrupados = dados_agrupados[
                (dados_agrupados['VALOR EMPRESA'] > 0) | 
                (dados_agrupados['CONTRATO'] > 0) |
                (dados_agrupados['TECNICO'] > 0)
            ]

            # Verifica se há resultados após o agrupamento
            if len(dados_agrupados) == 0:
                st.warning("Não há dados ativos para gerar as tabelas")
                return

            # Calcula VL EQ (Valor por Equipe)
            dados_agrupados['VL EQ'] = dados_agrupados.apply(
                lambda x: round(x['VALOR EMPRESA'] / x['TECNICO'], 2) if x['TECNICO'] > 0 else 0, 
                axis=1
            )
            
            # Calcula EQ_CTTS (Contratos por Equipe)
            dados_agrupados['EQ_CTTS'] = dados_agrupados.apply(
                lambda x: round(x['CONTRATO'] / x['TECNICO'], 1) if x['TECNICO'] > 0 else 0,
                axis=1
            )

            # Renomeia as colunas
            dados_agrupados.columns = ['BASE', 'VALOR', 'CONTRATOS', 'EQUIPES', 'VL EQ', 'EQ_CTTS']

            # Ordena por BASE
            dados_agrupados = dados_agrupados.sort_values('BASE')

            # Adiciona linha de total
            total = pd.DataFrame({
                'BASE': ['Total Geral'],
                'VALOR': [dados_agrupados['VALOR'].sum()],
                'CONTRATOS': [dados_agrupados['CONTRATOS'].sum()],
                'EQUIPES': [dados_agrupados['EQUIPES'].sum()],
                'VL EQ': [round(dados_agrupados['VALOR'].sum() / dados_agrupados['EQUIPES'].sum(), 2) if dados_agrupados['EQUIPES'].sum() > 0 else 0],
                'EQ_CTTS': [round(dados_agrupados['CONTRATOS'].sum() / dados_agrupados['EQUIPES'].sum(), 1) if dados_agrupados['EQUIPES'].sum() > 0 else 0]
            })

            # Concatena e reseta o índice
            dados_agrupados = pd.concat([dados_agrupados, total], ignore_index=True)

            # Formata a tabela
            st.write("### Resumo por Base")
            st.dataframe(
                dados_agrupados.style
                .format({
                    'VALOR': 'R$ {:,.2f}',
                    'VL EQ': lambda x: 'R$ {:,.2f}'.format(x) if x > 0 else '-',
                    'CONTRATOS': '{:,.0f}',
                    'EQUIPES': '{:,.0f}',
                    'EQ_CTTS': lambda x: '{:,.1f}'.format(x) if x > 0 else '-'
                })
                .set_properties(**{
                    'background-color': '#262730',
                    'color': 'white',
                    'border': '1px solid gray'
                })
                .set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#1E1E1E'), ('color', 'white')]},
                    {'selector': 'tr:last-child', 'props': [('background-color', '#1E1E1E'), ('font-weight', 'bold')]}
                ])
            )

            # Mesma lógica para a tabela de desconexão
            if 'TIPO DE SERVIÇO' in dados_filtrados.columns:
                desconexao = dados_filtrados[
                    dados_filtrados['TIPO DE SERVIÇO'].str.contains('DESCONEX', case=False, na=False)
                ]

                if len(desconexao) > 0:
                    desconexao = desconexao.groupby('BASE').agg({
                        'VALOR EMPRESA': 'sum',
                        'CONTRATO': 'count',
                        'TECNICO': 'nunique'
                    }).reset_index()

                    # Filtra apenas bases com valores ou contratos
                    desconexao = desconexao[
                        (desconexao['VALOR EMPRESA'] > 0) | 
                        (desconexao['CONTRATO'] > 0) |
                        (desconexao['TECNICO'] > 0)
                    ]

                    if len(desconexao) > 0:
                        # Calcula métricas adicionais
                        desconexao['VL EQ'] = desconexao.apply(
                            lambda x: x['VALOR EMPRESA'] / x['TECNICO'] if x['TECNICO'] > 0 else 0,
                            axis=1
                        )
                        desconexao['EQ_CTTS'] = desconexao.apply(
                            lambda x: (x['CONTRATO'] / x['TECNICO']).round(1) if x['TECNICO'] > 0 else 0,
                            axis=1
                        )

                        # Adiciona total
                        total_desc = pd.DataFrame({
                            'BASE': ['Total Geral'],
                            'VALOR EMPRESA': [desconexao['VALOR EMPRESA'].sum()],
                            'CONTRATO': [desconexao['CONTRATO'].sum()],
                            'TECNICO': [desconexao['TECNICO'].sum()],
                            'VL EQ': [desconexao['VALOR EMPRESA'].sum() / desconexao['TECNICO'].sum() if desconexao['TECNICO'].sum() > 0 else 0],
                            'EQ_CTTS': [(desconexao['CONTRATO'].sum() / desconexao['TECNICO'].sum()).round(1) if desconexao['TECNICO'].sum() > 0 else 0]
                        })

                        desconexao = pd.concat([desconexao, total_desc], ignore_index=True)

                        st.write("### Desconexão")
                        st.dataframe(
                            desconexao.style
                            .format({
                                'VALOR EMPRESA': 'R$ {:,.2f}',
                                'VL EQ': lambda x: 'R$ {:,.2f}'.format(x) if x > 0 else '-',
                                'CONTRATO': '{:,.0f}',
                                'TECNICO': '{:,.0f}',
                                'EQ_CTTS': lambda x: '{:,.1f}'.format(x) if x > 0 else '-'
                            })
                            .set_properties(**{
                                'background-color': '#262730',
                                'color': 'white',
                                'border': '1px solid gray'
                            })
                            .set_table_styles([
                                {'selector': 'th', 'props': [('background-color', '#1E1E1E'), ('color', 'white')]},
                                {'selector': 'tr:last-child', 'props': [('background-color', '#1E1E1E'), ('font-weight', 'bold')]}
                            ])
                        )
                    else:
                        st.info("Não há dados de desconexão ativos para os filtros selecionados")

        except Exception as e:
            st.error(f"Erro ao gerar tabelas: {str(e)}")
            st.error(f"Quantidade de dados filtrados: {len(dados_filtrados)}")
            st.error(f"Colunas disponíveis: {list(dados_filtrados.columns)}")

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

def load_css():
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Dashboard de Produtividade",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Carrega o CSS externo
    load_css()
    
    # Adiciona um loader
    with st.spinner('Carregando dashboard...'):
        menu_items = {
            "Produtividade dos Técnicos": "📊",
            "Status dos Serviços": "📈"
        }
        
        with st.sidebar:
            st.title("🔧 Menu Principal")
            selected = st.radio(
                "Selecione a Análise",
                list(menu_items.keys()),
                format_func=lambda x: f"{menu_items[x]} {x}"
            )
        
        dashboard = DashboardTecnicos()
        
        # Lista arquivos disponíveis
        arquivos = dashboard.listar_arquivos()
        
        if not arquivos:
            st.error("Nenhum arquivo encontrado na pasta Dados_excel")
            st.info("Por favor, adicione seus arquivos Excel/CSV na pasta Dados_excel")
        else:
            # Permite selecionar o arquivo se houver mais de um
            if len(arquivos) > 1:
                arquivo = st.selectbox(
                    "Selecione o arquivo para análise:",
                    arquivos,
                    format_func=lambda x: f"📄 {x}"
                )
            else:
                arquivo = arquivos[0]
            
            if dashboard.carregar_dados(arquivo):
                if selected == "Produtividade dos Técnicos":
                    st.title("Dashboard de Produtividade - Técnicos")
                    dashboard.mostrar_dados_basicos()
                    dashboard.analisar_produtividade()
                else:
                    st.title("Dashboard de Status dos Serviços")
                    dashboard.analisar_status()

if __name__ == "__main__":
    main() 