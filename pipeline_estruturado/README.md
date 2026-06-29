# Pipeline Estruturado

Esta pasta contém a primeira versão do ETL em Python para coleta e organização de dados públicos estruturados.

O projeto começou a partir de uma necessidade de trabalhar com dados ligados à Previdência e ao orçamento público, mas a estrutura não está limitada a esse tema. A ideia é permitir a inclusão de outras bases públicas, como IBGE, IPEA, PNAD, SIOP, Tesouro Nacional e outras fontes que possam ser úteis para pesquisa.

Esta versão ainda é inicial. O foco, neste momento, é deixar uma base funcional para coleta, armazenamento dos dados brutos e geração de arquivos tratados.

## Objetivo

O objetivo é construir um fluxo simples de ETL para dados públicos.

ETL significa:

- Extract: coletar os dados nas fontes públicas;
- Transform: organizar e padronizar os dados coletados;
- Load: salvar os arquivos em pastas próprias para uso posterior.

No projeto, esse fluxo foi dividido em três camadas:

```text
data/bronze
data/silver
data/gold
```

A camada `bronze` guarda os dados brutos.

A camada `silver` guarda os dados já tratados.

A camada `gold` guarda os dados consolidados para análise.

## Fontes usadas nesta primeira versão

Nesta etapa, o projeto trabalha principalmente com:

- IBGE, por meio da API do SIDRA;
- PNAD Contínua, também acessada por tabelas do SIDRA;
- IPEAData, para séries econômicas e sociais;
- SIOP, ainda mais organizado como estrutura de pastas e arquivos.

A PNAD está sendo usada, por enquanto, a partir de dados agregados do SIDRA. O uso de microdados pode ser incluído depois, mas exige outro tratamento, pois os arquivos são maiores e têm uma estrutura diferente.

## Estrutura da pasta

```text
pipeline_estruturado/
├── config/
│   └── sources.json
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── docs/
│   └── COMO_PROGRAMAR_ETL.md
├── logs/
├── notebooks/
├── outputs/
├── scripts/
│   └── run_etl.py
├── src/
│   └── observatorio_etl/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── http_client.py
│       ├── ipeadata.py
│       ├── paths.py
│       ├── runner.py
│       ├── sidra.py
│       └── storage.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## O que tem em cada pasta

### `config/`

Guarda as configurações das fontes de dados.

O arquivo principal é:

```text
config/sources.json
```

Nele ficam cadastradas as fontes que o ETL deve buscar. A ideia é que novas fontes possam ser adicionadas nesse arquivo, sem precisar alterar toda a lógica do código.

### `data/bronze/`

Guarda os dados brutos, no formato mais próximo possível do retorno das APIs.

Essa pasta é importante porque permite conferir o que veio diretamente da fonte. Se algum erro aparecer na transformação, os dados originais continuam salvos.

### `data/silver/`

Guarda os dados tratados.

Nessa camada, os dados passam a ter uma estrutura mais parecida entre as fontes. A ideia é facilitar comparações e análises depois.

### `data/gold/`

Guarda os arquivos finais consolidados.

Essa pasta deve ser usada para os dados que já estão prontos para análise, gráficos, notebooks ou dashboards.

### `docs/`

Pasta para guardar anotações, explicações e documentação do projeto.

### `logs/`

Pasta reservada para registros de execução.

### `notebooks/`

Pasta para análises exploratórias. A ideia é usar notebooks para testar, visualizar e estudar os dados, mas não colocar neles a lógica principal do ETL.

### `outputs/`

Pasta para saídas do projeto, como gráficos, tabelas exportadas, imagens e relatórios.

### `scripts/`

Guarda os scripts usados para executar o projeto.

O principal arquivo é:

```text
scripts/run_etl.py
```

### `src/`

Guarda o código-fonte do projeto.

Dentro dela existe o pacote:

```text
observatorio_etl
```

É nessa pasta que ficam os módulos responsáveis por coletar, tratar e salvar os dados.

## Principais arquivos do código

### `scripts/run_etl.py`

É o arquivo usado para executar o projeto pelo terminal.

### `src/observatorio_etl/cli.py`

Define os comandos disponíveis.

Os comandos principais são:

```bash
python scripts/run_etl.py list-sources
python scripts/run_etl.py run
```

### `src/observatorio_etl/config.py`

Lê o arquivo `config/sources.json` e transforma as informações das fontes em objetos usados pelo ETL.

### `src/observatorio_etl/http_client.py`

Centraliza as requisições HTTP. Esse módulo é usado para acessar as APIs externas e receber os dados em JSON.

### `src/observatorio_etl/sidra.py`

Contém a lógica de acesso ao SIDRA, usado para dados agregados do IBGE e da PNAD Contínua.

### `src/observatorio_etl/ipeadata.py`

Contém a lógica de acesso ao IPEAData. Esse módulo busca metadados e valores das séries, depois organiza as informações em formato tabular.

### `src/observatorio_etl/paths.py`

Organiza os caminhos principais do projeto.

### `src/observatorio_etl/storage.py`

Contém funções para salvar arquivos nas pastas `bronze`, `silver` e `gold`.

### `src/observatorio_etl/runner.py`

É o módulo que coordena a execução do ETL. Ele lê as fontes configuradas, identifica o tipo de API, chama o coletor correto, salva os dados brutos, transforma os dados e gera as saídas consolidadas.

## Como instalar

Acesse esta pasta:

```bash
cd pipeline_estruturado
```

Crie o ambiente virtual:

```bash
python3 -m venv .venv
```

Ative o ambiente virtual no Linux:

```bash
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Como executar

Para conferir as fontes cadastradas:

```bash
python scripts/run_etl.py list-sources
```

Para executar a coleta e o tratamento dos dados:

```bash
python scripts/run_etl.py run
```

## O que acontece quando o ETL roda

Quando o comando `run` é executado, o projeto faz o seguinte:

1. Lê o arquivo `config/sources.json`;
2. Verifica quais fontes estão ativadas;
3. Identifica se a fonte usa SIDRA ou IPEAData;
4. Faz a requisição para a API;
5. Salva a resposta original em `data/bronze/`;
6. Transforma os dados em uma tabela padronizada;
7. Salva os dados tratados em `data/silver/`;
8. Junta as séries coletadas;
9. Gera arquivos finais em `data/gold/`.

## Como adicionar uma nova fonte

Para adicionar uma nova fonte, edite o arquivo:

```text
config/sources.json
```

Exemplo de fonte usando SIDRA:

```json
{
  "name": "ibge_populacao_estimada_brasil",
  "type": "sidra",
  "source": "ibge",
  "theme": "populacao",
  "table": "6579",
  "variable": "9324",
  "period": "last",
  "territorial_level": "1",
  "localities": "all",
  "decimals": "0"
}
```

Exemplo de fonte usando IPEAData:

```json
{
  "name": "ipea_ipca_indice_mensal",
  "type": "ipeadata",
  "source": "ipea",
  "theme": "inflacao",
  "series_code": "PRECOS12_IPCA12"
}
```

Depois de alterar o arquivo, confira se a fonte foi lida:

```bash
python scripts/run_etl.py list-sources
```

Em seguida, execute:

```bash
python scripts/run_etl.py run
```

## Saídas esperadas

Após a execução, o projeto pode gerar arquivos como:

```text
data/bronze/ibge/*.json
data/bronze/ipea/*.json
data/bronze/pnad/*.json

data/silver/ibge/*.csv
data/silver/ipea/*.csv
data/silver/pnad/*.csv

data/gold/series_consolidadas.csv
data/gold/series_consolidadas.parquet
data/gold/catalogo_series.csv
```

## Situação atual

Nesta versão, o projeto já possui uma base funcional para:

- listar fontes configuradas;
- acessar APIs públicas;
- salvar respostas brutas;
- tratar dados em formato tabular;
- consolidar séries em arquivos finais.

Ainda existem pontos que podem ser melhorados, como:

- adicionar mais fontes;
- tratar melhor erros de conexão;
- criar logs mais detalhados;
- incluir testes automatizados;
- melhorar a documentação das variáveis;
- criar notebooks de análise;
- automatizar a coleta do SIOP;
- estudar o uso de microdados da PNAD.

## Observações

Este projeto ainda está em desenvolvimento. Por isso, algumas partes podem mudar conforme novas fontes forem incluídas e conforme os dados forem sendo testados.

A separação dos dados em `bronze`, `silver` e `gold` ajuda a manter o processo mais organizado. Também facilita refazer uma etapa sem precisar baixar tudo novamente.
