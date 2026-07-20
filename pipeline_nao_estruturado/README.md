# 🏛️ Observatório de Dados Públicos: Pipeline RGPS

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458.svg)
![Docling](https://img.shields.io/badge/Docling-PDF%20Extraction-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)
![DuckDB](https://img.shields.io/badge/DuckDB-SQL%20Query-FFF000.svg)
![License](https://img.shields.io/badge/License-Academic-lightgrey.svg)

## 📖 Sobre o Projeto

O **Observatório de Dados Públicos** é um projeto de pesquisa desenvolvido no âmbito do **PIBIC**, com o objetivo de automatizar a extração, organização e consolidação de dados públicos relacionados ao **Regime Geral de Previdência Social (RGPS)**.

O sistema baixa automaticamente relatórios governamentais em PDF a partir de uma lista de URLs, extrai as tabelas de interesse com Docling, armazena os dados em um banco **PostgreSQL** organizado em camadas (Bronze/Prata) e disponibiliza tudo em um painel Streamlit com consulta SQL para exploração e download.

---

# 🏗 Arquitetura do Projeto

O pipeline utiliza uma abordagem **determinística baseada em regras (Table Anchoring)**: em vez de IA generativa, a tabela correta é localizada por meio da presença de termos-âncora específicos (ex: "Arrecadação Líquida Total", "Renúncias Previdenciárias"), garantindo maior confiabilidade para dados fiscais.

Para lidar com limitações conhecidas do modelo de estrutura de tabelas do Docling (células que saem vazias mesmo quando o texto existe no PDF), cada PDF é processado em **duas passadas** — uma priorizando o texto real do PDF e outra usando o texto reconhecido visualmente pelo modelo — e os resultados são mesclados, sempre priorizando o dado real.

Fluxo geral do processamento:

```text
urls_alvo.txt
    │
    ▼
Download do PDF + Hash SHA-256
(deduplicação: PDF já processado é ignorado)
    │
    ▼
Docling
(2 passadas: texto real + texto previsto pelo modelo)
    │
    ▼
Pandas
(mesclagem das passadas + identificação da tabela âncora)
    │
    ▼
PostgreSQL
├── Camada Bronze  (catálogo/auditoria: hash, URL, status, data)
└── Camada Prata   (dados extraídos, em JSONB, vinculados ao documento)
    │
    ▼
Streamlit
(dashboard + consulta SQL via DuckDB + download em CSV)
```

---

# 🚀 Como Executar Localmente

## Pré-requisitos

- Python 3.10 ou superior
- Git
- Um banco de dados PostgreSQL acessível (local ou em nuvem)

---

## 1️⃣ Clonar o repositório

```bash
git clone -b desenvolvimento https://github.com/maracatu-machine-lab/observatorio-de-dados-publicos.git

cd observatorio-de-dados-publicos
```

---

## 2️⃣ Criar um ambiente virtual

Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows

```bash
python -m venv venv

venv\Scripts\activate
```

---

## 3️⃣ Instalar as dependências

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configurar o banco de dados

Crie um arquivo `.env` na **raiz do projeto** (fora da pasta `src`) com a URL de conexão do PostgreSQL:

```env
DATABASE_URL=postgresql://usuario:senha@host:porta/nome_do_banco
```

Em seguida, crie as tabelas (camadas Bronze e Prata):

```bash
python src/database.py
```

---

## 5️⃣ Configurar as URLs de ingestão

Crie o arquivo `urls_alvo.txt` na **raiz do projeto**, com uma URL de PDF por linha (linhas iniciadas com `#` são ignoradas):

```text
# Relatórios RGPS
https://exemplo.gov.br/relatorio_rgps_2024_01.pdf
https://exemplo.gov.br/relatorio_rgps_2024_02.pdf
```

---

## 6️⃣ Executar a ingestão automática

```bash
python src/ingestao_automatica.py
```

O script baixa cada PDF, verifica se já foi processado (via hash SHA-256), extrai a tabela-alvo e grava o resultado no PostgreSQL. Documentos já processados ou sem a tabela-alvo são registrados na Camada Bronze com o status correspondente.

---

## 7️⃣ Executar o painel de visualização

```bash
streamlit run src/app.py
```

Após iniciar, o aplicativo estará disponível em:

```
http://localhost:8501
```

---

# 💻 Como utilizar

1. Rode a ingestão (`src/ingestao_automatica.py`) sempre que quiser processar novos PDFs listados em `urls_alvo.txt`.
2. Abra o painel Streamlit (`src/app.py`) no navegador.
3. Na aba **Camada Prata**, acompanhe os KPIs, escreva uma consulta SQL (via DuckDB) para filtrar os dados extraídos e baixe o resultado em CSV.
4. Na aba **Camada Bronze**, consulte o catálogo de auditoria — todos os documentos processados, com hash, URL de origem, status e data.

---

# 🔍 Metodologia Computacional

O pipeline foi desenvolvido seguindo princípios de processamento determinístico e auditável. As principais etapas são:

1. Leitura da lista de URLs em `urls_alvo.txt`;
2. Download do PDF e cálculo do hash SHA-256, usado para evitar reprocessamento;
3. Extração da estrutura tabular via Docling, em duas passadas (texto real do PDF e texto previsto pelo modelo);
4. Mesclagem das duas passadas, priorizando sempre o texto real;
5. Localização da tabela-alvo por palavras-chave (Table Anchoring);
6. Persistência em PostgreSQL: metadados/auditoria na Camada Bronze, dados extraídos (JSONB) na Camada Prata;
7. Consulta, filtragem via SQL (DuckDB) e exportação (CSV) através do painel Streamlit.

Essa abordagem reduz ambiguidades, aumenta a confiabilidade da extração para documentos fiscais e mantém rastreabilidade completa de cada documento processado.

---

# 📈 Resultados Esperados

- Extração automática e auditável de tabelas do RGPS a partir de uma lista de URLs;
- Deduplicação de documentos já processados via hash SHA-256;
- Armazenamento estruturado em PostgreSQL, com histórico de auditoria (Bronze) e dados prontos para análise (Prata);
- Exploração e filtragem dos dados via consulta SQL, sem necessidade de ferramentas externas;
- Construção de séries históricas para apoio a pesquisas em Previdência Social e análises estatísticas/econômicas.
