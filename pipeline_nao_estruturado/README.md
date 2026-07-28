# 🏛️ Observatório de Dados Públicos

### Pipeline Inteligente para Extração, Padronização e Reconstrução de Séries Históricas do Regime Geral de Previdência Social (RGPS)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)
![DuckDB](https://img.shields.io/badge/DuckDB-SQL%20Engine-FFF000.svg)
![Docling](https://img.shields.io/badge/Docling-PDF%20Extraction-green.svg)
![PIBIC](https://img.shields.io/badge/PIBIC-UFAPE-success.svg)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-orange.svg)
![License](https://img.shields.io/badge/License-Academic-lightgrey.svg)

---

## 📖 Sobre o Projeto

O **Observatório de Dados Públicos** é um projeto de pesquisa desenvolvido no âmbito do **Programa Institucional de Bolsas de Iniciação Científica (PIBIC)** da **Universidade Federal do Agreste de Pernambuco (UFAPE)**.

O projeto tem como objetivo automatizar a extração, padronização e consolidação de informações provenientes dos relatórios oficiais do **Regime Geral de Previdência Social (RGPS)** publicados mensalmente pelo Governo Federal.

Os dados extraídos são transformados em matrizes estruturadas e armazenados em uma arquitetura de medalhões (**Bronze → Prata → Gold**).

O pipeline foi projetado para lidar automaticamente com mudanças de layout, alterações na estrutura das tabelas (**Schema Drift**) e inconsistências provenientes da extração OCR, garantindo reprodutibilidade, rastreabilidade e qualidade dos dados produzidos.

---

# 🎯 Problema de Pesquisa

Os relatórios mensais do RGPS são disponibilizados exclusivamente em formato PDF.

Embora contenham informações essenciais para estudos econômicos e atuariais, esses documentos apresentam diversas dificuldades para extração automática, entre elas:

- mudanças frequentes no layout das tabelas;
- alterações de nomenclatura das variáveis;
- células vazias causadas por OCR;
- páginas com estruturas completamente diferentes entre meses;
- documentos contendo dezenas de tabelas irrelevantes.

Essas características tornam inviável a construção manual de séries históricas de longo prazo.

Este projeto propõe um pipeline computacional capaz de identificar automaticamente as tabelas relevantes, padronizar suas variáveis e reconstruir séries históricas contínuas de forma totalmente automática.

---

# 🎯 Objetivos

## Objetivo Geral

Desenvolver uma infraestrutura computacional capaz de extrair, padronizar, armazenar e disponibilizar dados públicos do RGPS para aplicações em Ciência de Dados e Inteligência Artificial.

---

## Objetivos Específicos

- Automatizar o download dos relatórios oficiais.
- Extrair tabelas utilizando Docling.
- Corrigir inconsistências geradas pelo OCR.
- Tratar Schema Drift automaticamente.
- Classificar as tabelas utilizando regras de negócio.
- Armazenar os dados em PostgreSQL.
- Construir uma arquitetura Bronze → Prata → Gold.
- Disponibilizar consultas SQL através do DuckDB.
- Reconstruir séries históricas automaticamente.
- Gerar bases estruturadas para modelos preditivos.

---

# ✨ Principais Funcionalidades

- Download automático dos relatórios oficiais
- Extração automática utilizando Docling
- Processamento OCR em dupla passagem
- Correção automática de Schema Drift
- Classificação determinística por regras de negócio
- Identificação automática das tabelas relevantes
- Padronização matemática das variáveis fiscais
- Persistência em PostgreSQL
- Arquitetura Bronze → Prata → Gold
- Consultas SQL em memória utilizando DuckDB
- Dashboard interativo em Streamlit
- Exportação para CSV
- Reconstrução automática de séries temporais
- Governança completa dos documentos processados
- Deduplicação utilizando Hash SHA-256

---

# 🛠️ Tecnologias Utilizadas

| Tecnologia | Finalidade |
|------------|------------|
| Python | Linguagem principal |
| Pandas | Manipulação de dados |
| PostgreSQL | Banco de dados |
| DuckDB | Engine SQL |
| Streamlit | Dashboard |
| Docling | Extração de PDFs |
| SQLAlchemy | ORM |
| Psycopg | Comunicação PostgreSQL |
| NumPy | Operações Numéricas |
| dotenv | Configuração do ambiente |

---

# 🏗️ Arquitetura Geral

O pipeline foi desenvolvido seguindo conceitos modernos de **Data Lakehouse**, organizando os dados em camadas independentes.

```

Bronze
↓

Prata

↓

Gold

↓

Dashboard Analítico

```

Cada camada possui responsabilidades específicas, permitindo rastreabilidade completa dos dados desde o documento original até a série histórica final.

---

# ⚙️ Arquitetura do Pipeline

O sistema utiliza uma abordagem **determinística baseada em regras de negócio**, eliminando dependências de modelos generativos para classificação das tabelas.

A identificação das tabelas ocorre através de um mecanismo de **Rule-Based Classification**, no qual os títulos das colunas e variáveis são comparados contra um dicionário de palavras-chave mutuamente exclusivas.

Essa estratégia torna o pipeline robusto mesmo quando o governo altera o layout dos relatórios.

---

## Estratégias Utilizadas

### 📄 Passagem Dupla de OCR

Cada documento é processado duas vezes pelo Docling.

**Primeira passagem**

- Texto real presente no PDF.

**Segunda passagem**

- Estrutura prevista pelo modelo visual.

Posteriormente, ambas as estruturas são fundidas, preservando o texto original sempre que disponível e utilizando o modelo apenas como mecanismo de preenchimento de lacunas.

---

### 🔄 Tratamento de Schema Drift

Mudanças estruturais nas tabelas são detectadas automaticamente.

O pipeline consegue identificar alterações como:

- troca de posição das colunas;
- mudança de nomes;
- colunas adicionais;
- colunas removidas;
- reorganização das tabelas.

Essas diferenças são padronizadas antes da persistência.

---

### 🧩 Classificação por Regras de Negócio

Após a limpeza das tabelas, o algoritmo compara cada estrutura contra um conjunto de gabaritos.

Cada gabarito representa uma categoria específica dos relatórios do RGPS.

Caso nenhuma correspondência seja encontrada, a tabela é descartada automaticamente.

---

### 🔒 Deduplicação

Todos os documentos recebem um hash SHA-256.

Caso um documento já tenha sido processado anteriormente, sua ingestão é ignorada automaticamente.

---

# 📊 Fluxo Geral do Pipeline

```mermaid
flowchart TD

A[urls_alvo.txt]

A --> B[Download do PDF]

B --> C[Hash SHA-256]

C --> D[Docling]

D --> E[Texto Original]

D --> F[Modelo Visual OCR]

E --> G[Fusão Inteligente]

F --> G

G --> H[Tratamento Pandas]

H --> I[Schema Drift]

I --> J[Classificação por Regras]

J --> K[(Bronze)]

J --> L[(Prata)]

L --> M[(Gold)]

M --> N[Dashboard Streamlit]

```

---

# 🏛️ Arquitetura Medalhão

```text
                 PDFs Oficiais

                       │

                       ▼

               Camada Bronze
       (Catálogo e Auditoria)

                       │

                       ▼

               Camada Prata
      (Dados Padronizados JSONB)

                       │

                       ▼

                Camada Gold
      (Séries Históricas Consolidadas)

                       │

                       ▼

          Dashboard Streamlit
```

---

Na próxima parte construiremos:

- 📊 As 10 categorias mapeadas (tabela profissional)
- 📂 Estrutura completa do projeto
- 🚀 Instalação
- ⚙️ Configuração
- ▶️ Execução
- 💾 Banco de dados
- 📁 Estrutura dos diretórios

---

# 📊 Categorias Mapeadas

O pipeline foi desenvolvido para identificar e classificar automaticamente as principais tabelas presentes nos relatórios mensais do RGPS.

Durante o processamento, cada tabela extraída é comparada contra um conjunto de **gabaritos (templates)** baseados em regras de negócio. Apenas as categorias conhecidas são persistidas no banco de dados; tabelas irrelevantes, como capas, índices, notas metodológicas e anexos, são descartadas.

| ID | Categoria | Descrição |
|----|-----------|-----------|
| 1 | **Resultado_Total** | Resultado consolidado do RGPS (Arrecadação Líquida × Despesas com Benefícios). |
| 2 | **Resultado_Urbano** | Resultado específico da Previdência Urbana. |
| 3 | **Resultado_Rural** | Resultado específico da Previdência Rural. |
| 4 | **Acumulado_12_Meses** | Indicadores acumulados dos últimos 12 meses. |
| 5 | **Renuncias_Total** | Renúncias previdenciárias totais (MEI, Simples Nacional, Filantrópicas etc.). |
| 6 | **Renuncias_Urbano** | Renúncias relacionadas ao regime urbano. |
| 7 | **Renuncias_Rural** | Renúncias relacionadas ao regime rural. |
| 8 | **Beneficios_Quantidade_Resumo** | Quantidade total de benefícios emitidos. |
| 9 | **Beneficios_Quantidade_Detalhado** | Quantidade detalhada por tipo de benefício. |
| 10 | **Beneficios_Faixa_Valor** | Distribuição dos benefícios por faixa salarial. |

---

# 🗂️ Estrutura do Projeto

```text
observatorio-de-dados-publicos/
│
├── docs/                        # Documentação do projeto
│
├── src/
│   ├── app.py                   # Dashboard Streamlit
│   ├── database.py              # Inicialização do banco
│   ├── ingestao_automatica.py   # Pipeline principal
│   │
│   ├── classificacao/
│   ├── extracao/
│   ├── processamento/
│   ├── database/
│   ├── utils/
│   └── config/
│
├── urls_alvo.txt
├── requirements.txt
├── .env
├── README.md
└── LICENSE
```

---

# 💾 Arquitetura do Banco de Dados

O PostgreSQL funciona como o repositório central do pipeline.

A arquitetura foi organizada em três camadas.

## 🥉 Bronze

Responsável pela governança dos documentos.

Cada PDF processado possui um registro contendo:

- Nome do arquivo
- URL de origem
- Hash SHA-256
- Data de processamento
- Status da ingestão
- Mensagem de erro (quando existir)

Essa camada permite auditoria completa do pipeline.

---

## 🥈 Prata

Armazena os dados estruturados extraídos dos PDFs.

Cada registro contém:

- categoria da tabela;
- competência (mês/ano);
- documento de origem;
- dados estruturados em JSONB;
- metadados de processamento.

Essa camada representa os dados já tratados e prontos para análises.

---

## 🥇 Gold

A camada Gold é construída dinamicamente pelo painel Streamlit.

Ela realiza automaticamente:

- união cronológica dos meses;
- alinhamento das variáveis;
- reconstrução das séries históricas;
- exportação em formato tabular.

Nenhum dado é duplicado fisicamente nessa camada.

---

# 🚀 Como Executar Localmente

## Pré-requisitos

Antes de iniciar, certifique-se de possuir:

- Python 3.10 ou superior
- Git
- PostgreSQL
- Ambiente virtual (venv recomendado)

---

## 1️⃣ Clonar o repositório

```bash
git clone -b desenvolvimento https://github.com/maracatu-machine-lab/observatorio-de-dados-publicos.git

cd observatorio-de-dados-publicos
```

---

## 2️⃣ Criar ambiente virtual

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

---

## 3️⃣ Instalar dependências

```bash
pip install -r requirements.txt
```

---

# ⚙️ Configuração

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto.

```env
DATABASE_URL=postgresql://usuario:senha@host:porta/banco
```

Exemplo:

```env
DATABASE_URL=postgresql://postgres:123456@localhost:5432/rgps
```

---

## Inicializar o banco

Após configurar o `.env`, execute:

```bash
python src/database.py
```

O script criará automaticamente todas as tabelas necessárias.

---

# 📥 Configuração das URLs

Na raiz do projeto, crie o arquivo

```text
urls_alvo.txt
```

Cada linha deve conter um PDF oficial.

Exemplo:

```text
# Relatórios RGPS

https://www.gov.br/arquivo1.pdf

https://www.gov.br/arquivo2.pdf

https://www.gov.br/arquivo3.pdf
```

Linhas iniciadas por `#` são ignoradas.

---

# ▶️ Executando a Ingestão

Basta executar:

```bash
python src/ingestao_automatica.py
```

Durante a execução o pipeline realiza automaticamente:

1. Download do PDF;
2. Verificação do hash SHA-256;
3. Extração via Docling;
4. OCR em dupla passagem;
5. Correção de Schema Drift;
6. Classificação das tabelas;
7. Persistência na camada Bronze;
8. Persistência na camada Prata.

Ao término da execução, todos os dados estarão disponíveis para consulta.

---

# 🌐 Executando o Dashboard

```bash
streamlit run src/app.py
```

Após iniciar, abra:

```
http://localhost:8501
```

---

# 📈 Interface Analítica

O painel foi dividido em três módulos.

## 🥇 Camada Gold

Nesta aba o usuário pode:

- selecionar uma categoria;
- reconstruir automaticamente séries históricas;
- visualizar tabelas consolidadas;
- exportar resultados em CSV.

---

## 🥈 Camada Prata

Permite explorar os dados estruturados.

Recursos disponíveis:

- KPIs de ingestão;
- filtros dinâmicos;
- consultas SQL utilizando DuckDB;
- download dos resultados.

---

## 🥉 Camada Bronze

Responsável pela auditoria.

Exibe:

- documentos processados;
- URLs;
- hashes;
- data da ingestão;
- status;
- erros encontrados.

Essa camada permite rastrear toda a execução do pipeline.

---

# 🔬 Metodologia Computacional

O pipeline foi desenvolvido seguindo princípios de **Engenharia de Dados**, **reprodutibilidade científica** e **governança de dados**, permitindo que cada etapa do processamento seja auditável e reproduzível.

O fluxo computacional pode ser resumido nas seguintes etapas:

1. Leitura automática da lista de URLs (`urls_alvo.txt`);
2. Download dos relatórios oficiais em PDF;
3. Geração do hash SHA-256 para identificação única do documento;
4. Verificação de duplicidade na Camada Bronze;
5. Extração da estrutura tabular utilizando Docling;
6. Processamento em dupla passagem (texto nativo + modelo visual);
7. Fusão inteligente dos resultados extraídos;
8. Tratamento de inconsistências estruturais (Schema Drift);
9. Classificação das tabelas por regras de negócio;
10. Persistência dos metadados na Camada Bronze;
11. Persistência dos dados estruturados na Camada Prata;
12. Reconstrução automática das séries históricas na Camada Gold;
13. Disponibilização dos dados através do dashboard Streamlit.

Essa abordagem garante rastreabilidade completa desde o documento original até a série histórica consolidada.

---

# 🧠 Tratamento de Schema Drift

Uma das principais contribuições deste projeto é o tratamento automático do **Schema Drift**, fenômeno comum em bases governamentais onde a estrutura das tabelas sofre alterações ao longo do tempo.

O pipeline é capaz de lidar automaticamente com situações como:

- alteração na ordem das colunas;
- renomeação de variáveis;
- inclusão de novas colunas;
- remoção de colunas;
- mudanças de layout entre diferentes competências;
- duplicação de nomes causada pelo OCR;
- células parcialmente preenchidas.

Após a extração, as tabelas passam por um processo de padronização que preserva a semântica dos indicadores fiscais, independentemente das mudanças editoriais realizadas nos documentos oficiais.

---

# 📄 Estrutura dos Dados

Após o processamento, cada tabela é armazenada na Camada Prata em formato **JSONB**, permitindo consultas flexíveis e preservando a estrutura original dos dados.

Exemplo simplificado:

```json
{
    "categoria": "Resultado_Total",
    "competencia": "2025-12",
    "variavel": "Arrecadação Líquida Total",
    "valor": 58234123456.89,
    "unidade": "R$ milhões",
    "documento": "RGPS_2025_12.pdf"
}
```

---

# 🔍 Exemplo de Consulta SQL

Como os dados são disponibilizados através do DuckDB, consultas SQL podem ser executadas diretamente pelo dashboard.

Exemplo:

```sql
SELECT
    competencia,
    categoria,
    variavel,
    valor
FROM camada_prata
WHERE categoria = 'Resultado_Total'
ORDER BY competencia;
```

---

# 📊 Casos de Uso

O pipeline foi desenvolvido para atender diferentes cenários de pesquisa e análise de dados públicos.

Entre suas aplicações destacam-se:

- construção automática de séries históricas;
- pesquisas em Previdência Social;
- estudos atuariais;
- análises econômicas;
- avaliação de políticas públicas;
- mineração de dados governamentais;
- preparação de bases para Machine Learning;
- preparação de bases para Deep Learning;
- previsão de indicadores fiscais utilizando modelos como:
  - LSTM;
  - GRU;
  - SVR;
  - Random Forest;
  - XGBoost.

---

# 📈 Resultados Esperados

A utilização do pipeline permite:

- automatizar a extração dos relatórios oficiais do RGPS;
- eliminar processamento manual de planilhas;
- reduzir erros humanos;
- padronizar variáveis entre diferentes competências;
- construir séries históricas contínuas;
- gerar bases de dados auditáveis;
- facilitar pesquisas acadêmicas;
- disponibilizar dados estruturados para modelos preditivos.

---

# 🚀 Trabalhos Futuros

O projeto continua em desenvolvimento.

Entre as funcionalidades planejadas destacam-se:

- integração com novos relatórios governamentais;
- atualização automática via agendamento;
- API REST para consulta dos dados;
- exportação em Parquet;
- integração com Apache Arrow;
- dashboards analíticos avançados;
- detecção automática de novas categorias;
- geração automática de metadados;
- versionamento das séries históricas;
- integração com modelos de Machine Learning para previsão do resultado previdenciário.

---

# 📚 Publicações

Este projeto faz parte das atividades desenvolvidas no âmbito do Programa Institucional de Bolsas de Iniciação Científica (PIBIC).

Quando houver publicações relacionadas, elas serão disponibilizadas nesta seção.

---

</div>
