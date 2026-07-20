import streamlit as st
import pandas as pd
import duckdb
from sqlalchemy.orm import Session
from database import engine, BronzeDocumentos, PrataExtracao

st.set_page_config(page_title="Observatório RGPS", page_icon="📊", layout="wide")

# ==================== ESTILO ====================
st.markdown("""
<style>
    .main .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background-color: #f8f9fb;
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 14px 18px;
    }
    div[data-testid="stMetricLabel"] {font-weight: 600; color: #555;}
    h1 {padding-bottom: 0.2rem;}
    .stTextArea textarea {font-family: "Menlo", "Consolas", monospace; font-size: 0.85rem;}
    div[data-testid="stExpander"] {border: 1px solid #e6e6e6; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Observatório de Dados - RGPS")
st.caption("Visualização automática dos dados extraídos dos relatórios governamentais.")

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


def executar_consulta_sql(df, consulta_sql, nome_tabela="dados"):
    """Executa uma consulta SQL (via DuckDB) sobre o DataFrame em memória."""
    con = duckdb.connect(database=":memory:")
    con.register(nome_tabela, df)
    resultado = con.execute(consulta_sql).df()
    con.close()
    return resultado


# ==================== INTERFACE (TABS) ====================
aba_prata, aba_bronze = st.tabs(["📈 Camada Prata (Dados Extraídos)", "🗄️ Camada Bronze (Auditoria)"])

with aba_prata:
    with st.spinner("Carregando dados da nuvem..."):
        df_prata = carregar_dados_prata()

    if df_prata.empty:
        st.warning("Nenhum dado encontrado na Camada Prata.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de registros", f"{len(df_prata):,}".replace(",", "."))
        col2.metric("Arquivos de origem", df_prata['Arquivo de Origem'].nunique())
        col3.metric("Colunas disponíveis", df_prata.shape[1])

        st.divider()
        st.subheader("🔎 Consulta SQL")
        st.caption(
            "A tabela em memória se chama **dados**. Exemplo: "
            "`SELECT * FROM dados WHERE \"Arquivo de Origem\" LIKE '%2024%'`"
        )

        consulta_padrao = 'SELECT * FROM dados'
        consulta_sql = st.text_area(
            "Digite sua consulta SQL:",
            value=consulta_padrao,
            height=100,
            label_visibility="collapsed",
        )

        col_run, col_reset = st.columns([1, 1])
        executar = col_run.button("▶️ Executar consulta", use_container_width=True)
        limpar = col_reset.button("↺ Limpar filtro", use_container_width=True)

        if "df_prata_filtrado" not in st.session_state:
            st.session_state.df_prata_filtrado = df_prata

        if limpar:
            st.session_state.df_prata_filtrado = df_prata

        if executar:
            try:
                st.session_state.df_prata_filtrado = executar_consulta_sql(df_prata, consulta_sql)
                st.success(f"Consulta executada: {len(st.session_state.df_prata_filtrado)} linha(s) retornada(s).")
            except Exception as e:
                st.error(f"Erro na consulta SQL: {e}")

        df_exibido = st.session_state.df_prata_filtrado

        st.divider()
        st.subheader("Dados Consolidados")
        st.markdown("Base de dados limpa e pronta para alimentar os modelos preditivos e análises de séries temporais.")
        st.dataframe(df_exibido, use_container_width=True, height=420)

        csv_prata = df_exibido.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Dados Filtrados (CSV)",
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
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de documentos", len(df_bronze))
        col2.metric("Processados com sucesso", int((df_bronze['Status'] == 'Extração Bem-Sucedida').sum()))
        col3.metric("Falhas", int(df_bronze['Status'].str.startswith('Falha').sum()))

        st.divider()
        st.dataframe(df_bronze, use_container_width=True, height=420)
        csv_bronze = df_bronze.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Catálogo (CSV)",
            data=csv_bronze,
            file_name="catalogo_bronze_auditoria.csv",
            mime="text/csv",
        )
