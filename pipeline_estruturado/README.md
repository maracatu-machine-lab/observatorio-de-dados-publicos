# Pipeline Estruturado

Esta pasta contém o ETL em Python usado para coletar, organizar, tratar e consolidar dados públicos estruturados.

O projeto começou a partir da necessidade de trabalhar com dados ligados à Previdência e ao orçamento público, mas a estrutura não está limitada a esses temas. A proposta é permitir a inclusão gradual de outras bases públicas, como IBGE, IPEA, PNAD Contínua, SIOP, Tesouro Nacional e outras fontes que possam ser utilizadas nas pesquisas do observatório.

Nesta etapa, o pipeline já consegue consultar fontes públicas, armazenar os retornos originais, transformar os dados e gerar arquivos consolidados. O projeto continua em desenvolvimento e deve receber novas fontes, testes e ajustes conforme as bases forem sendo estudadas.

## Objetivo

O objetivo desta parte do projeto é construir um fluxo de ETL para dados públicos estruturados.

ETL significa:

- Extract: coletar os dados nas fontes públicas;
- Transform: organizar, converter e padronizar os dados coletados;
- Load: salvar os resultados em pastas próprias para uso posterior.

O fluxo foi dividido em três camadas:

```text
data/bronze
data/silver
data/gold
```

A camada `bronze` guarda os dados próximos ao formato original recebido da fonte.

A camada `silver` guarda os dados tratados e com nomes de colunas mais padronizados.

A camada `gold` guarda arquivos consolidados para análises, gráficos, notebooks e outras etapas do projeto.

## Fontes usadas nesta versão

Nesta etapa, o projeto trabalha com:

- IBGE, por meio da API do SIDRA;
- PNAD Contínua, também acessada por tabelas do SIDRA;
- IPEAData, para séries econômicas e sociais;
- SIOP, para dados da Lei Orçamentária Anual e da execução orçamentária.

A PNAD Contínua está sendo usada, por enquanto, a partir de dados agregados disponíveis no SIDRA. O uso de microdados pode ser incluído depois, mas exige outro processo de download, leitura e transformação.

Os dados do SIOP são consultados com a biblioteca `orcamentobr`. Nesta versão, o pipeline consulta os exercícios de 2015 a 2026.

A consulta do SIOP é feita separadamente para cada exercício. Cada ano é coletado com todas as categorias e dimensões disponíveis na LOA, permitindo preservar os dados completos na camada `bronze` e produzir recortes consolidados na camada `gold`.

## Estrutura da pasta

```text
pipeline_estruturado/
├── config/
│   └── sources.json
├── data/
│   ├── bronze/
│   │   ├── ibge/
│   │   ├── ipea/
│   │   ├── pnad/
│   │   └── siop/
│   │       └── execucao_orcamentaria/
│   ├── silver/
│   │   ├── ibge/
│   │   ├── ipea/
│   │   ├── pnad/
│   │   └── siop/
│   │       └── execucao_orcamentaria/
│   └── gold/
│       └── siop/
├── docs/
│   ├── COMO_PROGRAMAR_ETL.md
│   └── LEGENDA_PREVIDENCIA_PUBLICA.md
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
│       ├── siop.py
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

Nele ficam cadastradas as fontes que o ETL deve consultar. Cada entrada informa o nome do conjunto de dados, o tipo da fonte, o tema e os parâmetros necessários para a consulta.

Atualmente, o pipeline reconhece três tipos:

```text
sidra
ipeadata
siop
```

A configuração do SIOP contém uma lista de exercícios:

```json
"exercicios": [
  2015,
  2016,
  2017,
  2018,
  2019,
  2020,
  2021,
  2022,
  2023,
  2024,
  2025,
  2026
]
```

A ideia é que novas consultas possam ser adicionadas nesse arquivo sem alterar toda a estrutura do projeto.

### `data/bronze/`

Guarda os dados brutos ou próximos ao formato original recebido das fontes.

Essa camada permite conferir o conteúdo devolvido pela API ou biblioteca antes da transformação. Se algum problema aparecer na camada seguinte, os dados originais continuam disponíveis para análise.

Para o SIDRA e o IPEAData, podem ser salvos arquivos JSON e CSV.

Para o SIOP, a camada `bronze` preserva a LOA completa de cada exercício, incluindo todas as categorias e dimensões configuradas.

As dimensões coletadas são:

```text
esfera
orgao
unidade orcamentaria
funcao
subfuncao
programa
acao
plano orcamentario
subtitulo
categoria economica
grupo de natureza da despesa
modalidade de aplicacao
elemento de despesa
fonte de recursos
identificador de uso
resultado primario
```

Também são coletados os seguintes valores:

```text
PLOA
dotacao inicial
dotacao atualizada
valor empenhado
valor liquidado
valor pago
```

Para cada exercício do SIOP, são salvos:

- um arquivo JSON com os parâmetros usados na consulta;
- um arquivo CSV com o retorno bruto completo.

Exemplo:

```text
data/bronze/siop/execucao_orcamentaria/
├── siop_loa_completa_2015_consulta.json
├── siop_loa_completa_2015_bruto.csv
├── siop_loa_completa_2016_consulta.json
├── siop_loa_completa_2016_bruto.csv
├── ...
├── siop_loa_completa_2026_consulta.json
└── siop_loa_completa_2026_bruto.csv
```

### `data/silver/`

Guarda os dados tratados.

Nessa camada, os nomes das colunas são padronizados, os valores monetários são convertidos para formato numérico e as informações de origem da coleta são acrescentadas.

Os dados do IBGE, PNAD e IPEAData são organizados em formato de séries.

Os dados do SIOP são tratados separadamente para cada exercício. As dimensões da LOA são preservadas para permitir filtros e análises posteriores.

Entre os campos principais estão:

```text
fonte
tema
dataset
exercicio
valor_ploa
dotacao_inicial
dotacao_atualizada
valor_empenhado
valor_liquidado
valor_pago
coletado_em
```

Os arquivos anuais são salvos em CSV e Parquet:

```text
data/silver/siop/execucao_orcamentaria/
├── siop_loa_completa_2015.csv
├── siop_loa_completa_2015.parquet
├── ...
├── siop_loa_completa_2026.csv
└── siop_loa_completa_2026.parquet
```

### `data/gold/`

Guarda os arquivos consolidados.

As séries do IBGE, PNAD e IPEAData são reunidas nos arquivos:

```text
data/gold/series_consolidadas.csv
data/gold/series_consolidadas.parquet
```

O catálogo das fontes executadas é salvo em:

```text
data/gold/catalogo_series.csv
```

Para o SIOP, são produzidos dois arquivos consolidados distintos:

```text
data/gold/siop/loa_total_por_ano.csv
data/gold/siop/loa_previdencia_publica_por_ano.csv
```

Os dois arquivos possuem a mesma estrutura:

```text
fonte | tema | dataset | exercicio | valor_empenhado | valor_liquidado | valor_pago | coletado_em
```

#### `loa_total_por_ano.csv`

Contém uma linha para cada exercício entre 2015 e 2026.

Cada linha representa a soma de todos os registros da LOA do respectivo exercício, sem aplicar recorte por função, órgão, programa ou outra dimensão.

#### `loa_previdencia_publica_por_ano.csv`

Contém uma linha para cada exercício entre 2015 e 2026.

Cada linha representa a soma dos registros relacionados à Previdência Pública segundo a classificação funcional da despesa.

O critério utilizado é:

```text
funcao = 09 - Previdencia Social
```

O filtro é aplicado pelo código da função, e não por palavras presentes nos nomes de órgãos, programas, ações ou planos orçamentários.

## Critério do recorte de Previdência Pública

O recorte de Previdência Pública considera todas as linhas da LOA classificadas na função:

```text
09 - Previdencia Social
```

As subfunções associadas são:

| Código | Descrição |
|---|---|
| 271 | Previdência Básica |
| 272 | Previdência do Regime Estatutário |
| 273 | Previdência Complementar |
| 274 | Previdência Especial |

Todas as linhas classificadas na função 09 são incluídas, independentemente do órgão, unidade orçamentária, programa, ação, plano orçamentário, natureza da despesa, fonte de recursos ou outra categoria.

Não são incluídas linhas classificadas em outras funções, mesmo quando o nome do órgão, programa ou ação contenha expressões como `INSS`, `previdência`, `aposentadoria` ou `pensão`.

Esse critério evita decisões baseadas apenas em palavras e torna o recorte reproduzível entre os exercícios.

A explicação metodológica completa fica registrada em:

```text
docs/LEGENDA_PREVIDENCIA_PUBLICA.md
```

## Principais arquivos do código

### `scripts/run_etl.py`

É o arquivo usado para executar o projeto pelo terminal.

Ele chama a interface de linha de comando definida em `cli.py`.

### `src/observatorio_etl/cli.py`

Define os comandos disponíveis.

Os principais comandos são:

```bash
python scripts/run_etl.py list-sources
python scripts/run_etl.py run
```

### `src/observatorio_etl/config.py`

Lê o arquivo `config/sources.json` e transforma as configurações em objetos usados pelo restante do pipeline.

### `src/observatorio_etl/http_client.py`

Centraliza as requisições HTTP feitas para as APIs.

Esse módulo é usado principalmente nas consultas ao SIDRA e ao IPEAData.

### `src/observatorio_etl/sidra.py`

Contém a lógica de acesso à API do SIDRA.

Esse módulo é usado para dados agregados do IBGE e da PNAD Contínua.

### `src/observatorio_etl/ipeadata.py`

Contém a lógica de acesso ao IPEAData.

O módulo busca os metadados e os valores das séries, depois organiza as informações em formato tabular.

### `src/observatorio_etl/siop.py`

Contém a lógica de consulta, validação e tratamento dos dados do SIOP.

A coleta é feita por meio da biblioteca `orcamentobr`.

O módulo:

1. recebe os parâmetros da consulta;
2. valida se todas as dimensões e valores necessários estão ativados;
3. consulta um exercício por vez;
4. repete a tentativa em caso de falha temporária;
5. padroniza os nomes das colunas;
6. converte os valores monetários para formato numérico;
7. preserva as dimensões da LOA;
8. soma o total da LOA de cada exercício;
9. filtra a função 09;
10. soma os valores relacionados à Previdência Pública.

As funções principais são:

```text
SiopClient.fetch_expenses()
validate_complete_loa_params()
prepare_siop_dataframe()
build_total_loa_row()
build_previdencia_publica_row()
filter_previdencia_publica()
```

### `src/observatorio_etl/paths.py`

Organiza os caminhos principais do projeto.

Isso evita repetir os mesmos caminhos em vários módulos.

### `src/observatorio_etl/storage.py`

Contém funções para salvar dados nos formatos JSON, CSV e Parquet.

### `src/observatorio_etl/runner.py`

Coordena a execução do ETL.

Esse módulo:

1. lê as fontes cadastradas;
2. identifica o tipo de cada fonte;
3. chama o coletor correspondente;
4. salva os dados na camada `bronze`;
5. transforma e salva os dados na camada `silver`;
6. consolida os resultados na camada `gold`;
7. percorre os exercícios de 2015 a 2026 para a fonte SIOP;
8. gera o arquivo com o total da LOA por exercício;
9. gera o arquivo com o total relacionado à Previdência Pública por exercício.

O `runner.py` reconhece atualmente fontes dos tipos:

```text
sidra
ipeadata
siop
```

## Como instalar

Acesse a pasta do pipeline:

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
python -m pip install -r requirements.txt
```

As principais dependências são:

```text
requests
pandas
pyarrow
orcamentobr
```

## Como executar

Para conferir as fontes cadastradas:

```bash
python scripts/run_etl.py list-sources
```

Entre as fontes listadas, deve aparecer:

```text
siop_loa_completa_2015_2026 | siop | siop/execucao_orcamentaria
```

Para executar a coleta e o tratamento de todas as fontes:

```bash
python scripts/run_etl.py run
```

A coleta do SIOP realiza uma consulta para cada exercício e solicita todas as dimensões da LOA. Por isso, essa etapa pode levar mais tempo e produzir arquivos maiores do que as consultas das outras fontes.

## O que acontece quando o ETL roda

Quando o comando `run` é executado, o pipeline realiza as seguintes etapas:

1. lê o arquivo `config/sources.json`;
2. percorre as fontes cadastradas;
3. identifica se cada fonte usa SIDRA, IPEAData ou SIOP;
4. faz a consulta correspondente;
5. salva o retorno original na camada `bronze`;
6. transforma os dados;
7. salva os dados tratados na camada `silver`;
8. reúne as séries do IBGE, PNAD e IPEAData;
9. consulta a LOA completa para cada exercício entre 2015 e 2026;
10. soma os valores totais de cada exercício;
11. filtra os registros da função 09;
12. soma os valores de Previdência Pública;
13. gera os dois arquivos consolidados na camada `gold`;
14. gera o catálogo das fontes executadas.

## Como adicionar uma nova fonte

Para adicionar uma nova fonte, edite:

```text
config/sources.json
```

### Exemplo usando SIDRA

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

### Exemplo usando IPEAData

```json
{
  "name": "ipea_ipca_indice_mensal",
  "type": "ipeadata",
  "source": "ipea",
  "theme": "inflacao",
  "series_code": "PRECOS12_IPCA12"
}
```

### Exemplo usando SIOP

```json
{
  "name": "siop_loa_completa_2015_2026",
  "type": "siop",
  "source": "siop",
  "theme": "execucao_orcamentaria",
  "exercicios": [
    2015,
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026
  ],
  "esfera": true,
  "orgao": true,
  "uo": true,
  "funcao": true,
  "sub_funcao": true,
  "programa": true,
  "acao": true,
  "plano_orcamentario": true,
  "subtitulo": true,
  "categoria_economica": true,
  "gnd": true,
  "modalidade_aplicacao": true,
  "elemento_despesa": true,
  "fonte": true,
  "id_uso": true,
  "resultado_primario": true,
  "valor_ploa": true,
  "valor_loa": true,
  "valor_loa_mais_credito": true,
  "valor_empenhado": true,
  "valor_liquidado": true,
  "valor_pago": true,
  "inclui_descricoes": true,
  "detalhe_maximo": true,
  "ignore_secure_certificate": true,
  "timeout": 600000,
  "print_url": false
}
```

Depois de editar o arquivo, confira as fontes:

```bash
python scripts/run_etl.py list-sources
```

Em seguida, execute:

```bash
python scripts/run_etl.py run
```

## Saídas esperadas

### IBGE, PNAD e IPEAData

```text
data/bronze/ibge/
data/bronze/ipea/
data/bronze/pnad/

data/silver/ibge/
data/silver/ipea/
data/silver/pnad/

data/gold/series_consolidadas.csv
data/gold/series_consolidadas.parquet
data/gold/catalogo_series.csv
```

### SIOP

Na camada `bronze`, são criados arquivos completos para cada exercício:

```text
data/bronze/siop/execucao_orcamentaria/
├── siop_loa_completa_2015_consulta.json
├── siop_loa_completa_2015_bruto.csv
├── ...
├── siop_loa_completa_2026_consulta.json
└── siop_loa_completa_2026_bruto.csv
```

Na camada `silver`, são criados arquivos tratados para cada exercício:

```text
data/silver/siop/execucao_orcamentaria/
├── siop_loa_completa_2015.csv
├── siop_loa_completa_2015.parquet
├── ...
├── siop_loa_completa_2026.csv
└── siop_loa_completa_2026.parquet
```

Na camada `gold`, são criados:

```text
data/gold/siop/
├── loa_total_por_ano.csv
└── loa_previdencia_publica_por_ano.csv
```

Os dois arquivos possuem esta estrutura:

```text
fonte | tema | dataset | exercicio | valor_empenhado | valor_liquidado | valor_pago | coletado_em
```

Exemplo do arquivo total:

```csv
fonte,tema,dataset,exercicio,valor_empenhado,valor_liquidado,valor_pago,coletado_em
siop,execucao_orcamentaria,siop_loa_total_por_ano,2015,valor,valor,valor,data_hora
```

Exemplo do arquivo de Previdência Pública:

```csv
fonte,tema,dataset,exercicio,valor_empenhado,valor_liquidado,valor_pago,coletado_em
siop,previdencia_publica,siop_loa_previdencia_publica_por_ano,2015,valor,valor,valor,data_hora
```

## Situação atual

Nesta versão, o pipeline já possui funções para:

- listar as fontes cadastradas;
- consultar dados do IBGE pelo SIDRA;
- consultar dados agregados da PNAD Contínua pelo SIDRA;
- consultar séries do IPEAData;
- consultar a LOA completa do SIOP entre 2015 e 2026;
- preservar todas as categorias e dimensões na camada `bronze`;
- repetir consultas do SIOP em caso de falha temporária;
- gerar arquivos tratados em CSV e Parquet;
- consolidar séries temporais;
- gerar o total da LOA por exercício;
- gerar o total relacionado à Previdência Pública por exercício;
- registrar a metodologia do recorte previdenciário.

Ainda existem pontos que podem ser desenvolvidos:

- adicionar novas tabelas e séries;
- incluir dados do Tesouro Nacional;
- criar logs mais detalhados;
- incluir testes automatizados;
- melhorar a documentação das variáveis;
- criar notebooks de análise;
- permitir a execução de apenas uma fonte;
- permitir a escolha dos exercícios pelo terminal;
- estudar o uso de microdados da PNAD;
- incluir validações para valores ausentes e resultados inesperados;
- comparar os dados do SIOP com outras fontes orçamentárias;
- avaliar formas de reduzir o tempo de consulta da LOA completa.

## Observações sobre os dados do SIOP

O exercício de 2026 ainda está em andamento. Por isso, os valores de empenhado, liquidado e pago representam o acumulado disponível no momento da coleta e não um exercício encerrado.

Os valores dos demais anos também dependem da atualização e da disponibilidade das informações no endpoint consultado.

A opção:

```json
"ignore_secure_certificate": true
```

foi usada porque o endpoint do SIOP apresentou falha na validação do certificado SSL durante os testes. Essa configuração deve permanecer restrita à consulta do SIOP.

A consulta completa da LOA pode produzir arquivos grandes e levar vários minutos por exercício.

## Observações sobre o projeto

O projeto ainda está em desenvolvimento. Algumas partes podem mudar conforme novas fontes forem incluídas e os resultados das consultas forem avaliados.

A separação entre `bronze`, `silver` e `gold` ajuda a acompanhar as etapas do ETL e facilita o reprocessamento dos dados.

Os dados da camada `bronze` devem ser preservados sempre que possível, pois representam o retorno mais próximo da fonte original. As alterações, padronizações, filtros e consolidações devem acontecer nas camadas seguintes.