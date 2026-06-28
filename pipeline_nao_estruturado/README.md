# 🏛️ Pipeline ETL - RGPS (Série Histórica)

## Descrição do Projeto
Este repositório contém a infraestrutura de extração e consolidação de dados governamentais do Regime Geral de Previdência Social (RGPS). O objetivo é construir séries históricas a partir de relatórios em PDF, automatizando o alinhamento de rubricas financeiras (com foco nas Renúncias Previdenciárias).

## Metodologia Computacional
O pipeline foi construído com tecnologia 100% open-source, processamento local e sem dependência de APIs externas, garantindo total privacidade dos dados e reprodutibilidade científica:
* **Docling:** Utilizado para a extração avançada de tabelas complexas e conversão estruturada para linguagem Markdown.
* **LangChain:** Framework de orquestração do fluxo de processamento de linguagem natural.
* **Ollama (Llama 3.2):** Motor de Inteligência Artificial Local responsável pela estruturação semântica e pareamento das variáveis financeiras em formato JSON.

## 🚀 Como Executar Localmente no Linux

1. **Instale o motor Ollama e baixe o modelo Llama 3.2:**
   ```bash
   curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
   ollama run llama3.2
