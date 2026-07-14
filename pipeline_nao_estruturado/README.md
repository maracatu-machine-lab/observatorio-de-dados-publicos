# 🏛️ Observatório de Dados Públicos: Pipeline RGPS

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458.svg)
![Docling](https://img.shields.io/badge/Docling-PDF%20Extraction-green.svg)
![License](https://img.shields.io/badge/License-Academic-lightgrey.svg)

## 📖 Sobre o Projeto

O **Observatório de Dados Públicos** é um projeto de pesquisa desenvolvido no âmbito do **PIBIC**, com o objetivo de automatizar a extração, organização e consolidação de dados públicos relacionados ao **Regime Geral de Previdência Social (RGPS)**.

O sistema transforma relatórios governamentais em PDF — muitas vezes extensos e com tabelas complexas — em bases de dados estruturadas (JSON/CSV), permitindo a construção de séries históricas para análises econômicas e fiscais.

---

# 🏗 Arquitetura do Projeto

O pipeline utiliza uma abordagem **determinística baseada em regras (Table Anchoring)**.

Ao contrário de métodos probabilísticos ou baseados em IA generativa, a extração é realizada através de regras explícitas de localização das tabelas, garantindo maior confiabilidade para dados fiscais.

Fluxo geral do processamento:

```text
PDF RGPS
    │
    ▼
Docling
(Extração Estrutural)
    │
    ▼
Pandas
(Identificação das tabelas e tratamento)
    │
    ▼
Table Anchoring
(Localização determinística)
    │
    ▼
JSON / CSV
    │
    ▼
Streamlit
(Curadoria Human-in-the-Loop)
```

---

# 🚀 Como Executar Localmente

## Pré-requisitos

- Python 3.10 ou superior
- Git

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

## 4️⃣ Executar a aplicação

```bash
streamlit run src/app.py
```

Após iniciar, o aplicativo estará disponível em:

```
http://localhost:8501
```

---

# 💻 Como utilizar

1. Abra a aplicação no navegador.
2. Faça upload do PDF do RGPS.
3. Aguarde o processamento.
4. Revise as tabelas extraídas.
5. Exporte os resultados em JSON ou CSV.

---

# 🔍 Metodologia Computacional

O pipeline foi desenvolvido seguindo princípios de processamento determinístico.

As principais etapas são:

1. Leitura do PDF;
2. Extração da estrutura utilizando Docling;
3. Conversão para DataFrames Pandas;
4. Localização das tabelas através de palavras-chave (Table Anchoring);
5. Consolidação dos dados;
6. Exportação para JSON/CSV;
7. Validação manual via interface Streamlit.

Essa abordagem reduz ambiguidades e aumenta a confiabilidade da extração para documentos fiscais.

---

# 📈 Resultados Esperados

- Extração automática de tabelas do RGPS;
- Preservação da estrutura original dos documentos;
- Construção de séries históricas;
- Apoio a pesquisas em Previdência Social;
- Base estruturada para análises estatísticas e econômicas.

---

# 🛠 Desenvolvimento

Para registrar alterações no repositório:

```bash
# Adicionar arquivos modificados
git add src/app.py requirements.txt README.md

# Criar um commit
git commit -m "Refatoração: Extração determinística com Docling e exportação para JSON"

# Enviar para o GitHub
git push origin desenvolvimento
```
