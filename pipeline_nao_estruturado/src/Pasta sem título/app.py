import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database import engine, BronzeDocumentos, PrataExtracao

st.set_page_config(page_title="Observatório RGPS", layout="wide")

st.title("📊 Observatório de Dados - RGPS")
st.markdown("Visualização automática dos dados extraídos dos relatórios governamentais.")

# ==================== FUNÇÕES DE CARREGAMENTO ====================
@st.cache_data(ttl=60)
def carregar_dados_prata():
    """Busca os dados extraídos e estruturados."""
    with Session(engine) as session:
        registros = session.query(PrataExtracao, BronzeDocumentos).join(
            BronzeDocumentos, PrataExtracao.documento_id == BronzeDocumentos.id
        ).all()
        
        lista_dataframes = []
        for extracao, documento in registros:
            df = pd.DataFrame(extracao.dados_json)
            df['Arquivo de Origem'] = documento.nome_arquivo
            df['Data de Extração'] = documento.data_processamento
            lista_dataframes.append(df)
            
        if lista_dataframes:
            return pd.concat(lista_dataframes, ignore_index=True)
        return pd.DataFrame()

@st.cache_data(ttl=60)
def carregar_dados_bronze():
    """Busca o catálogo de metadados e auditoria dos arquivos."""
    with Session(engine) as session:
        registros = session.query(BronzeDocumentos).all()
        dados = []
        for doc in registros:
            dados.append({
                "ID": doc.id,
                "Nome do Arquivo": doc.nome_arquivo,
                "Hash (SHA-256)": doc.hash_documento,
                "URL de Origem": doc.url_origem,
                "Processado em": doc.data_processamento,
                "Status": doc.status
            })
        return pd.DataFrame(dados)

# ==================== INTERFACE (TABS) ====================
# Cria abas para organizar a visualização
aba_prata, aba_bronze = st.tabs(["📈 Camada Prata (Dados Extraídos)", "🗄️ Camada Bronze (Auditoria)"])

with aba_prata:
    st.subheader("Dados Consolidados")
    st.markdown("Base de dados limpa e pronta para alimentar os modelos preditivos e análises de séries temporais.")
    
    with st.spinner("Carregando dados da nuvem..."):
        df_prata = carregar_dados_prata()

    if df_prata.empty:
        st.warning("Nenhum dado encontrado na Camada Prata.")
    else:
        st.dataframe(df_prata, use_container_width=True)
        csv_prata = df_prata.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Dados (CSV)",
            data=csv_prata,
            file_name="dados_rgps_prata.csv",
            mime="text/csv",
        )

with aba_bronze:
    st.subheader("Catálogo de Documentos")
    st.markdown("Histórico de rastreabilidade de todos os relatórios brutos processados pelo sistema.")
    
    with st.spinner("Carregando catálogo da nuvem..."):
        df_bronze = carregar_dados_bronze()

    if df_bronze.empty:
        st.warning("Nenhum documento registrado na Camada Bronze.")
    else:
        st.dataframe(df_bronze, use_container_width=True)
        csv_bronze = df_bronze.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Catálogo (CSV)",
            data=csv_bronze,
            file_name="catalogo_bronze_auditoria.csv",
            mime="text/csv",
        )