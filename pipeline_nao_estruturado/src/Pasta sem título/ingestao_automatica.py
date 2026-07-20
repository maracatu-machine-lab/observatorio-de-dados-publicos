import os
import tempfile
import hashlib
import requests
import json
import pandas as pd
from datetime import datetime

from sqlalchemy.orm import Session
from database import engine, BronzeDocumentos, PrataExtracao

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

# ==================== CONFIGURAÇÃO DO DOCLING ====================
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

# ==================== FUNÇÕES DE INTEGRIDADE ====================
def calcular_hash_sha256(caminho_arquivo):
    sha256_hash = hashlib.sha256()
    with open(caminho_arquivo, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def identificar_tabela_alvo(df):
    texto_tabela = df.to_string().lower()
    ancoras = [
        "arrecadação líquida total",
        "renúncias previdenciárias",
        "resultado do rgps com renúncias"
    ]
    return all(ancora in texto_tabela for ancora in ancoras)

# ==================== ORQUESTRAÇÃO DE PIPELINE ====================
def processar_pdf(url_pdf, nome_arquivo):
    print(f"\n🚀 Iniciando processamento: {nome_arquivo}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url_pdf, stream=True, headers=headers, timeout=30)
        resposta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Falha no download de {url_pdf}: {e}")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        for chunk in resposta.iter_content(chunk_size=8192):
            tmp.write(chunk)
        caminho_pdf = tmp.name

    hash_doc = calcular_hash_sha256(caminho_pdf)
    print(f"🔍 Hash do Documento: {hash_doc}")

    with Session(engine) as session:
        documento_existente = session.query(BronzeDocumentos).filter_by(hash_documento=hash_doc).first()
        if documento_existente:
            print(f"⚠️ Documento já catalogado na Camada Bronze (ID: {documento_existente.id}). Ignorando extração.")
            os.unlink(caminho_pdf)
            return

        print("⚙️ Inspecionando estrutura tabular via Docling...")
        resultado = conversor_docling.convert(caminho_pdf)
        tabela_extraida = None

        for table in resultado.document.tables:
            df_bruto = table.export_to_dataframe()
            if df_bruto.empty:
                continue
            
            if identificar_tabela_alvo(df_bruto):
                tabela_extraida = df_bruto
                break

        if tabela_extraida is not None:
            novo_doc = BronzeDocumentos(
                nome_arquivo=nome_arquivo,
                hash_documento=hash_doc,
                url_origem=url_pdf,
                status="Extração Bem-Sucedida"
            )
            session.add(novo_doc)
            session.flush() 
            
            dados_json_string = tabela_extraida.to_json(orient="records", force_ascii=False)
            dados_json_objeto = json.loads(dados_json_string) 
            
            nova_extracao = PrataExtracao(
                documento_id=novo_doc.id,
                dados_json=dados_json_objeto
            )
            session.add(nova_extracao)
            
            session.commit()
            print(f"✅ Sucesso! Tabela salva no PostgreSQL vinculada ao arquivo '{nome_arquivo}'.")
        else:
            print("❌ Falha: A tabela âncora não foi encontrada nas páginas deste PDF.")
            novo_doc_falho = BronzeDocumentos(
                nome_arquivo=nome_arquivo,
                hash_documento=hash_doc,
                url_origem=url_pdf,
                status="Falha: Tabela Alvo Não Localizada"
            )
            session.add(novo_doc_falho)
            session.commit()

    os.unlink(caminho_pdf)

# ==================== EXECUÇÃO VIA ARQUIVO DE TEXTO ====================
if __name__ == "__main__":
    caminho_arquivo_urls = os.path.join(os.path.dirname(__file__), "..", "urls_alvo.txt")
    
    if not os.path.exists(caminho_arquivo_urls):
        print(f"❌ O arquivo não foi encontrado: {caminho_arquivo_urls}")
        print("Por favor, crie o arquivo 'urls_alvo.txt' na raiz do projeto.")
    else:
        with open(caminho_arquivo_urls, "r") as arquivo:
            linhas = arquivo.readlines()
        
        urls = [linha.strip() for linha in linhas if linha.strip() and not linha.startswith("#")]
        
        if not urls:
            print("⚠️ O arquivo urls_alvo.txt está vazio ou contém apenas comentários.")
        else:
            print(f"📋 Foram encontradas {len(urls)} URLs no arquivo de configuração.")
            for url in urls:
                nome_arquivo = url.split('/')[-1]
                processar_pdf(url, nome_arquivo)