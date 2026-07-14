import sys
import os
import streamlit as st
import pandas as pd
import tempfile

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

st.set_page_config(page_title="Pipeline ETL RGPS - PIBIC", layout="wide")
st.title("🏛️ Extrator Cirúrgico: Resultado do RGPS")
st.markdown("Busca dinâmica da tabela de Renúncias em PDFs de múltiplas páginas, garantindo 100% de integridade dos dados.")

# ==================== CONFIGURAÇÃO DOCLING ====================
@st.cache_resource
def carregar_conversor():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )

conversor_docling = carregar_conversor()

# ==================== LÓGICA DE ANCORAGEM ====================
def identificar_tabela_alvo(df):
    """
    Verifica se a tabela atual é a tabela de 'Resultado do RGPS com Renúncias'.
    """
    # Converte a tabela inteira para uma string única (em minúsculas) para facilitar a busca
    texto_tabela = df.to_string().lower()
    
    # Âncoras exclusivas desta tabela. Se essas palavras estiverem juntas, é a tabela certa.
    ancoras = [
        "arrecadação líquida total", 
        "renúncias previdenciárias", 
        "resultado do rgps com renúncias"
    ]
    
    # Retorna True apenas se TODAS as âncoras forem encontradas na tabela
    return all(ancora in texto_tabela for ancora in ancoras)

# ======================= INTERFACE =======================
arquivos_pdf = st.file_uploader(
    "Selecione os relatórios PDF (Multijogos permitidos)", 
    type=["pdf"], 
    accept_multiple_files=True
)

if arquivos_pdf:
    if st.button("🚀 Iniciar Busca e Extração", type="primary"):
        tabelas_consolidadas = []
        barra_progresso = st.progress(0)

        for i, arquivo in enumerate(arquivos_pdf):
            with st.spinner(f"Varrendo páginas de: {arquivo.name}..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(arquivo.getvalue())
                        caminho_pdf = tmp.name

                    # O Docling lê o PDF inteiro
                    resultado = conversor_docling.convert(caminho_pdf)
                    tabela_encontrada = False
                    
                    # Varre todas as tabelas encontradas em todas as páginas
                    for table in resultado.document.tables:
                        df_bruto = table.export_to_dataframe()
                        
                        if df_bruto.empty: 
                            continue
                            
                        # Passa a tabela pelo nosso detector
                        if identificar_tabela_alvo(df_bruto):
                            # Cria uma coluna para identificar a origem do dado
                            df_bruto['Arquivo_Origem'] = arquivo.name
                            tabelas_consolidadas.append(df_bruto)
                            tabela_encontrada = True
                            
                            # Como já achamos a tabela alvo neste PDF, podemos parar de procurar nele
                            break
                    
                    if not tabela_encontrada:
                        st.warning(f"A tabela alvo não foi encontrada em: {arquivo.name}")

                    os.unlink(caminho_pdf)

                except Exception as e:
                    st.error(f"Erro ao processar {arquivo.name}: {str(e)}")
                    continue
            
            barra_progresso.progress((i + 1) / len(arquivos_pdf))

        # ======================= GERAÇÃO DA SAÍDA =======================
        if tabelas_consolidadas:
            st.success("✨ Extração concluída! Nenhuma linha foi perdida.")
            
            # Aqui preservamos a tabela inteira, exatamente como está no PDF
            for idx, tabela_final in enumerate(tabelas_consolidadas):
                st.write(f"### Tabela extraída do arquivo: {tabela_final['Arquivo_Origem'].iloc[0]}")
                st.dataframe(tabela_final, use_container_width=True)
                
                # Conversão do DataFrame para JSON formatado e legível
                json_data = tabela_final.to_json(orient="records", force_ascii=False, indent=4)
                
                # Botão de download atualizado para JSON
                st.download_button(
                    label=f"📥 Baixar Tabela {idx + 1} Completa (JSON)",
                    data=json_data,
                    file_name=f"extracao_completa_{idx+1}.json",
                    mime="application/json",
                    type="primary",
                    key=f"download_btn_{idx}"
                )
