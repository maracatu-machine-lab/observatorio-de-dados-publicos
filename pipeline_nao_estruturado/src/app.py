import streamlit as st
import pandas as pd
import tempfile
import os
import json

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from langchain_community.llms import Ollama

from models.prompts import prompt_rgps

st.set_page_config(page_title="Pipeline ETL RGPS (Open-Source)", layout="wide")
st.title("🏛️ Construtor de Série Histórica do RGPS")
st.markdown("Metodologia baseada em **Docling** + **LangChain** com IA 100% local (Llama 3.2).")

@st.cache_resource
def carregar_conversor():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.do_code_enrichment = False

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )

conversor_docling = carregar_conversor()
llm_local = Ollama(model="llama3.2")

arquivos_pdf = st.file_uploader("Selecione os arquivos PDF governamentais", type=["pdf"], accept_multiple_files=True)

if arquivos_pdf:
    st.info(f"📁 {len(arquivos_pdf)} arquivo(s) carregado(s) para processamento local.")

    if st.button("🚀 Iniciar Extração LangChain + Docling", type="primary"):
        dados_consolidados = {}
        barra_progresso = st.progress(0)

        for i, arquivo in enumerate(arquivos_pdf):
            with st.spinner(f"Processando {arquivo.name}..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(arquivo.getvalue())
                        caminho_pdf = tmp.name

                    resultado_docling = conversor_docling.convert(caminho_pdf)
                    texto_markdown = resultado_docling.document.export_to_markdown()
                    os.unlink(caminho_pdf)

                    chain = prompt_rgps | llm_local
                    resposta_bruta = chain.invoke({"documento": texto_markdown})

                    texto_limpo = resposta_bruta.strip()
                    if "```json" in texto_limpo:
                        texto_limpo = texto_limpo.split("```json")[1].split("```")[0]
                    elif "```" in texto_limpo:
                        texto_limpo = texto_limpo.split("```")[1]

                    extracao = json.loads(texto_limpo.strip())
                    mes = extracao.get("mes_referencia", f"Desconhecido_{i}")
                    valores = extracao.get("dados", {})
                    dados_consolidados[mes] = valores

                except Exception as e:
                    st.error(f"Erro ao processar {arquivo.name}: {str(e)}")
                    continue

                barra_progresso.progress((i + 1) / len(arquivos_pdf))

        if dados_consolidados:
            st.success("✨ Processamento concluído com sucesso!")
            df_historico = pd.DataFrame.from_dict(dados_consolidados, orient='index')
            st.dataframe(df_historico, use_container_width=True)

            st.download_button(
                label="📥 Baixar Série Histórica (CSV)",
                data=df_historico.to_csv(),
                file_name="serie_historica_rgps.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.warning("Nenhum dado foi extraído.")
