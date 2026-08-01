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

Os relatórios mensais do RGPS são disponibilizados em formatos de apresentação e texto (como PDF e PPTX).

Embora contenham informações essenciais para estudos econômicos e atuariais, esses documentos apresentam diversas dificuldades para extração automática, entre elas:

- mudanças frequentes no layout das tabelas;
- alterações de nomenclatura das variáveis;
- células vazias causadas por OCR;
- páginas com estruturas completamente diferentes entre meses;
- documentos contendo dezenas de tabelas irrelevantes.

Essas características tornam inviável a construção manual de séries históricas de longo prazo.

Este projeto propõe um pipeline computacional capaz de identificar automaticamente as tabelas relevantes, padronizar suas variáveis e reconstruir séries históricas contínuas de forma totalmente automática.

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

### 🗺️ Extração Orientada a Metadados (Metadata-Driven) e Fallback Híbrido

Para garantir 100% de precisão matemática na extração e evitar falsos positivos causados pelo ruído do OCR, o pipeline implementa uma arquitetura híbrida de busca:

1. **Mapeamento Explícito (Excel):** O sistema consome uma planilha de controle (`mapeamento.xlsx`) que indica em qual página exata cada tabela está localizada em cada mês/ano, acelerando o processamento.
2. **Prova Real:** A tabela encontrada na página mapeada é submetida ao Gabarito de Regras. Se as palavras-chave baterem, ela é aprovada.
3. **Fallback Automático (Plano B):** Se o mapeamento humano falhar (ex: erro de digitação na planilha) ou a página estiver em branco, o sistema não quebra. Ele emite um alerta e aciona automaticamente a varredura completa do documento em busca da tabela perdida.

---

### 🔒 Deduplicação

Todos os documentos recebem um hash SHA-256.

Caso um documento já tenha sido processado anteriormente, sua ingestão é ignorada automaticamente.

---

# 📊 Fluxo Geral do Pipeline

```mermaid
flowchart TD

A[urls_alvo.txt]
A2[mapeamento.xlsx]

A --> B[Download do Documento]
B --> C{É PDF ou PPTX?}
C --> D[Hash SHA-256]

A2 --> G
D --> E[Docling OCR / Parsing]

E --> F[Leitura de Páginas]
F --> G{Cruzamento com Mapeamento Excel}

G -->|Página Correta e Validada| H[Tratamento Pandas]
G -->|Página Errada / Não Mapeada| I[Varredura Completa e Gabarito]
I --> H

H --> J[Schema Drift & Filtro Temporal]
J --> K[(Camada Bronze)]
J --> L[(Camada Prata)]
L --> M[(Camada Gold)]
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

# 📊 Categorias Mapeadas (O Gabarito)

O pipeline foi desenvolvido para identificar, limpar e classificar automaticamente as **10 tabelas centrais** presentes nos relatórios mensais do RGPS. 

Durante o processamento, cada tabela extraída é comparada contra um conjunto de **gabaritos (templates)** baseados em regras de negócio. Apenas as categorias mapeadas abaixo são persistidas no banco de dados; tabelas irrelevantes, como capas, índices, notas metodológicas e anexos, são descartadas automaticamente.

| ID | Categoria no Banco | Descrição dos Indicadores Contidos |
| :--- | :--- | :--- |
| **1** | `1_Resultado_Total` | Arrecadação Líquida e Despesa com Benefícios (Visão Consolidada). |
| **2** | `2_Resultado_Urbano` | Arrecadação Líquida e Despesa com Benefícios (Visão Urbana). |
| **3** | `3_Resultado_Rural` | Arrecadação Líquida e Despesa com Benefícios (Visão Rural). |
| **4** | `4_Acumulado_12_Meses` | Visão consolidada dos resultados e despesas acumulados nos últimos 12 meses. |
| **5** | `5_Renuncias_Total` | Impacto das Renúncias Previdenciárias (Simples Nacional, MEI, Filantrópicas, etc.) no resultado total. |
| **6** | `6_Renuncias_Urbano` | Impacto das Renúncias Previdenciárias focado na arrecadação urbana. |
| **7** | `7_Renuncias_Rural` | Impacto das Renúncias Previdenciárias focado na arrecadação rural (Funrural, Exportação, etc.). |
| **8** | `8_Beneficios_Quantidade_Resumo` | Quantidade total de benefícios emitidos (Previdenciários + Acidentários vs. Assistenciais). |
| **9** | `9_Beneficios_Quantidade_Detalhado` | Abertura detalhada da quantidade de benefícios (Aposentadorias, Auxílio-Doença, BPC, etc.). |
| **10** | `10_Beneficios_Faixa_Valor` | Distribuição dos benefícios emitidos divididos por faixas de Salário Mínimo (<1 SM, 1 SM, etc.). *Possui tratamento especial de transposição e formatação na Camada Gold para reestruturação das linhas.* |
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
│   ├── limpar_banco.py          # Script de reset (Drop Tables)
...
│
├── urls_alvo.txt                # Lista de PDFs e PPTXs
├── mapeamento.xlsx              # Matriz de controle de páginas (Metadata-Driven)
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

# 📥 Configuração de Ingestão e Metadados

Na raiz do projeto, você deve gerenciar dois arquivos de entrada:

**1. `urls_alvo.txt`**
Cada linha deve conter um link direto para o documento oficial (suporta `.pdf` e `.pptx`). Linhas iniciadas por `#` são ignoradas.

**2. `mapeamento.xlsx`**
Planilha de controle contendo os meses nas colunas (ex: `2026-03`) e as categorias nas linhas (ex: `1_Resultado_Total`). O cruzamento deve conter o número da página onde a tabela se encontra para otimizar o processamento.
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

1. Leitura automática da lista de documentos (`urls_alvo.txt`) e da planilha de controle (`mapeamento.xlsx`);
2. Download dos relatórios (PDF ou PowerPoint) e identificação nativa da extensão;
3. Geração do hash SHA-256 para evitar duplicidade na Camada Bronze;
4. Extração da estrutura tabular utilizando Docling (dupla passagem para PDFs);
5. **Cruzamento Híbrido:** Verificação da página mapeada no Excel contra a regra do Gabarito;
6. Execução do Fallback automático de busca em caso de divergência humana;
7. Tratamento de inconsistências estruturais (Schema Drift) e isolamento da variável mensal;
8. Persistência dos metadados na Camada Bronze e JSONB na Camada Prata;
9. Reconstrução cronológica automatizada das séries históricas na Camada Gold, com tratamento de transposição para categorias excepcionais (Tabela 10);
10. Disponibilização dos dados através do dashboard interativo Streamlit.
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
