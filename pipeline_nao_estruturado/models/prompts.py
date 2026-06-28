from langchain_core.prompts import PromptTemplate

TEMPLATE_EXTRACAO_RGPS = """
Você é um especialista em extração de dados financeiros de documentos do RGPS.

Tarefa: Extrair os dados da tabela "RESULTADO DO RGPS EM R$ MILHÕES NOMINAIS" para um JSON.

Regras de Ouro:
1. NÃO omita nenhuma linha. Se o valor estiver vazio ou for zero, coloque 0.
2. Identifique o mês e ano na coluna de referência.
3. Extraia o nome da rubrica exatamente como está no texto.
4. Se uma rubrica tiver sub-itens (ex: 2.1, 2.2), extraia todos.

Exemplo do formato desejado:
{{
  "mes_referencia": "jan/25",
  "dados": {{
    "1. Receita Previdenciária": 5000.0,
    "2. Renúncias Previdenciárias": 200.0,
    "2.1 Simples Nacional": 150.0,
    "4. Resultado do RGPS com Renúncias": 4800.0
  }}
}}

Texto do PDF:
{documento}

Retorne APENAS o JSON. Não inclua blocos de markdown ```json.
"""

prompt_rgps = PromptTemplate(
    input_variables=["documento"],
    template=TEMPLATE_EXTRACAO_RGPS
)
