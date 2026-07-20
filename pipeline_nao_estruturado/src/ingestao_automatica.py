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
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

# ==================== CONFIGURAÇÃO DO DOCLING ====================
# O TableFormer (modelo de estrutura de tabela do Docling) às vezes prevê a
# caixa delimitadora de uma célula um pouco deslocada. Com do_cell_matching=True
# (padrão), o Docling tenta "casar" essa caixa com o texto real do PDF; se a
# caixa estiver deslocada, não encontra nada ali e a célula sai vazia — mesmo
# o texto existindo no PDF. Com do_cell_matching=False, o Docling usa o texto
# que o próprio modelo reconhece visualmente na célula, sem depender desse
# casamento de posição, o que preenche essas lacunas.
#
# Estratégia: converter o PDF nos dois modos e mesclar (ver mesclar_tabelas),
# priorizando sempre o texto real do PDF e usando o texto previsto só como
# fallback para células que vieram vazias.
def carregar_conversor(do_cell_matching):
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.table_structure_options.do_cell_matching = do_cell_matching
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )

conversor_docling_preciso = carregar_conversor(do_cell_matching=True)
conversor_docling_previsto = carregar_conversor(do_cell_matching=False)

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

def _normalizar_vazios(df):
    """Converte células vazias/só-espaço em NaN, sem alterar nenhum valor real."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(r'^\s*$', pd.NA, regex=True)
            df[col] = df[col].replace({'nan': pd.NA, 'None': pd.NA})
    return df

def mesclar_tabelas(df_preciso, df_previsto):
    """
    Combina as duas extrações da mesma tabela:
    - df_preciso: extraído com do_cell_matching=True (texto real do PDF).
    - df_previsto: extraído com do_cell_matching=False (texto que o modelo
      reconhece visualmente na célula prevista).

    Regra: SEMPRE usa o valor real do PDF (df_preciso). Só recorre ao valor
    de df_previsto quando a célula em df_preciso está de fato vazia — ou
    seja, nunca substitui um dado que já foi lido corretamente.
    """
    df_preciso = _normalizar_vazios(df_preciso)

    if df_previsto is None or df_previsto.shape != df_preciso.shape:
        if df_previsto is not None:
            print("⚠️ As duas extrações vieram com formatos diferentes; "
                  "usando apenas a extração com texto real (algumas células podem ficar vazias).")
        return df_preciso

    df_previsto = _normalizar_vazios(df_previsto)
    df_final = df_preciso.copy()

    preenchidos = 0
    for col in df_final.columns:
        for idx in df_final.index:
            valor_real = df_preciso.at[idx, col]
            if pd.isna(valor_real):
                valor_previsto = df_previsto.at[idx, col]
                if pd.notna(valor_previsto):
                    df_final.at[idx, col] = valor_previsto
                    preenchidos += 1

    if preenchidos:
        print(f"{preenchidos} célula(s) que vieram vazias na extração precisa "
              f"foram preenchidas com o texto previsto pelo modelo.")

    return df_final

# ==================== ORQUESTRAÇÃO DE PIPELINE ====================
def processar_pdf(url_pdf, nome_arquivo):
    print(f"\nIniciando processamento: {nome_arquivo}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url_pdf, stream=True, headers=headers, timeout=30)
        resposta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Falha no download de {url_pdf}: {e}")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        for chunk in resposta.iter_content(chunk_size=8192):
            tmp.write(chunk)
        caminho_pdf = tmp.name

    hash_doc = calcular_hash_sha256(caminho_pdf)
    print(f"Hash do Documento: {hash_doc}")

    with Session(engine) as session:
        documento_existente = session.query(BronzeDocumentos).filter_by(hash_documento=hash_doc).first()
        if documento_existente:
            print(f"Documento já catalogado na Camada Bronze (ID: {documento_existente.id}). Ignorando extração.")
            os.unlink(caminho_pdf)
            return

        print("Inspecionando estrutura tabular via Docling (extração precisa)...")
        resultado_preciso = conversor_docling_preciso.convert(caminho_pdf)
        df_alvo_preciso = None

        for table in resultado_preciso.document.tables:
            df_bruto = table.export_to_dataframe()
            if df_bruto.empty:
                continue
            if identificar_tabela_alvo(df_bruto):
                df_alvo_preciso = df_bruto
                break

        tabela_extraida = None
        if df_alvo_preciso is not None:
            print("Rodando segunda passada (texto previsto) para preencher eventuais lacunas...")
            resultado_previsto = conversor_docling_previsto.convert(caminho_pdf)
            df_alvo_previsto = None

            for table in resultado_previsto.document.tables:
                df_bruto = table.export_to_dataframe()
                if df_bruto.empty:
                    continue
                if identificar_tabela_alvo(df_bruto):
                    df_alvo_previsto = df_bruto
                    break

            tabela_extraida = mesclar_tabelas(df_alvo_preciso, df_alvo_previsto)

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
            print(f"Sucesso! Tabela salva no PostgreSQL vinculada ao arquivo '{nome_arquivo}'.")
        else:
            print("Falha: A tabela âncora não foi encontrada nas páginas deste PDF.")
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
        print(f"O arquivo não foi encontrado: {caminho_arquivo_urls}")
        print("Por favor, crie o arquivo 'urls_alvo.txt' na raiz do projeto.")
    else:
        with open(caminho_arquivo_urls, "r") as arquivo:
            linhas = arquivo.readlines()
        
        urls = [linha.strip() for linha in linhas if linha.strip() and not linha.startswith("#")]
        
        if not urls:
            print("O arquivo urls_alvo.txt está vazio ou contém apenas comentários.")
        else:
            print(f"Foram encontradas {len(urls)} URLs no arquivo de configuração.")
            for url in urls:
                nome_arquivo = url.split('/')[-1]
                processar_pdf(url, nome_arquivo)