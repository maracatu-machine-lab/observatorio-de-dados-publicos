from langchain_core.prompts import PromptTemplate

TEMPLATE_EXTRACAO_RGPS = """
Você é um Engenheiro de Dados. A sua tarefa é converter a tabela financeira do texto abaixo em um arquivo JSON válido.

REGRAS DE EXTRAÇÃO (MUITO IMPORTANTE):
1. EXTRAIA TODAS AS LINHAS DA TABELA. Se houver 20 linhas no texto, o JSON deve ter as 20 linhas. Não pule nenhuma rubrica.
2. NÚMEROS: Remova pontos que separam milhares e use apenas UM PONTO para a casa decimal.
   - Errado: 52.098.7 ou 52.098,7
   - Correto: 52098.7

ESTRUTURA DE SAÍDA EXIGIDA:
{{
  "mes_referencia": "extrair_mes_ano",
  "dados": {{
    "[NOME DA PRIMEIRA RUBRICA ENCONTRADA NO TEXTO]": 0.0,
    "[NOME DA SEGUNDA RUBRICA ENCONTRADA NO TEXTO]": 0.0,
    "[NOME DA TERCEIRA RUBRICA ENCONTRADA NO TEXTO]": 0.0,
    "[CONTINUE EXTRAINDO TODAS AS OUTRAS LINHAS DA TABELA...]": 0.0
  }}
}}

Texto do PDF a ser processado:
{documento}
"""

prompt_rgps = PromptTemplate(
    input_variables=["documento"],
    template=TEMPLATE_EXTRACAO_RGPS
)
